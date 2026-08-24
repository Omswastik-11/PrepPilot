from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class InterviewState(BaseModel):
    interview_id: UUID
    current_difficulty: str = Field(default="Junior", description="Junior, Mid, Senior, Principal")
    target_role: Optional[str] = None
    skills_to_test: List[str] = Field(default_factory=list)
    skills_tested: List[str] = Field(default_factory=list)
    recent_performance: List[float] = Field(default_factory=list) # Last N scores
    weaknesses_identified: List[str] = Field(default_factory=list)

class PlannedQuestion(BaseModel):
    domain: str
    topic: str
    difficulty: str
    adaptation_reason: str
    context_used: Optional[str] = None
    
    # If retrieved from question bank
    question_bank_id: Optional[UUID] = None
    
    # If generated dynamically
    question_text: Optional[str] = None
    expected_key_points: Optional[str] = None
