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

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://preppilot:preppilot_dev_password@localhost:5432/preppilot"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Providers Config
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30
    GEMINI_MAX_RETRIES: int = 1

    HF_TOKEN: str = ""
    HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    HF_TIMEOUT_SECONDS: int = 30
    HF_MAX_RETRIES: int = 1

    AI_PRIMARY_PROVIDER: str = "gemini"
    AI_FALLBACK_PROVIDER: str = "huggingface"

    # Memory Dedup
    MEMORY_DEDUP_THRESHOLD: float = 0.25

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # Web Search Settings
    WEB_SEARCH_ENABLED: bool = False
    WEB_SEARCH_PROVIDER: str = "gemini"

    # Application
    APP_NAME: str = "PrepPilot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    DESIGN DECISION: Using @lru_cache ensures we only parse the .env file once.
    Every subsequent call returns the same Settings object from memory.
    This is a common FastAPI pattern — you'll see it in dependency injection.
    """
    return Settings()
