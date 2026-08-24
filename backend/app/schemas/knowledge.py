from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class KnowledgeSourceBase(BaseModel):
    source_type: str
    reference: str
    content: str

class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass

class KnowledgeSourceResponse(KnowledgeSourceBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionBankBase(BaseModel):
    domain: str
    topic: str
    difficulty: str
    question_text: str
    expected_key_points: Optional[str] = None
    knowledge_source_id: Optional[UUID] = None

class QuestionBankCreate(QuestionBankBase):
    pass

class QuestionBankResponse(QuestionBankBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
