"""
PrepPilot Backend Configuration.

Uses pydantic-settings to load environment variables with type validation.
This is a pattern you'll see in production FastAPI apps — it gives you:
  1. Type-safe config (no more raw os.getenv() everywhere)
  2. Validation at startup (app crashes immediately if config is wrong)
  3. Default values for development
  4. Easy to mock in tests

SYSTEM DESIGN NOTE:
  This follows the "Fail Fast" principle — if required config is missing,
  the app won't start. Better to crash at startup than serve broken responses.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://preppilot:preppilot_dev_password@localhost:5432/preppilot"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """Ensure standard Postgres URLs from cloud providers use asyncpg driver."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            if "sslmode=" in v:
                v = v.replace("sslmode=", "ssl=")
            # Remove channel_binding parameter (unsupported by asyncpg connection args)
            if "channel_binding=" in v:
                import re
                v = re.sub(r"([?&])channel_binding=[^&]+(&?)", r"\1", v)
                v = v.rstrip("&?").replace("?&", "?")
        return v

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Providers Config
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30
    GEMINI_MAX_RETRIES: int = 1

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT_SECONDS: int = 30
    GROQ_MAX_RETRIES: int = 1

    AI_PRIMARY_PROVIDER: str = "gemini"
    AI_FALLBACK_PROVIDER: str = "groq"

    # Memory Dedup
    MEMORY_DEDUP_THRESHOLD: float = 0.25

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # Web Search Settings
    WEB_SEARCH_ENABLED: bool = False
    WEB_SEARCH_PROVIDER: str = "gemini"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    # Application
    APP_NAME: str = "PrepPilot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Rate Limiting & Abuse Prevention
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_AI_GUEST_PER_MINUTE: int = 5
    RATE_LIMIT_AI_USER_PER_MINUTE: int = 20
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60
    GUEST_COOLDOWN_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    DESIGN DECISION: Using @lru_cache ensures we only parse the .env file once.
    Every subsequent call returns the same Settings object from memory.
    This is a common FastAPI pattern — you'll see it in dependency injection.
    """
    return Settings()
