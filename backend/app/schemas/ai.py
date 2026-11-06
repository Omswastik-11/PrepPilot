"""
AI Schemas (Pydantic Models).

Defines the structured output expected from AI providers.
These are the Pydantic schemas that we enforce when calling Gemini/HF.
"""

from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    """What the AI returns for each generated question."""
    question_text: str = Field(..., description="The question text")
    time_limit_seconds: int = Field(..., ge=60, le=300, description="Recommended time limit for answering")
    ideal_answer_hints: list[str] = Field(..., description="Bullet points of what a good answer includes")
    topic: str | None = Field(
        None,
        description="A concise 1-3 word title or competency tag describing the specific topic tested (e.g. 'Conflict Resolution', 'Dynamic Programming', 'Scalability', 'System Design')"
    )


class EvaluationResult(BaseModel):
    """What the AI returns for answer evaluation."""
    score: float = Field(..., ge=0.0, le=10.0, description="Score from 0.0 to 10.0")
    feedback: str = Field(..., description="2-3 sentence overall assessment")
    strengths: list[str] = Field(..., description="1-3 specific strengths")
    weaknesses: list[str] = Field(..., description="1-3 specific areas for improvement")
    ideal_answer: str = Field(..., description="What a perfect answer would include")
