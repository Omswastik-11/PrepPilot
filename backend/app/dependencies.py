"""
Dependency Injection Wiring.

This is the composition root — where all pieces are wired together.
Routes declare what they need via Depends(), and these functions
provide the concrete implementations.

CONTAINS:
  1. Service factories — get_auth_service()
  2. Authentication — get_current_user()
  3. Authorization — require_role()

ARCHITECTURE:
  - get_current_user is a standalone dependency, NOT a method on AuthService.
    It's infrastructure plumbing (decode JWT → fetch user), not business logic.
  - require_role() is a dependency factory that returns a Depends-compatible
    function. It wraps get_current_user and adds a role check.

AUTHENTICATION FLOW:
  Authorization header
      ↓
  get_current_user()
      ↓
  decode/verify JWT via decode_token()
      ↓
  require type == "access"
      ↓
  extract sub (user ID)
      ↓
  fetch User from DB
      ↓
  check is_active
      ↓
  return User object

RBAC FLOW:
  require_role("admin")
      ↓
  get_current_user()   (authentication)
      ↓
  check user.role in allowed_roles
      ↓
  return User or raise 403
"""

from typing import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.interview_service import InterviewService
from app.services.ai.service import AIService
from app.utils.security import decode_token

# OAuth2PasswordBearer extracts the token from the Authorization header.
# tokenUrl tells Swagger UI where to send the login request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Service Factories
# ---------------------------------------------------------------------------

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Provide an AuthService wired to the request-scoped session."""
    return AuthService(db)


async def get_ai_service() -> AIService:
    """Provide the AIService singleton/instance."""
    return AIService()


async def get_interview_service(
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> InterviewService:
    """Provide an InterviewService with DB and AI injected."""
    return InterviewService(db, ai_service)


# ---------------------------------------------------------------------------
# Authentication Dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that authenticates the current request.

    Extracts the Bearer token, decodes it, fetches the user from
    the database, and checks that the account is active.

    Raises AuthenticationError (→ 401) if any step fails.
    """
    # decode_token validates signature, expiry, and token type
    payload = decode_token(token, expected_type="access")
    user_id = payload["sub"]

    # Fetch user from DB — the user might have been deleted since
    # the token was issued
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise AuthenticationError("Invalid token")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated")

    return user


# ---------------------------------------------------------------------------
# Authorization Dependency Factory
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin/users")
        async def list_users(user: User = Depends(require_role("admin"))):
            ...

    How it works:
        1. Runs get_current_user first (authentication)
        2. Checks user.role against the allowed roles
        3. Returns the User if authorized, raises 403 if not
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{current_user.role}' is not authorized. "
                f"Required: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker
