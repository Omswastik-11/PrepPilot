"""
Question & Answer Schemas (Pydantic Models).
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class AnswerCreate(BaseModel):
    """Data required to submit an answer."""
    user_answer: str = Field(..., min_length=1, description="The user's answer text")
    time_taken_seconds: int = Field(..., ge=1, description="Time taken to answer in seconds")


class AnswerResponse(BaseModel):
    """Answer response, including AI evaluation."""
    id: UUID
    user_answer: Optional[str]
    time_taken_seconds: Optional[int]
    score: Optional[float]
    feedback: Optional[str]
    strengths: Optional[list[str]]
    weaknesses: Optional[list[str]]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """Question response, optionally including the answer."""
    id: UUID
    question_text: str
    question_order: int
    time_limit_seconds: int
    domain: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    answer: Optional[AnswerResponse] = None

    class Config:
        from_attributes = True
