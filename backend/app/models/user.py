"""
User Model.

SCHEMA DESIGN DECISIONS:
  1. UUID as Primary Key (via UUIDMixin):
     - UUIDs are globally unique — safe to generate on client or server
     - No sequential IDs exposed in URLs (security: can't guess user IDs)
     - Easier for distributed systems (no central ID counter)
     - Trade-off: Slightly larger storage (16 bytes vs 4 bytes)

  2. is_guest field:
     - Allows users to try the product without registering
     - Guest sessions can be "upgraded" to full accounts later
     - Guest data is still stored, just not behind a password

  3. Email as UNIQUE:
     - Prevents duplicate accounts
     - Database enforces this constraint — even if our code has a bug,
       the DB will reject duplicate emails

  4. role field:
     - Supports RBAC (Role-Based Access Control)
     - Default is "user" — the most common role
     - CheckConstraint ensures only valid values at the DB level
     - Prevents raw SQL or migration bugs from inserting invalid roles

  5. is_active field (ADDED IN PHASE 3):
     - Supports account deactivation and banning
     - Checked during login, token refresh, and on every authenticated request
     - Deactivation takes effect immediately for new requests (existing
       stateless access tokens remain valid until their 30-minute expiry)
     - server_default ensures existing rows get True during migration

  6. lazy="raise" on interviews relationship:
     - Forces explicit loading via selectinload() when needed
     - Prevents accidental N+1 queries and makes database access intentional
"""

from sqlalchemy import String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,  # Nullable for guest users
        index=True,      # Index for fast lookups during login
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # Nullable for guest users
    )
    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_guest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        server_default="user",
        nullable=False,
    )

    # Relationships — Using lazy="raise" to prevent accidental loading
    # This means accessing user.interviews without explicit loading will
    # raise an error, forcing you to use selectinload() when you need it.
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview",
        back_populates="user",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<User {self.email or 'guest'} role={self.role} active={self.is_active}>"
