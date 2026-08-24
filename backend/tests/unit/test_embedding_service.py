import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai.embedding_service import EmbeddingService
from google.genai import types

# Test data
DUMMY_TEXT = "This is a test string."
DUMMY_BATCH = ["First string.", "Second string."]
DUMMY_EMBEDDING = [0.1] * 768

@pytest.fixture
def mock_genai_client():
    with patch("app.services.ai.embedding_service.genai.Client") as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.aio.models.embed_content = AsyncMock()
        yield mock_instance

@pytest.fixture
def embedding_service(mock_genai_client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "768")
    
    # Reload settings to pick up mocked env vars
    from app.config import get_settings
    get_settings.cache_clear()
    
    return EmbeddingService()

@pytest.mark.asyncio
async def test_embed_text_success(embedding_service, mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = DUMMY_EMBEDDING
    mock_response.embeddings = [mock_embedding]
    mock_genai_client.aio.models.embed_content.return_value = mock_response

    result = await embedding_service.embed_text(DUMMY_TEXT)

    assert result == DUMMY_EMBEDDING
    # Extract the args
    args, kwargs = mock_genai_client.aio.models.embed_content.call_args
    assert kwargs["model"] == embedding_service.model
    assert kwargs["contents"] == DUMMY_TEXT
    assert kwargs["config"].output_dimensionality == 768

@pytest.mark.asyncio
async def test_embed_text_empty(embedding_service, mock_genai_client):
    result = await embedding_service.embed_text("")
    
    assert len(result) == 768
    assert all(v == 0.0 for v in result)
    mock_genai_client.aio.models.embed_content.assert_not_called()

@pytest.mark.asyncio
async def test_embed_text_api_failure(embedding_service, mock_genai_client):
    mock_genai_client.aio.models.embed_content.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await embedding_service.embed_text(DUMMY_TEXT)

@pytest.mark.asyncio
async def test_embed_batch_success(embedding_service, mock_genai_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_emb1 = MagicMock()
    mock_emb1.values = [0.1] * 768
    mock_emb2 = MagicMock()
    mock_emb2.values = [0.2] * 768
    mock_response.embeddings = [mock_emb1, mock_emb2]
    mock_genai_client.aio.models.embed_content.return_value = mock_response

    result = await embedding_service.embed_batch(DUMMY_BATCH)

    assert len(result) == 2
    assert result[0] == [0.1] * 768
    assert result[1] == [0.2] * 768
    args, kwargs = mock_genai_client.aio.models.embed_content.call_args
    assert kwargs["model"] == embedding_service.model
    assert kwargs["contents"] == DUMMY_BATCH
    assert kwargs["config"].output_dimensionality == 768

@pytest.mark.asyncio
async def test_embed_batch_empty_list(embedding_service, mock_genai_client):
    result = await embedding_service.embed_batch([])
    
    assert result == []
    mock_genai_client.aio.models.embed_content.assert_not_called()
