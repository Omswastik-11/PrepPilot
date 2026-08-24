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
        return await self.profile_repo.update(user_id=user_id, **profile_data.model_dump(exclude_unset=True))

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
