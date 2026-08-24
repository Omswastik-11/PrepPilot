"""
User Repository.

Extends BaseRepository with user-specific database queries.
This is the ONLY place where SQLAlchemy query code for the User
entity lives. Services never import `select` or write raw queries.

DESIGN NOTE:
  get_by_email() is the most performance-critical query in auth —
  it's called on every login. The `users.email` column has an index
  (defined in the User model) so this is an O(log n) B-tree lookup.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity persistence operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch a user by email address.

        Used during login and duplicate-email checks during registration.
        Returns None if no user with this email exists.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
