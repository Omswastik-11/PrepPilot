"""
Base Repository.

Provides a thin generic base with the two operations that every repository
needs: fetching by primary key and adding an entity to the session.

DESIGN DECISIONS:
  - Only get_by_id() and add() are included. These are universally useful.
  - update() is NOT here because SQLAlchemy tracks dirty attributes
    automatically. Modify the object, then commit in the service.
  - delete() is NOT here because deletion semantics vary per entity
    (some soft-delete, some cascade, some have preconditions).
  - add() does NOT commit. Repositories are query executors, not
    transaction managers. The service layer owns commit/rollback.

TRANSACTION RULE:
  Repositories NEVER call commit() or rollback().
  They operate within the transaction that the service manages.
  Multiple repository calls in one service method share the same
  AsyncSession and therefore the same database transaction.
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """
    Thin generic base for all repositories.

    Provides:
      - get_by_id(id) — fetch by primary key
      - add(entity) — stage entity in the session (does NOT commit)
    """

    def __init__(self, model: type[ModelT], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """Fetch an entity by its primary key. Returns None if not found."""
        return await self.db.get(self.model, id)

    def add(self, entity: ModelT) -> None:
        """
        Add an entity to the session.

        This stages the entity for insertion. The actual INSERT is sent
        to PostgreSQL when the service calls commit() (or earlier if
        autoflush triggers on a query).
        """
        self.db.add(entity)
