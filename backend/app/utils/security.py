"""
Security Utilities for Authentication.

This module handles the cryptographic primitives of authentication:
  - Password hashing (bcrypt)
  - JWT creation and validation

IMPORTANT: This module is a utility, not a service. It contains pure
functions with no database access and no business logic. The AuthService
uses these utilities to implement auth business rules.

PASSWORD HASHING:
  We use bcrypt via passlib. bcrypt is intentionally slow (~100ms per hash)
  to make brute-force attacks impractical. A salt is automatically generated
  and embedded in each hash.

JWT DESIGN:
  Access tokens and refresh tokens are both stateless JWTs, but they have
  different claims:
    - Access token: type="access", short-lived (30 min)
    - Refresh token: type="refresh", long-lived (7 days)

  The `type` claim prevents cross-use: a refresh token cannot be used as
  a Bearer token, and an access token cannot be sent to the refresh endpoint.

  LIMITATION: Stateless JWTs cannot be revoked server-side. If a token is
  stolen, it remains valid until expiry. Server-side revocation (via Redis
  token blacklist) is planned for Phase 8.

  No `role` is embedded in tokens. The role is fetched from the database
  on every authenticated request via get_current_user(). This ensures
  role changes (e.g., admin demotion) take effect immediately rather than
  waiting for token expiry.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.config import get_settings
from app.exceptions import AuthenticationError

settings = get_settings()

# Setup passlib with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided plain password matches the hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for a password."""
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a short-lived JWT access token.

    Claims:
      sub  — user ID (UUID string)
      type — "access" (prevents use as refresh token)
      exp  — expiration timestamp
      iat  — issued-at timestamp
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode = {
        "sub": str(subject),
        "type": "access",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a long-lived JWT refresh token.

    Claims:
      sub  — user ID (UUID string)
      type — "refresh" (prevents use as access token)
      exp  — expiration timestamp
      iat  — issued-at timestamp

    NOTE: This is a stateless JWT. It cannot be revoked server-side.
    The previous refresh token remains valid until its own expiry.
    True rotation/revocation requires server-side state (Phase 8 — Redis).
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    to_encode = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The raw JWT string.
        expected_type: Either "access" or "refresh". Tokens of the wrong
                       type are rejected to prevent cross-use.

    Returns:
        The decoded payload dict (contains sub, type, exp, iat).

    Raises:
        AuthenticationError: If the token is expired, malformed, tampered
                             with, or has the wrong type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except JWTError:
        raise AuthenticationError("Invalid token")

    # Validate required claims
    if not payload.get("sub"):
        raise AuthenticationError("Invalid token")

    # Validate token type — prevents using a refresh token as a Bearer token
    token_type = payload.get("type")
    if token_type != expected_type:
        raise AuthenticationError(f"Expected {expected_type} token")

    return payload
