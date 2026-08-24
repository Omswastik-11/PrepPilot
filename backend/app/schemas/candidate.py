from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class CandidateProfileBase(BaseModel):
    target_roles: Optional[List[str]] = None
    target_companies: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    preferred_interview_types: Optional[List[str]] = None
    bio: Optional[str] = None

class CandidateProfileCreate(CandidateProfileBase):
    pass

class CandidateProfileUpdate(CandidateProfileBase):
    pass

class CandidateProfileResponse(CandidateProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CandidateMemoryBase(BaseModel):
    memory_type: str = Field(..., description="strength, weakness, preference, experience, skill, or note")
    content: str
    source: str = Field(..., description="resume, user_input, interview_answer, ai_inference, or manual_note")
    confidence: Optional[float] = 0.5
    interview_id: Optional[UUID] = None

class CandidateMemoryCreate(CandidateMemoryBase):
    pass

class CandidateMemoryResponse(CandidateMemoryBase):
    id: UUID
    user_id: UUID
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
