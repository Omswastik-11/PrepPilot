"""
Interview Repository.

Extends BaseRepository with interview-specific database queries.
Uses eager loading to avoid N+1 queries when fetching questions and answers.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import Interview
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    def __init__(self, db: AsyncSession):
        super().__init__(Interview, db)

    async def get_by_id_with_questions(self, id: UUID) -> Optional[Interview]:
        """
        Fetch interview and eagerly load questions and answers.
        Uses selectinload which emits exactly two queries total, avoiding N+1.
        """
        result = await self.db.execute(
            select(Interview)
            .where(Interview.id == id)
            .options(
                selectinload(Interview.questions).selectinload(Interview.questions.property.mapper.class_.answer)
            )
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total interviews created by a user."""
        result = await self.db.execute(
            select(func.count(Interview.id)).where(Interview.user_id == user_id)
        )
        return result.scalar_one()

    async def get_latest_guest_interview_by_ip(
        self, client_ip: str, cooldown_hours: int = 24
    ) -> Optional[Interview]:
        """
        Find the most recent guest interview originating from this IP address
        within the cooldown window.
        """
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=cooldown_hours)
        stmt = (
            select(Interview)
            .where(
                Interview.created_at >= cutoff,
                Interview.metadata_.is_not(None),
                Interview.metadata_["client_ip"].astext == client_ip,
                Interview.metadata_["is_guest"].astext == "true",
            )
            .order_by(Interview.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, status: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> tuple[list[Interview], int]:
        """
        List interviews for a user with optional status filter.
        Returns a tuple of (items, total_count) for pagination.
        """
        # Base query for counting
        count_query = select(func.count(Interview.id)).where(Interview.user_id == user_id)
        if status:
            count_query = count_query.where(Interview.status == status)
            
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Base query for items
        query = (
            select(Interview)
            .where(Interview.user_id == user_id)
            .order_by(Interview.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status:
            query = query.where(Interview.status == status)

        items_result = await self.db.execute(query)
        items = list(items_result.scalars().all())

        return items, total
