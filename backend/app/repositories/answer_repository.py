"""
Answer Repository.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Answer
from app.repositories.base import BaseRepository


class AnswerRepository(BaseRepository[Answer]):
    def __init__(self, db: AsyncSession):
        super().__init__(Answer, db)

    async def get_by_question_id(self, question_id: UUID) -> Optional[Answer]:
        """Fetch an answer for a specific question."""
        result = await self.db.execute(
            select(Answer).where(Answer.question_id == question_id)
        )
        return result.scalar_one_or_none()
