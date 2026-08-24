import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.retrieval_service import RetrievalService
from app.models.knowledge import QuestionBank
from app.models.candidate import CandidateMemory

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.retrieval_service.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_text = AsyncMock(return_value=[0.1] * 768)
        yield instance

@pytest.fixture
def retrieval_service(mock_session, mock_embedding_service):
    return RetrievalService(mock_session)

@pytest.mark.asyncio
async def test_retrieve_questions(retrieval_service, mock_session, mock_embedding_service):
    # Setup mock result
    mock_result = MagicMock()
    mock_questions = [QuestionBank(id=uuid4(), question_text="Q1"), QuestionBank(id=uuid4(), question_text="Q2")]
    mock_result.scalars.return_value.all.return_value = mock_questions
    mock_session.execute.return_value = mock_result

    result = await retrieval_service.retrieve_questions(
        query="Python basics",
        domain="Python",
        difficulty="Junior",
        limit=2
    )

    assert result == mock_questions
    mock_embedding_service.embed_text.assert_called_once_with("Python basics")
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_retrieve_memories(retrieval_service, mock_session, mock_embedding_service):
    user_id = uuid4()
    mock_result = MagicMock()
    mock_memories = [CandidateMemory(id=uuid4(), content="Knows Django")]
    mock_result.scalars.return_value.all.return_value = mock_memories
    mock_session.execute.return_value = mock_result

    result = await retrieval_service.retrieve_memories(
        user_id=user_id,
        query="web framework",
        limit=1
    )

    assert result == mock_memories
    mock_embedding_service.embed_text.assert_called_once_with("web framework")
    mock_session.execute.assert_called_once()
