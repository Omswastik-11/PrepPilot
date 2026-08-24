"""
Question & Answer Models.

SCHEMA DESIGN DECISIONS:
  1. Separate Question and Answer tables (not embedded in Interview):
     - Follows database normalization (3NF) — each entity gets its own table
     - Allows querying questions and answers independently
     - Example: "Show me all DSA questions across all interviews" — easy with a separate table
     - If we embedded Q&A as JSON in Interview, such queries would be painful

  2. question_order field:
     - Interviews need a deterministic order (Question 1, 2, 3...)
     - We can't rely on insertion order or timestamps for ordering
     - This explicit field makes the order clear and queryable

  3. UniqueConstraint on (interview_id, question_order) — ADDED IN PHASE 2:
     - Prevents inserting two questions with the same order in one interview
     - Without this, a bug in your code could create: Q1, Q1, Q3
     - The database enforces business rules that your code might miss
     - This is "defense in depth" — don't trust application code alone

  4. One Answer per Question (1:1 relationship):
     - In the MVP, each question gets exactly one answer
     - We use a foreign key from Answer → Question (not the other way around)
     - If we later support multiple attempts, just remove the UNIQUE constraint
     - This is easier than trying to store all data in one table

  5. ARRAY type for strengths/weaknesses:
     - PostgreSQL supports native arrays — perfect for lists of strings
     - Alternative: Store as JSON, or create a separate strengths table
     - Arrays are simpler for lists of uniform type (all strings)

INTERVIEW QUESTION: "How do you handle 1:1 vs 1:N relationships?"
  → 1:1 (Question ↔ Answer): Foreign key on either side, add UNIQUE constraint
  → 1:N (Interview → Questions): Foreign key on the "many" side (questions table)
  → M:N (User ↔ Companies): Needs a junction/bridge table
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.models.base import Base, UUIDMixin, TimestampMixin


class Question(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "questions"

    # Table-level constraints
    __table_args__ = (
        # Prevents duplicate question_order within the same interview
        # Without this, nothing stops: Interview X → [Q1, Q1, Q3]
        UniqueConstraint("interview_id", "question_order", name="uq_interview_question_order"),
    )

    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        index=True,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    time_limit_seconds: Mapped[int] = mapped_column(
        Integer,
        default=120,
    )
    ideal_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,  # Filled after AI evaluation
    )
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    adaptation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    interview: Mapped["Interview"] = relationship(
        "Interview",
        back_populates="questions",
    )
    answer: Mapped["Answer | None"] = relationship(
        "Answer",
        back_populates="question",
        uselist=False,  # 1:1 relationship — single answer per question
    )

    def __repr__(self) -> str:
        return f"<Question {self.question_order}: {self.question_text[:50]}...>"


class Answer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        unique=True,  # Enforces 1:1 at database level
        index=True,
    )
    user_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,  # Can be null if user skipped or timed out
    )
    time_taken_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,  # Filled after AI evaluation
    )
    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    strengths: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    weaknesses: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="answer",
    )

    def __repr__(self) -> str:
        return f"<Answer score={self.score}>"
