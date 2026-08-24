"""
Test Configuration and Fixtures.

Uses PostgreSQL for all integration/API tests — not SQLite.
SQLite lacks UUID support, ARRAY types, CHECK constraints, and
PostgreSQL-specific behaviors that production relies on.

The test database reuses the same Docker PostgreSQL instance but
with a separate database name ('preppilot_test') to isolate test
data from development data.

Each test function gets a fresh transaction that is rolled back after
the test completes, so tests don't interfere with each other.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Base

settings = get_settings()

_db_url = str(settings.DATABASE_URL)
TEST_DATABASE_URL = _db_url.rsplit("/", 1)[0] + "/preppilot_test"

from sqlalchemy.pool import NullPool

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    yield async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database(test_engine):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine as create_eng

    admin_engine = create_eng(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS preppilot_test"))
        await conn.execute(text("CREATE DATABASE preppilot_test"))
    await admin_engine.dispose()

    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(autouse=True)
async def cleanup_database(test_session_factory):
    """Clean up the database before each test."""
    async with test_session_factory() as cleanup_session:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_session.execute(table.delete())
        await cleanup_session.commit()
    yield

@pytest_asyncio.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "768")

@pytest.fixture(autouse=True)
def mock_genai_client_global():
    from unittest.mock import AsyncMock, patch, MagicMock
    with patch("app.services.ai.embedding_service.genai.Client") as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_response.embeddings = [mock_embedding]
        mock_instance.aio.models.embed_content = AsyncMock(return_value=mock_response)
        yield mock_instance
