"""
Authentication Schemas (Pydantic Models).

These schemas handle auth-specific request/response payloads:
  - TokenPair: Returned after login, refresh, and guest login
  - RefreshTokenRequest: Sent to the refresh endpoint

Token schemas are separated from user schemas because tokens are an
auth domain concern, not a user domain concern.
"""

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """Response schema for login/refresh — contains both tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request schema for the refresh endpoint."""
    refresh_token: str = Field(..., description="The refresh token to exchange for a new token pair")
