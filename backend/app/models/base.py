"""
Model Base Classes and Mixins.

ENGINEERING CONTEXT:
  This file provides the foundational building blocks for ALL database models.
  Instead of repeating `id`, `created_at`, `updated_at` in every model, we
  define them once here as "mixins" — reusable building blocks.

  WHY MIXINS INSTEAD OF A SINGLE BASE CLASS?
    - Mixins follow the "composition over inheritance" principle
    - A model can pick and choose which mixins it needs
    - TimestampMixin can be used even on tables that don't use UUID primary keys
    - This is the same pattern used by Flask-SQLAlchemy, Django, and most ORMs

  WHY IS Base DEFINED HERE (not in database.py)?
    - Single Responsibility: database.py manages connections/sessions
    - This file manages model infrastructure (base class, mixins)
    - Prevents import cycles: models need Base, and database.py might
      eventually need to import models (e.g., for health checks)

  WHY server_default?
    - `default=func.now()` runs in Python when using the ORM
    - `server_default=func.now()` generates DEFAULT NOW() in the SQL schema
    - Both are needed: ORM uses the Python default, raw SQL uses the server default
    - This is "defense in depth" — the database enforces defaults even if
      someone bypasses the ORM (Alembic migration, admin panel, raw query)

  WHY onupdate for updated_at?
    - `onupdate=func.now()` tells SQLAlchemy to set this field automatically
      whenever a row is modified through the ORM
    - The database-level equivalent would be a trigger, which is more complex
    - Trade-off: If you update a row via raw SQL, `updated_at` won't change
      unless you add a PostgreSQL trigger separately
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Every model (User, Interview, Question, Answer) inherits from this.
    SQLAlchemy uses this to:
      1. Track all models via Base.metadata
      2. Generate CREATE TABLE statements
      3. Power Alembic's auto-detection of schema changes
    """
    pass


class UUIDMixin:
    """
    Mixin that adds a UUID primary key to any model.

    DESIGN DECISION:
      - UUID v4 (random) instead of UUID v1 (time-based) or auto-increment
      - Random UUIDs prevent ID enumeration attacks (/users/1, /users/2, ...)
      - Can be generated client-side or server-side without coordination
      - Trade-off: Slightly worse B-tree index locality than sequential IDs
        (inserts go to random positions in the index, not appended at the end)
      - At our scale (thousands of rows), this trade-off is irrelevant
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at to any model.

    PRODUCTION PATTERN:
      - Every table in a production system should have these two columns
      - created_at: When the record was first inserted (immutable after creation)
      - updated_at: When the record was last modified (auto-updates on change)

    USE CASES:
      - Auditing: "When was this user created? When was their profile last changed?"
      - Caching: "Has this record changed since I last fetched it?" (HTTP ETag)
      - Debugging: "This interview was created 3 days ago but updated 2 minutes ago"
      - Conflict detection: Optimistic locking uses updated_at to detect
        concurrent modifications
      - Data pipelines: "Give me all records modified since yesterday"
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
