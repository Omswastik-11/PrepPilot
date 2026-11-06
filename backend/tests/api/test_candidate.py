import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user
from app.models.user import User
from app.models.candidate import CandidateProfile, CandidateMemory

client = TestClient(app)

def test_candidate_routes_require_auth():
    # Unauthenticated requests must be rejected with 401
    response = client.get("/api/candidate/profiles/me")
    assert response.status_code == 401

    response = client.get(f"/api/candidate/memories")
    assert response.status_code == 401


def test_create_profile_success():
    user_id = uuid4()
    mock_user = User(
        id=user_id,
        email="candidate@example.com",
        role="user",
        is_active=True,
    )
    profile_data = {
        "skills": ["Python", "React"],
        "experience_years": 3,
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        with patch("app.routes.candidate.CandidateService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.create_profile = AsyncMock(return_value=CandidateProfile(
                id=uuid4(),
                user_id=user_id,
                skills=["Python", "React"],
                experience_years=3,
                created_at="2026-08-21T00:00:00Z",
                updated_at="2026-08-21T00:00:00Z",
            ))

            response = client.post("/api/candidate/profiles", json=profile_data)

            assert response.status_code == 201
            data = response.json()
            assert data["skills"] == ["Python", "React"]
            assert data["experience_years"] == 3
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_get_other_user_profile_forbidden():
    user_id = uuid4()
    other_user_id = uuid4()
    mock_user = User(
        id=user_id,
        email="candidate@example.com",
        role="user",
        is_active=True,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        response = client.get(f"/api/candidate/profiles/{str(other_user_id)}")
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_get_memories():
    user_id = uuid4()
    mock_user = User(
        id=user_id,
        email="candidate@example.com",
        role="user",
        is_active=True,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        with patch("app.routes.candidate.CandidateService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_memories = AsyncMock(return_value=[
                CandidateMemory(
                    id=uuid4(),
                    user_id=user_id,
                    memory_type="strength",
                    content="System Design",
                    source="interview_answer",
                    created_at="2026-08-21T00:00:00Z",
                    updated_at="2026-08-21T00:00:00Z",
                )
            ])

            response = client.get("/api/candidate/memories?memory_type=strength")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["memory_type"] == "strength"
            assert data[0]["content"] == "System Design"
    finally:
        app.dependency_overrides.pop(get_current_user, None)

