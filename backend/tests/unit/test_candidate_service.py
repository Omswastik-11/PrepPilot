import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.candidate_service import CandidateService
from app.schemas.candidate import CandidateProfileCreate, CandidateProfileUpdate
from app.models.candidate import CandidateProfile, CandidateMemory

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.candidate_service.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_text = AsyncMock(return_value=[0.1] * 768)
        yield instance

@pytest.fixture
def candidate_service(mock_session, mock_embedding_service, monkeypatch):
    with patch("app.services.candidate_service.CandidateProfileRepository") as mock_profile_repo, \
         patch("app.services.candidate_service.CandidateMemoryRepository") as mock_memory_repo:
        
        service = CandidateService(mock_session)
        service.profile_repo = mock_profile_repo.return_value
        service.memory_repo = mock_memory_repo.return_value
        service.memory_repo.upsert = AsyncMock()
        service.memory_repo.get_by_id = AsyncMock()
        service.memory_repo.delete = AsyncMock()
        service.memory_repo.find_similar_memory = AsyncMock()
        service.memory_repo.create = AsyncMock()
        service.memory_repo.update = AsyncMock()
        yield service

@pytest.mark.asyncio
async def test_upsert_memory_new(candidate_service, mock_embedding_service):
    user_id = uuid4()
    candidate_service.memory_repo.find_similar_memory.return_value = None
    
    mock_memory = CandidateMemory(id=uuid4(), user_id=user_id, memory_type="strength", content="Python")
    candidate_service.memory_repo.create.return_value = mock_memory

    result = await candidate_service.upsert_memory(
        user_id=user_id,
        memory_type="strength",
        content="Python",
        source="interview_answer"
    )

    assert result == mock_memory
    candidate_service.memory_repo.create.assert_called_once()
    mock_embedding_service.embed_text.assert_called_once_with("Python")

@pytest.mark.asyncio
async def test_upsert_memory_existing(candidate_service, mock_embedding_service):
    user_id = uuid4()
    existing_memory = CandidateMemory(id=uuid4(), user_id=user_id, confidence=0.5, interview_id=uuid4())
    candidate_service.memory_repo.find_similar_memory.return_value = existing_memory
    
    mock_updated = CandidateMemory(id=existing_memory.id, confidence=0.6)
    candidate_service.memory_repo.update.return_value = mock_updated

    result = await candidate_service.upsert_memory(
        user_id=user_id,
        memory_type="strength",
        content="Python",
        source="interview_answer"
    )

    assert result == mock_updated
    candidate_service.memory_repo.update.assert_called_once()
    # Shouldn't create a new one
    candidate_service.memory_repo.create.assert_not_called()
    # Should embed because we embed before deduplication now
    mock_embedding_service.embed_text.assert_called_once_with("Python")
