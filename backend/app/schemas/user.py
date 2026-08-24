"""
User Schemas (Pydantic Models).

SCHEMA DESIGN DECISIONS:
  1. Separation of DB Models (SQLAlchemy) and API Schemas (Pydantic):
     - SQLAlchemy models represent database tables.
     - Pydantic models represent API request/response payloads.
     - Why separate?
       - Security: You never want to return the password hash in the API.
       - Validation: Pydantic validates incoming JSON before it hits your logic.
       - Documentation: FastAPI uses Pydantic to auto-generate Swagger UI.

  2. Base Schema Pattern:
     - `UserBase`: Shared fields (email, name)
     - `UserCreate`: Fields needed for registration (inherits Base + password)
     - `UserResponse`: What we send back to the client (inherits Base + id, created_at)
     - This DRY (Don't Repeat Yourself) approach keeps schemas clean.

  Token-related schemas have been moved to schemas/auth.py — they are
  auth domain concerns, not user domain concerns.
"""

from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared fields for User schemas."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """
    Data required to create a new user.
    We require email and password for standard registration.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserResponse(UserBase):
    """
    Data returned to the client when querying a user.
    Notice we DO NOT include password_hash here — sensitive fields
    must never leak through response schemas.
    """
    id: uuid.UUID
    is_guest: bool
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """
        orm_mode (from_attributes in Pydantic v2) allows Pydantic to read data
        from SQLAlchemy objects (which use object.attribute) instead of just dicts.
        """
        from_attributes = True
