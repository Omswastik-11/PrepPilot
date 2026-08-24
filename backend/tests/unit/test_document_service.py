import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.document_service import DocumentService, ResumeExtraction
from app.models.document import Document

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def document_service(mock_session):
    with patch("app.services.document_service.DocumentRepository") as mock_repo, \
         patch("app.services.document_service.CandidateService") as mock_cand_service, \
         patch("app.services.document_service.GeminiProvider") as mock_gemini:
        
        service = DocumentService(MagicMock())
        service.doc_repo = mock_repo.return_value
        service.candidate_service = mock_cand_service.return_value
        service.doc_repo.create = AsyncMock()
        service.doc_repo.update = AsyncMock()
        service.candidate_service.update_profile = AsyncMock()
        service.candidate_service.upsert_memory = AsyncMock()
        yield service

@pytest.mark.asyncio
async def test_ingest_document_success(document_service):
    user_id = uuid4()
    doc_id = uuid4()
    raw_text = "I am a software engineer."
    
    mock_doc = Document(id=doc_id, user_id=user_id, status="pending")
    document_service.doc_repo.create.return_value = mock_doc
    
    # Mock AIService response
    mock_ai_json = '{"skills": ["Python"], "experience_years": 5, "target_roles": ["Backend Engineer"], "memories": [{"memory_type": "experience", "content": "Built API"}]}'
    
    with patch("app.services.ai.service.AIService.generate_response", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_ai_json
        
        await document_service.ingest_document(
            user_id=user_id,
            filename="resume.pdf",
            file_type="pdf",
            raw_text=raw_text
        )
        
    document_service.doc_repo.create.assert_called_once()
    document_service.candidate_service.update_profile.assert_called_once()
    document_service.candidate_service.upsert_memory.assert_called_once()
    document_service.doc_repo.update.assert_any_call(doc_id, parsed_json=mock_ai_json)

@pytest.mark.asyncio
async def test_ingest_document_failure(document_service):
    user_id = uuid4()
    doc_id = uuid4()
    
    mock_doc = Document(id=doc_id, user_id=user_id, status="pending")
    document_service.doc_repo.create.return_value = mock_doc
    
    with patch("app.services.ai.service.AIService.generate_response", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = Exception("AI Failed")
        
        await document_service.ingest_document(
            user_id=user_id,
            filename="resume.pdf",
            file_type="pdf",
            raw_text="text"
        )
        
    document_service.doc_repo.update.assert_called_with(doc_id, status="failed", error_message="AI Failed")
    document_service.candidate_service.update_profile.assert_not_called()
