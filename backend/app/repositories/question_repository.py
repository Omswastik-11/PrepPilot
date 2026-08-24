"""
Question Repository.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    def __init__(self, db: AsyncSession):
        super().__init__(Question, db)

    async def get_with_answer(self, question_id: UUID) -> Optional[Question]:
        """Fetch question and eagerly load its answer."""
        result = await self.db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.answer))
        )
        return result.scalar_one_or_none()

    async def get_unanswered_count(self, interview_id: UUID) -> int:
        """
        Count how many questions in the given interview do not have an answer yet.
        Used to determine if an interview can be marked as completed.
        """
        result = await self.db.execute(
            select(func.count(Question.id))
            .where(Question.interview_id == interview_id)
            .where(~Question.answer.has())
        )
        return result.scalar_one()
