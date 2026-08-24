from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, or_
from typing import Optional, List
from uuid import UUID
import logging

from app.models.candidate import CandidateProfile, CandidateMemory

logger = logging.getLogger(__name__)

class CandidateProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> Optional[CandidateProfile]:
        result = await self.session.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, **kwargs) -> CandidateProfile:
        profile = CandidateProfile(user_id=user_id, **kwargs)
        self.session.add(profile)
        return profile

    async def update(self, user_id: UUID, **kwargs) -> Optional[CandidateProfile]:
        # Filter out None values to not overwrite existing arrays with None
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_user_id(user_id)
            
        result = await self.session.execute(
            update(CandidateProfile)
            .where(CandidateProfile.user_id == user_id)
            .values(**update_data)
            .returning(CandidateProfile)
        )
        return result.scalar_one_or_none()

class CandidateMemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, memory_id: UUID) -> Optional[CandidateMemory]:
        result = await self.session.execute(
            select(CandidateMemory).where(CandidateMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, 
        user_id: UUID, 
        memory_type: Optional[str] = None
    ) -> List[CandidateMemory]:
        query = select(CandidateMemory).where(CandidateMemory.user_id == user_id)
        if memory_type:
            query = query.where(CandidateMemory.memory_type == memory_type)
            
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> CandidateMemory:
        memory = CandidateMemory(**kwargs)
        self.session.add(memory)
        return memory

    async def update(self, memory_id: UUID, **kwargs) -> Optional[CandidateMemory]:
        result = await self.session.execute(
            update(CandidateMemory)
            .where(CandidateMemory.id == memory_id)
            .values(**kwargs)
            .returning(CandidateMemory)
        )
        return result.scalar_one_or_none()
        
    async def find_similar_memory(
        self, user_id: UUID, memory_type: str, content: str, embedding: Optional[list[float]] = None
    ) -> Optional[CandidateMemory]:
        """
        Uses vector similarity if embedding is provided, otherwise falls back to exact text match.
        """
        from app.config import get_settings
        settings = get_settings()

        query = select(CandidateMemory).where(
            CandidateMemory.user_id == user_id,
            CandidateMemory.memory_type == memory_type
        )

        if embedding:
            # Vector similarity search
            distance = CandidateMemory.embedding.l2_distance(embedding)
            query = query.where(distance < settings.MEMORY_DEDUP_THRESHOLD).order_by(distance).limit(1)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        else:
            # Fallback to exact match or highly overlapping text
            query = query.where(
                or_(
                    CandidateMemory.content.ilike(f"%{content}%"),
                )
            )
            result = await self.session.execute(query)
            matches = list(result.scalars().all())
            
            for memory in matches:
                if content.lower() in memory.content.lower() or memory.content.lower() in content.lower():
                    return memory
                    
            return None
