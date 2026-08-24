"""
Interview Schemas (Pydantic Models).
"""

from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.question import QuestionResponse


class InterviewCreate(BaseModel):
    """Data required to start a new interview."""
    interview_type: Literal["behavioral", "technical", "system_design"] = Field(
        ..., description="The type of interview"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        "medium", description="The difficulty level"
    )
    num_questions: int = Field(
        5, ge=3, le=10, description="Number of questions to generate (3-10)"
    )
    company: Optional[str] = Field(None, description="Target company for the interview")


class InterviewSummary(BaseModel):
    """Compact interview representation for lists (no questions)."""
    id: UUID
    interview_type: str
    difficulty: str
    status: str
    num_questions: int
    total_score: Optional[float]
    company: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class InterviewResponse(InterviewSummary):
    """Full interview representation including questions."""
    questions: list[QuestionResponse] = []


class InterviewListResponse(BaseModel):
    """Paginated list response for interviews."""
    items: list[InterviewSummary]
    total: int
    limit: int
    offset: int
