"""
Authentication Service.

This is the business logic layer for authentication. It orchestrates:
  - User registration (duplicate check → hash password → persist)
  - Login (find user → verify password → issue tokens)
  - Token refresh (validate refresh JWT → check user → issue new pair)
  - Guest login (create guest user → issue tokens)

TRANSACTION OWNERSHIP:
  This service owns transaction boundaries. It calls commit() after
  successful write operations. Repositories never commit.

  The AsyncSession is request-scoped (one per HTTP request, provided
  by get_db()). All repository operations within a single service
  method share the same transaction. If any step fails, get_db()
  rolls back automatically.

  Keep transactions short: avoid holding a transaction open across
  slow non-database work (e.g., external API calls).

SECURITY NOTES:
  - Login returns the SAME generic error for nonexistent email, wrong
    password, and inactive account. This prevents user enumeration.
  - Password hashing and JWT operations are delegated to utils/security.py.
  - IntegrityError is caught as a fallback for the race condition where
    two concurrent requests pass the application-level duplicate check.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.exceptions import AlreadyExistsError, AuthenticationError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    """
    Authentication business logic.

    Receives an AsyncSession via dependency injection. Constructs its
    own UserRepository from that session. This ensures the service and
    its repository share the same transaction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        """
        Register a new user.

        1. Check if email already exists (application-level courtesy check)
        2. Hash the password
        3. Create the User entity
        4. Commit (with IntegrityError fallback for race conditions)

        The application-level check gives a clean error message.
        The DB UNIQUE constraint is the actual concurrency-safe guarantee.
        """
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise AlreadyExistsError("User with this email already exists")

        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            name=data.name,
            is_guest=False,
        )

        self.user_repo.add(user)

        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise AlreadyExistsError("User with this email already exists")

        return user

    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user and return a token pair.

        SECURITY: Returns the SAME error message for all failure cases
        (nonexistent email, wrong password, inactive account) to prevent
        user enumeration attacks.
        """
        generic_error = "Invalid email or password"

        user = await self.user_repo.get_by_email(email)

        if not user or not user.password_hash:
            raise AuthenticationError(generic_error)

        if not verify_password(password, user.password_hash):
            raise AuthenticationError(generic_error)

        # Inactive accounts get the same generic error during login
        # to prevent account enumeration via error message differences
        if not user.is_active:
            raise AuthenticationError(generic_error)

        return self._create_token_pair(str(user.id))

    async def refresh(self, refresh_token: str) -> dict:
        """
        Exchange a refresh token for a new token pair.

        1. Decode and validate the refresh JWT (checks signature, expiry, type)
        2. Fetch the user from DB (they might have been deleted since token was issued)
        3. Check is_active (admin might have deactivated the account)
        4. Issue a new access + refresh pair

        NOTE: This is stateless — the old refresh token remains valid
        until its own expiry. True single-use tokens require server-side
        state (planned for Phase 8 with Redis).
        """
        payload = decode_token(refresh_token, expected_type="refresh")

        user = await self.user_repo.get_by_id(payload["sub"])
        if not user:
            raise AuthenticationError("Invalid token")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return self._create_token_pair(str(user.id))

    async def guest_login(self) -> tuple[User, dict]:
        """
        Create a guest user and return the user + token pair.

        Guest users have no email/password and is_guest=True.
        They receive the same JWT tokens as regular users.
        """
        user = User(is_guest=True)
        self.user_repo.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        tokens = self._create_token_pair(str(user.id))
        return user, tokens

    @staticmethod
    def _create_token_pair(user_id: str) -> dict:
        """Create an access + refresh token pair for the given user ID."""
        return {
            "access_token": create_access_token(subject=user_id),
            "refresh_token": create_refresh_token(subject=user_id),
            "token_type": "bearer",
        }
