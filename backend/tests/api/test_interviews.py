"""
API tests for Interview endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4

from app.main import app
from app.dependencies import get_ai_service
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.exceptions import AIServiceError

from tests.api.test_auth import register_and_login


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """Returns a client authenticated as a standard user."""
    tokens = await register_and_login(client, email="testuser@example.com")
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client


@pytest_asyncio.fixture
async def auth_client_2(client: AsyncClient):
    """Returns a client authenticated as a second standard user (for testing ownership)."""
    tokens = await register_and_login(client, email="testuser2@example.com")
    # We must create a new client or clone headers if we want to run them side-by-side, 
    # but for sequential requests we can just return the tokens.
    return tokens["access_token"]


@pytest_asyncio.fixture
def mock_ai_service():
    """Provides a mocked AIService to avoid real API calls."""
    mock_service = AsyncMock()
    
    # Default success responses
    mock_service.generate_questions.return_value = [
        GeneratedQuestion(question_text="Q1", time_limit_seconds=120, ideal_answer_hints=["H1"]),
        GeneratedQuestion(question_text="Q2", time_limit_seconds=120, ideal_answer_hints=["H2"]),
        GeneratedQuestion(question_text="Q3", time_limit_seconds=120, ideal_answer_hints=["H3"]),
    ]
    
    mock_service.evaluate_answer.return_value = EvaluationResult(
        score=8.5,
        feedback="Good job",
        strengths=["Clear"],
        weaknesses=["Too short"],
        ideal_answer="A perfect answer"
    )
    
    # Apply override
    app.dependency_overrides[get_ai_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_ai_service, None)


class TestInterviews:
    
    @pytest.mark.asyncio
    async def test_create_interview(self, auth_client: AsyncClient, mock_ai_service):
        resp = await auth_client.post("/api/interviews", json={
            "interview_type": "technical",
            "difficulty": "medium",
            "num_questions": 3
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["interview_type"] == "technical"
        assert data["num_questions"] == 3
        assert data["status"] == "in_progress"
        assert len(data["questions"]) == 1
        
        mock_ai_service.generate_questions.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_interview_ai_failure_transaction(self, auth_client: AsyncClient, mock_ai_service):
        """If AI fails, NO interview or questions should be persisted."""
        mock_ai_service.generate_questions.side_effect = AIServiceError("AI failed entirely")
        
        resp = await auth_client.post("/api/interviews", json={
            "interview_type": "technical",
            "difficulty": "medium",
            "num_questions": 3
        })
        
        # 502 Bad Gateway mapping
        assert resp.status_code == 502
        
        # Verify DB is clean
        list_resp = await auth_client.get("/api/interviews")
        assert list_resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_get_interview_ownership(self, auth_client: AsyncClient, auth_client_2: str, mock_ai_service):
        # User 1 creates interview
        create_resp = await auth_client.post("/api/interviews", json={
            "interview_type": "technical",
            "difficulty": "easy",
            "num_questions": 3
        })
        interview_id = create_resp.json()["id"]
        
        # User 1 gets it successfully
        get_resp = await auth_client.get(f"/api/interviews/{interview_id}")
        assert get_resp.status_code == 200
        
        # User 2 tries to get it
        auth_client.headers["Authorization"] = f"Bearer {auth_client_2}"
        fail_resp = await auth_client.get(f"/api/interviews/{interview_id}")
        assert fail_resp.status_code == 403  # Forbidden / Authorization Error
        
    @pytest.mark.asyncio
    async def test_list_interviews_pagination(self, auth_client: AsyncClient, mock_ai_service):
        # Create 2 interviews
        await auth_client.post("/api/interviews", json={"interview_type": "technical", "difficulty": "easy", "num_questions": 3})
        await auth_client.post("/api/interviews", json={"interview_type": "behavioral", "difficulty": "easy", "num_questions": 3})
        
        resp = await auth_client.get("/api/interviews?limit=1&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1
        
        resp2 = await auth_client.get("/api/interviews?limit=1&offset=1")
        assert len(resp2.json()["items"]) == 1
        assert resp.json()["items"][0]["id"] != resp2.json()["items"][0]["id"]

    @pytest.mark.asyncio
    async def test_submit_answer_and_complete(self, auth_client: AsyncClient, mock_ai_service):
        # 1. Create interview
        create_resp = await auth_client.post("/api/interviews", json={
            "interview_type": "behavioral",
            "difficulty": "medium",
            "num_questions": 3
        })
        data = create_resp.json()
        interview_id = data["id"]
        q1_id = data["questions"][0]["id"]
        
        # 2. Try to complete prematurely
        fail_complete = await auth_client.post(f"/api/interviews/{interview_id}/complete")
        assert fail_complete.status_code == 409  # InvalidStateError
        assert "Not all questions are answered" in fail_complete.json()["error"]["message"]
        
        # 3. Submit answer to Q1
        ans1_resp = await auth_client.post(f"/api/interviews/{interview_id}/questions/{q1_id}/answer", json={
            "user_answer": "My answer 1",
            "time_taken_seconds": 60
        })
        assert ans1_resp.status_code == 200
        assert ans1_resp.json()["score"] == 8.5
        
        # 4. Fetch interview to get Q2
        get_resp = await auth_client.get(f"/api/interviews/{interview_id}")
        q2_id = get_resp.json()["questions"][1]["id"]
        
        # 5. Submit Q2
        await auth_client.post(f"/api/interviews/{interview_id}/questions/{q2_id}/answer", json={"user_answer": "A2", "time_taken_seconds": 30})
        
        # 6. Fetch interview to get Q3
        get_resp = await auth_client.get(f"/api/interviews/{interview_id}")
        q3_id = get_resp.json()["questions"][2]["id"]
        
        # 7. Submit Q3
        await auth_client.post(f"/api/interviews/{interview_id}/questions/{q3_id}/answer", json={"user_answer": "A3", "time_taken_seconds": 30})
        
        # 6. Complete interview
        complete_resp = await auth_client.post(f"/api/interviews/{interview_id}/complete")
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"
        assert complete_resp.json()["total_score"] == 8.5

    @pytest.mark.asyncio
    async def test_abandon_interview(self, auth_client: AsyncClient, mock_ai_service):
        create_resp = await auth_client.post("/api/interviews", json={
            "interview_type": "technical",
            "difficulty": "medium",
            "num_questions": 3
        })
        interview_id = create_resp.json()["id"]
        
        abandon_resp = await auth_client.post(f"/api/interviews/{interview_id}/abandon")
        assert abandon_resp.status_code == 200
        assert abandon_resp.json()["status"] == "abandoned"
        
        # Cannot submit answer to abandoned interview
        q1_id = create_resp.json()["questions"][0]["id"]
        fail_ans = await auth_client.post(f"/api/interviews/{interview_id}/questions/{q1_id}/answer", json={
            "user_answer": "My answer 1",
            "time_taken_seconds": 60
        })
        assert fail_ans.status_code == 409

    @pytest.mark.asyncio
    async def test_submit_answer_ai_planning_failure(self, auth_client: AsyncClient, mock_ai_service, db_session):
        # 1. Create interview
        create_resp = await auth_client.post("/api/interviews", json={
            "interview_type": "behavioral",
            "difficulty": "medium",
            "num_questions": 3
        })
        data = create_resp.json()
        interview_id = data["id"]
        q1_id = data["questions"][0]["id"]
        
        # 2. Mock AI to fail ONLY on planning next question
        # evaluate_answer succeeds, generate_questions (for next Q) fails
        mock_ai_service.generate_questions.side_effect = AIServiceError("Planning failed")
        
        # 3. Submit answer to Q1
        ans1_resp = await auth_client.post(f"/api/interviews/{interview_id}/questions/{q1_id}/answer", json={
            "user_answer": "My answer 1",
            "time_taken_seconds": 60
        })
        
        # Should return 502 Bad Gateway due to AI error
        assert ans1_resp.status_code == 502
        
        # 4. Verify DB transaction rolled back (no Answer saved for Q1)
        # We need a fresh get of the interview to check Q1 state
        get_resp = await auth_client.get(f"/api/interviews/{interview_id}")
        assert get_resp.status_code == 200
        q1_data = get_resp.json()["questions"][0]
        assert "answer" not in q1_data or q1_data["answer"] is None
