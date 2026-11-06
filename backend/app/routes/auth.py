"""
Authentication Routes.

These are thin HTTP adapters. They:
  1. Accept HTTP requests and validate input via Pydantic schemas
  2. Delegate to AuthService for business logic
  3. Return HTTP responses

Routes contain NO business logic, NO SQLAlchemy queries, NO password
hashing. They are pure HTTP plumbing.

ENDPOINTS:
  POST /register  — Create a new user account
  POST /login     — Authenticate and receive tokens
  POST /refresh   — Exchange refresh token for new token pair
  POST /logout    — Client-side logout (server acknowledges)
  GET  /me        — Get current user's profile
  POST /guest     — Create a guest session
"""

import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
import httpx

from app.config import get_settings

from app.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import TokenPair, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    user = await auth_service.register(user_in)
    return user


@router.post("/login", response_model=TokenPair)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    OAuth2-compatible token login.

    Expects form data with `username` (which is the email) and `password`.
    Returns an access + refresh token pair.
    """
    tokens = await auth_service.login(
        email=form_data.username,
        password=form_data.password,
    )
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Exchange a refresh token for a new access + refresh token pair.

    Send the refresh token in the request body (NOT in the Authorization
    header — that's for access tokens only).

    NOTE: With stateless JWTs, the old refresh token remains valid until
    its own expiry. Server-side revocation is planned for Phase 8 (Redis).
    """
    tokens = await auth_service.refresh(body.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user.

    NOTE: With stateless JWTs, this endpoint cannot server-side revoke
    tokens. The client MUST delete stored tokens. Already-issued access
    tokens remain valid until expiry (max 30 minutes).

    Server-side revocation is planned for Phase 8 (Redis token blacklist).

    This endpoint still requires a valid Bearer token to confirm the user
    is authenticated before acknowledging logout.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get the currently authenticated user's profile.

    Read-only — no database commit needed. The user object is already
    fetched by the get_current_user dependency.
    """
    return current_user


@router.post("/guest", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def guest_login(
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Create a guest user and return tokens.

    Guest users can access all non-admin features without registering.
    Their data is persisted and associated with a unique user ID.
    """
    _user, tokens = await auth_service.guest_login()
    return tokens


@router.get("/google/login")
async def google_login_redirect():
    """Redirect to Google's OAuth consent screen."""
    settings = get_settings()
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google Auth credentials not configured (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET missing)")
        return RedirectResponse(f"{frontend_url}/login?error={quote('Google Auth is not configured. Please check environment variables.')}")
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&response_type=code&scope=openid%20email%20profile&redirect_uri={quote(redirect_uri, safe=':/')}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Handle Google OAuth callback and exchange code for token."""
    settings = get_settings()
    frontend_url = settings.FRONTEND_URL.rstrip("/")

    if error:
        logger.warning(f"Google OAuth returned error: {error}")
        return RedirectResponse(f"{frontend_url}/login?error={quote(f'Google sign-in error: {error}')}")

    if not code:
        logger.warning("Google OAuth callback received without code")
        return RedirectResponse(f"{frontend_url}/login?error={quote('No authorization code provided by Google.')}")

    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )
            if token_response.status_code != 200:
                logger.error(f"Failed to exchange Google code: {token_response.text}")
                return RedirectResponse(f"{frontend_url}/login?error={quote('Failed to authenticate with Google.')}")
                
            access_token = token_response.json().get("access_token")
            
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if user_info_response.status_code != 200:
                logger.error(f"Failed to fetch Google user info: {user_info_response.text}")
                return RedirectResponse(f"{frontend_url}/login?error={quote('Failed to fetch user profile from Google.')}")
                
            user_data = user_info_response.json()
            
        tokens = await auth_service.google_login(
            email=user_data["email"],
            name=user_data.get("name", "")
        )
        
        callback_url = f"{frontend_url}/auth/callback"
        return RedirectResponse(f"{callback_url}?token={tokens['access_token']}")
    except Exception as e:
        logger.exception(f"Unexpected error in Google OAuth callback: {e}")
        return RedirectResponse(f"{frontend_url}/login?error={quote('Unexpected error during Google sign-in.')}")
