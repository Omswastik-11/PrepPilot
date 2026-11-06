import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from app.services.knowledge_service import KnowledgeService
from app.models.knowledge import KnowledgeSource, QuestionBank

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.knowledge_service.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_text = AsyncMock(return_value=[0.5] * 768)
        yield instance

@pytest.fixture
def knowledge_service(mock_session, mock_embedding_service):
    with patch("app.services.knowledge_service.KnowledgeRepository") as mock_know_repo, \
         patch("app.services.knowledge_service.QuestionBankRepository") as mock_quest_repo:
        
        service = KnowledgeService(mock_session)
        service.knowledge_repo = mock_know_repo.return_value
        service.question_repo = mock_quest_repo.return_value
        service.knowledge_repo.create_source = AsyncMock()
        service.question_repo.create_question = AsyncMock()
        service.question_repo.find_similar_question = AsyncMock(return_value=None)
        yield service

@pytest.mark.asyncio
async def test_add_source(knowledge_service, mock_embedding_service):
    mock_source = KnowledgeSource(id=uuid4(), content="Python uses whitespace")
    knowledge_service.knowledge_repo.create_source.return_value = mock_source
    
    from app.schemas.knowledge import KnowledgeSourceCreate
    source_data = KnowledgeSourceCreate(
        source_type="document",
        reference="python_docs.pdf",
        content="Python uses whitespace"
    )
    
    result = await knowledge_service.add_source(source_data)
    
    assert result == mock_source
    mock_embedding_service.embed_text.assert_called_once_with("Python uses whitespace")
    knowledge_service.knowledge_repo.create_source.assert_called_once()

@pytest.mark.asyncio
async def test_add_question(knowledge_service, mock_embedding_service):
    mock_question = QuestionBank(id=uuid4(), question_text="What is PEP8?")
    knowledge_service.question_repo.create_question.return_value = mock_question
    
    from app.schemas.knowledge import QuestionBankCreate
    question_data = QuestionBankCreate(
        domain="Python",
        topic="Style Guide",
        difficulty="Junior",
        question_text="What is PEP8?",
        expected_key_points="Formatting guidelines"
    )
    
    result = await knowledge_service.add_question(question_data)
    
    assert result == mock_question
    mock_embedding_service.embed_text.assert_called_once_with(
        "Python Style Guide What is PEP8? Formatting guidelines"
    )
    knowledge_service.question_repo.create_question.assert_called_once()


@pytest.mark.asyncio
async def test_add_question_deduplication(knowledge_service, mock_embedding_service):
    """Test that existing similar questions return existing record without duplicate insertion."""
    existing_question = QuestionBank(id=uuid4(), question_text="What is PEP8?", company=None)
    knowledge_service.question_repo.find_similar_question.return_value = existing_question
    
    from app.schemas.knowledge import QuestionBankCreate
    question_data = QuestionBankCreate(
        domain="Python",
        topic="Style Guide",
        difficulty="Junior",
        company="Google",
        question_text="What is PEP8 formatting standard?",
        expected_key_points="Formatting guidelines"
    )
    
    result = await knowledge_service.add_question(question_data)
    
    assert result == existing_question
    assert result.company == "Google"
    knowledge_service.question_repo.create_question.assert_not_called()
    knowledge_service.question_repo.create_question.assert_called_once()
