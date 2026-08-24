import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.candidate import CandidateProfileCreate, CandidateMemoryCreate
from app.models.candidate import CandidateProfile, CandidateMemory

client = TestClient(app)

def test_create_profile_success():
    user_id = uuid4()
    profile_data = {
        "skills": ["Python", "React"],
        "experience_years": 3
    }
    
    with patch("app.routes.candidate.CandidateService") as mock_service_class:
        mock_service = mock_service_class.return_value
        mock_service.create_profile = AsyncMock(return_value=CandidateProfile(
            id=uuid4(),
            user_id=user_id,
            skills=["Python", "React"],
            experience_years=3,
            created_at="2026-08-21T00:00:00Z",
            updated_at="2026-08-21T00:00:00Z"
        ))

        response = client.post(
            f"/api/candidate/profiles?user_id={str(user_id)}",
            json=profile_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == ["Python", "React"]
        assert data["experience_years"] == 3

def test_get_memories():
    user_id = uuid4()
    
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
                updated_at="2026-08-21T00:00:00Z"
            )
        ])

        response = client.get(f"/api/candidate/memories/{str(user_id)}?memory_type=strength")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["memory_type"] == "strength"
        assert data[0]["content"] == "System Design"
