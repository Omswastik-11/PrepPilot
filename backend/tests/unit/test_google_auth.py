"""
Unit Tests for Google OAuth Routes.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, MagicMock

from app.config import get_settings
from app.main import app


@pytest.mark.asyncio
async def test_google_login_redirect_success():
    """Verify Google login redirects to Google OAuth URL when configured."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/google/login", follow_redirects=False)
        assert response.status_code == 307
        location = response.headers.get("location")
        assert location is not None
        assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
        assert "client_id=" in location
        assert "response_type=code" in location


@pytest.mark.asyncio
async def test_google_login_redirect_not_configured():
    """Verify friendly redirect back to login page if credentials are missing."""
    with patch("app.routes.auth.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.GOOGLE_CLIENT_ID = None
        mock_settings.GOOGLE_CLIENT_SECRET = None
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        mock_get_settings.return_value = mock_settings

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/auth/google/login", follow_redirects=False)
            assert response.status_code == 307
            location = response.headers.get("location")
            assert location.startswith("http://localhost:3000/login?error=")


@pytest.mark.asyncio
async def test_google_callback_with_error():
    """Verify handling of OAuth cancel/denied from Google."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/google/callback?error=access_denied", follow_redirects=False)
        assert response.status_code == 307
        location = response.headers.get("location")
        assert "error=" in location
        assert "access_denied" in location
