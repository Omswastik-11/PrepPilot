import pytest
from httpx import AsyncClient

from tests.api.test_auth import register_and_login

@pytest.mark.asyncio
async def test_knowledge_ingest_auth(client: AsyncClient):
    # 1. Without token -> 401
    resp = await client.post("/api/knowledge/ingest", json={"url": "https://example.com", "domain": "Tech", "topic": "General"})
    assert resp.status_code == 401

    # 2. With normal user token -> 403
    tokens = await register_and_login(client, email="normaluser@example.com")
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    resp_user = await client.post("/api/knowledge/ingest", json={"url": "https://example.com", "domain": "Tech", "topic": "General"})
    assert resp_user.status_code == 403
