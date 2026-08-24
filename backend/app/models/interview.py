"""
Interview Model.

SCHEMA DESIGN DECISIONS:
  1. Status as VARCHAR (not boolean):
     - An interview goes through states: in_progress → completed / abandoned
     - Using a string enum is more flexible than multiple booleans
     - If we add "paused" or "reviewing" later, just add a new value
     - In production, you might use a PostgreSQL ENUM type for stricter validation

  2. metadata as JSONB:
     - JSONB is PostgreSQL's superpower — stores structured JSON natively
     - We can add arbitrary key-value data without schema migrations
     - Example: {"company": "Google", "role": "SDE-1", "resume_context": "..."}
     - This is the "extensibility" pattern — plan for data you don't know yet
     - Trade-off: No type safety on JSONB contents (unlike typed columns)

  3. Foreign Key with CASCADE:
     - ON DELETE CASCADE means: if a user is deleted, their interviews are too
     - This prevents "orphan records" (interviews pointing to deleted users)
     - Alternative: ON DELETE SET NULL (keep interview, set user_id to NULL)

  4. Composite Index on (user_id, status) — ADDED IN PHASE 2:
     - The most common query pattern: "Get all in-progress interviews for user X"
     - Without this index, PostgreSQL scans the entire interviews table
     - With this index, it jumps directly to the matching rows
     - This is called a "covering index" when both columns are in the WHERE clause

  5. lazy="raise" on questions relationship — CHANGED IN PHASE 2:
     - Forces explicit loading. When you list interviews, you don't
       automatically load all questions for each interview.
     - When you need questions (e.g., viewing a single interview), you
       explicitly use selectinload(Interview.questions)

INTERVIEW QUESTION: "When would you use JSONB vs adding a new column?"
  → JSONB: For optional/varying metadata that doesn't need indexing
  → New column: For data you'll query/filter/sort on frequently
  → Rule of thumb: If you'll put it in a WHERE clause, make it a column
"""

import uuid

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, UUIDMixin, TimestampMixin


class Interview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interviews"

    # Table-level configuration
    __table_args__ = (
        # Composite index: speeds up "get all interviews with status X for user Y"
        # This is the most common query pattern in the application
        Index("ix_interviews_user_id_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,  # Single-column index still useful for "all interviews for user X"
    )
    interview_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="medium",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="in_progress",
    )
    num_questions: Mapped[int] = mapped_column(
        Integer,
        default=5,
    )
    total_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    company: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    started_at: Mapped[DateTime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",  # Column name in DB (metadata_ avoids conflict with SQLAlchemy's .metadata)
        JSONB,
        nullable=True,
    )

    # Relationships — lazy="raise" forces explicit loading
    user: Mapped["User"] = relationship(
        "User",
        back_populates="interviews",
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="interview",
        lazy="raise",
        order_by="Question.question_order",
    )

    def __repr__(self) -> str:
        return f"<Interview {self.interview_type} - {self.status}>"
