"""
API tests for authentication endpoints.

Full-stack tests that hit the FastAPI app with a PostgreSQL test database.
Each test function gets a fresh database state (cleaned between tests).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.utils.security import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def register_user(client: AsyncClient, email: str = "test@example.com", password: str = "password123", name: str = "Test User"):
    """Helper to register a user and return the response."""
    return await client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
    })


async def login_user(client: AsyncClient, email: str = "test@example.com", password: str = "password123"):
    """Helper to login and return the response."""
    return await client.post("/api/auth/login", data={
        "username": email,
        "password": password,
    })


async def register_and_login(client: AsyncClient, email: str = "test@example.com", password: str = "password123"):
    """Helper to register a user and login, returning the token pair."""
    await register_user(client, email=email, password=password)
    resp = await login_user(client, email=email, password=password)
    return resp.json()


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        resp = await register_user(client)
        assert resp.status_code == 201

        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["is_guest"] is False
        assert data["is_active"] is True
        assert data["role"] == "user"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        # password_hash must NEVER appear in the response
        assert "password_hash" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        await register_user(client)
        resp = await register_user(client)  # Same email again
        assert resp.status_code == 409
        assert "already exists" in resp.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "short",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        await register_user(client)
        resp = await login_user(client)
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await register_user(client)
        resp = await login_user(client, password="wrong_password")
        assert resp.status_code == 401
        assert "invalid email or password" in resp.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        resp = await login_user(client, email="nobody@example.com")
        assert resp.status_code == 401
        # Same error message as wrong password — prevents user enumeration
        assert "invalid email or password" in resp.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session):
        """An inactive user should get the same generic error as wrong password."""
        await register_user(client)
        # Deactivate user directly in DB
        from app.models.user import User
        from sqlalchemy import select, update
        await db_session.execute(
            update(User).where(User.email == "test@example.com").values(is_active=False)
        )
        await db_session.commit()

        resp = await login_user(client)
        assert resp.status_code == 401
        # Same generic error — no "account deactivated" leak
        assert "invalid email or password" in resp.json()["error"]["message"].lower()


# ---------------------------------------------------------------------------
# Refresh Tests
# ---------------------------------------------------------------------------

class TestRefresh:

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        tokens = await register_and_login(client)
        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        """An access token should be rejected by the refresh endpoint."""
        tokens = await register_and_login(client)
        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": tokens["access_token"],  # Wrong token type!
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token(self, client: AsyncClient):
        """An expired refresh token should be rejected."""
        from datetime import timedelta
        expired_token = create_refresh_token(
            subject="some-fake-id",
            expires_delta=timedelta(seconds=-1),
        )
        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": expired_token,
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_inactive_user(self, client: AsyncClient, db_session):
        """Refreshing should fail if the user has been deactivated."""
        tokens = await register_and_login(client)

        # Deactivate user
        from app.models.user import User
        from sqlalchemy import update
        await db_session.execute(
            update(User).where(User.email == "test@example.com").values(is_active=False)
        )
        await db_session.commit()

        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Me Endpoint Tests
# ---------------------------------------------------------------------------

class TestMe:

    @pytest.mark.asyncio
    async def test_me_success(self, client: AsyncClient):
        tokens = await register_and_login(client)
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert resp.status_code == 200

        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_expired_token(self, client: AsyncClient):
        from datetime import timedelta
        expired_token = create_access_token(
            subject="some-id",
            expires_delta=timedelta(seconds=-1),
        )
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {expired_token}",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_refresh_token_fails(self, client: AsyncClient):
        """A refresh token should not work as a Bearer token."""
        tokens = await register_and_login(client)
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {tokens['refresh_token']}",
        })
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Guest Login Tests
# ---------------------------------------------------------------------------

class TestGuestLogin:

    @pytest.mark.asyncio
    async def test_guest_login_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/guest")
        assert resp.status_code == 201

        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# Logout Tests
# ---------------------------------------------------------------------------

class TestLogout:

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        tokens = await register_and_login(client)
        resp = await client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 401
