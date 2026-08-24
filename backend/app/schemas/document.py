from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_type: str

class DocumentCreate(DocumentBase):
    content: str

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
