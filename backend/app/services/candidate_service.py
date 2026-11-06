from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from app.schemas.candidate import CandidateProfileCreate, CandidateProfileUpdate, CandidateMemoryCreate
from app.models.candidate import CandidateProfile, CandidateMemory
from app.repositories.candidate_repository import CandidateProfileRepository, CandidateMemoryRepository
from app.services.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class CandidateService:
    def __init__(self, session: AsyncSession):
        self.profile_repo = CandidateProfileRepository(session)
        self.memory_repo = CandidateMemoryRepository(session)
        self.embedding_service = EmbeddingService()

    async def get_profile(self, user_id: UUID) -> Optional[CandidateProfile]:
        return await self.profile_repo.get_by_user_id(user_id)

    async def create_profile(self, user_id: UUID, profile_data: CandidateProfileCreate) -> CandidateProfile:
        existing = await self.profile_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Profile for user {user_id} already exists.")
        return await self.profile_repo.create(user_id=user_id, **profile_data.model_dump(exclude_unset=True))

    async def update_profile(self, user_id: UUID, profile_data: CandidateProfileUpdate) -> Optional[CandidateProfile]:
        updated = await self.profile_repo.update(user_id=user_id, **profile_data.model_dump(exclude_unset=True))
        if not updated:
            # Profile doesn't exist, create it
            return await self.profile_repo.create(user_id=user_id, **profile_data.model_dump(exclude_unset=True))
        return updated

    async def get_memories(self, user_id: UUID, memory_type: Optional[str] = None) -> List[CandidateMemory]:
        return await self.memory_repo.list_by_user(user_id, memory_type)

    async def resolve_memory_upsert(
        self,
        user_id: UUID,
        memory_type: str,
        content: str,
        source: str,
        confidence: float = 0.5,
        interview_id: Optional[UUID] = None
    ) -> dict:
        """
        Step 1: Generate embedding and find existing match without persisting.
        Returns a dict describing the operation to perform.
        """
        try:
            embedding = await self.embedding_service.embed_text(content)
        except Exception as e:
            logger.warning(f"Failed to generate embedding for memory: {e}")
            embedding = None

        existing = await self.memory_repo.find_similar_memory(user_id, memory_type, content, embedding=embedding)
        
        if existing:
            new_confidence = min(existing.confidence + 0.1, 0.9)
            return {
                "action": "update",
                "id": existing.id,
                "confidence": new_confidence,
                "last_verified_at": datetime.utcnow(),
                "interview_id": interview_id or existing.interview_id
            }
        else:
            return {
                "action": "insert",
                "user_id": user_id,
                "memory_type": memory_type,
                "content": content,
                "source": source,
                "confidence": confidence,
                "embedding": embedding,
                "interview_id": interview_id
            }

    async def apply_memory_upsert(self, plan: dict) -> Optional[CandidateMemory]:
        """
        Step 2: Persist the resolved memory upsert.
        """
        if plan["action"] == "update":
            return await self.memory_repo.update(
                plan["id"],
                confidence=plan["confidence"],
                last_verified_at=plan["last_verified_at"],
                interview_id=plan["interview_id"]
            )
        elif plan["action"] == "insert":
            # Remove action key
            insert_data = {k: v for k, v in plan.items() if k != "action"}
            return await self.memory_repo.create(**insert_data)
        return None

    async def upsert_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: str,
        source: str,
        confidence: float = 0.5,
        interview_id: Optional[UUID] = None
    ) -> CandidateMemory:
        """
        Legacy combined method (useful for document ingest).
        """
        plan = await self.resolve_memory_upsert(
            user_id, memory_type, content, source, confidence, interview_id
        )
        return await self.apply_memory_upsert(plan)

    async def summarize_and_update_insights(self, user_id: UUID, ai_service) -> None:
        """
        Reads all active strengths/weaknesses and synthesizes them into high-level themes.
        Marks old granular memories as superseded (by setting status or confidence).
        Wait, CandidateMemory model doesn't have a status field. We can just delete the old ones 
        or lower their confidence, or just delete them to avoid clutter. 
        As per user request: "Keep granular memories but mark them superseded."
        Let's add 'superseded' to their source or just keep them and the new ones will have source='theme_summary'.
        Actually, we can just delete the old ones for MVP simplicity, or update source='superseded'.
        Let's update their source to 'superseded'.
        """
        memories = await self.get_memories(user_id)
        active_strengths = [m.content for m in memories if m.memory_type == "strength" and m.source != "superseded"]
        active_weaknesses = [m.content for m in memories if m.memory_type == "weakness" and m.source != "superseded"]
        
        if not active_strengths and not active_weaknesses:
            return
            
        prompt = f"""[INST] Given these observations about a candidate from multiple interviews:

STRENGTHS:
{chr(10).join(active_strengths) if active_strengths else 'None'}

WEAKNESSES:
{chr(10).join(active_weaknesses) if active_weaknesses else 'None'}

Synthesize these into 3-5 high-level, actionable insights for each category.
- Group similar observations together by SUBJECT MATTER (e.g., 'Data Structures', 'System Design', 'Time Complexity Analysis').
- DO NOT mention exact implementation details (e.g. 'used erase and push_front'). Extract the generalized skill.
- Frame weaknesses as broad growth areas with actionable advice.

Return ONLY a valid JSON object. Do not include markdown formatting.
The object must have:
- "strengths" (array of strings)
- "weaknesses" (array of strings)
[/INST]"""

        try:
            # We use generic generate_response which is available on AI Service
            response_text = await ai_service.generate_response(prompt)
            import json
            
            # Clean up potential markdown formatting from response
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            data = json.loads(clean_text)
            
            # Mark old memories as superseded
            for m in memories:
                if m.source != "superseded":
                    await self.memory_repo.update(m.id, source="superseded")
                    
            # Insert new themed memories
            for s in data.get("strengths", []):
                await self.upsert_memory(user_id, "strength", s, source="theme_summary", confidence=1.0)
            for w in data.get("weaknesses", []):
                await self.upsert_memory(user_id, "weakness", w, source="theme_summary", confidence=1.0)
                
        except Exception as e:
            logger.error(f"Failed to summarize insights: {e}")
