"""
Interview Schemas (Pydantic Models).
"""

from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, computed_field

from app.schemas.question import QuestionResponse


class InterviewCreate(BaseModel):
    """Data required to start a new interview."""
    interview_type: Literal["behavioral", "technical", "system_design"] = Field(
        ..., description="The type of interview"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        "medium", description="The difficulty level"
    )
    duration_minutes: Literal[20, 40, 60] = Field(
        40, description="Duration of the interview in minutes"
    )
    num_questions: Optional[int] = Field(
        None, ge=3, le=10, description="Number of questions to generate (3-10)"
    )
    company: Optional[str] = Field(None, description="Target company for the interview")
    role: Optional[str] = Field(None, description="Target role for the interview")


class InterviewTitleUpdate(BaseModel):
    title: str

class InterviewSummary(BaseModel):
    """Compact interview representation for lists (no questions)."""
    id: UUID
    interview_type: str
    difficulty: str
    status: str
    num_questions: Optional[int]
    duration_minutes: Optional[int]
    total_score: Optional[float]
    company: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata_: Optional[dict] = None

    @computed_field
    def title(self) -> str:
        if self.metadata_ and "title" in self.metadata_:
            return self.metadata_["title"]
        # Default fallback
        parts = []
        if self.company: parts.append(self.company.capitalize())
        if self.metadata_ and "target_role" in self.metadata_:
            parts.append(self.metadata_["target_role"].title())
        if parts:
            return f"{' '.join(parts)} Mock"
        return f"{self.interview_type.replace('_', ' ').title()} Interview"

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
