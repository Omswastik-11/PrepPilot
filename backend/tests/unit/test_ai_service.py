"""
Unit Tests for AI Service.

Tests the orchestration, fallback logic, and error handling of AIService.
We mock the actual providers to avoid making network calls during unit testing.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.exceptions import AIServiceError
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.services.ai.service import AIService


@pytest.fixture
def mock_gemini():
    provider = AsyncMock()
    return provider


@pytest.fixture
def mock_fallback():
    provider = AsyncMock()
    return provider


@pytest.fixture
def ai_service(mock_gemini, mock_fallback):
    # We patch AIService's internal provider dictionary
    service = AIService()
    service.fallback_name = "groq"
    service.providers = {
        "gemini": mock_gemini,
        "groq": mock_fallback,
    }
    return service


@pytest.mark.asyncio
async def test_generate_questions_success(ai_service, mock_gemini, mock_fallback):
    """Test successful generation using primary provider (Gemini)."""
    mock_gemini.generate_questions.return_value = [
        GeneratedQuestion(
            question_text="What is a binary tree?",
            time_limit_seconds=120,
            ideal_answer_hints=["Nodes", "Left and Right children"]
        )
    ]
    
    result = await ai_service.generate_questions("technical", "easy", 1, None)
    
    assert len(result) == 1
    assert result[0].question_text == "What is a binary tree?"
    mock_gemini.generate_questions.assert_called_once()
    # Fallback should not be called if Gemini succeeds
    mock_fallback.generate_questions.assert_not_called()


@pytest.mark.asyncio
async def test_generate_questions_fallback(ai_service, mock_gemini, mock_fallback):
    """Test fallback to Groq when Gemini fails with AIServiceError."""
    # Setup Gemini to fail with AIServiceError
    mock_gemini.generate_questions.side_effect = AIServiceError("Gemini timed out")
    
    # Setup Fallback to succeed
    mock_fallback.generate_questions.return_value = [
        GeneratedQuestion(
            question_text="What is a hash map?",
            time_limit_seconds=120,
            ideal_answer_hints=["Key-value pairs", "O(1) lookup"]
        )
    ]
    
    result = await ai_service.generate_questions("technical", "easy", 1, None)
    
    assert len(result) == 1
    assert result[0].question_text == "What is a hash map?"
    
    # Gemini should have been called (and retried based on settings, default MAX_RETRIES=1)
    assert mock_gemini.generate_questions.call_count == 2  # 1 initial + 1 retry
    mock_fallback.generate_questions.assert_called_once()


@pytest.mark.asyncio
async def test_generate_questions_both_fail(ai_service, mock_gemini, mock_fallback):
    """Test when both providers fail, an AIServiceError is raised."""
    mock_gemini.generate_questions.side_effect = AIServiceError("Gemini failed")
    mock_fallback.generate_questions.side_effect = AIServiceError("Groq failed")
    
    with pytest.raises(AIServiceError) as exc_info:
        await ai_service.generate_questions("technical", "easy", 1, None)
        
    assert "All AI providers failed" in str(exc_info.value)
    assert mock_gemini.generate_questions.call_count == 2
    assert mock_fallback.generate_questions.call_count == 2


@pytest.mark.asyncio
async def test_evaluate_answer_programming_error_no_fallback(ai_service, mock_gemini, mock_fallback):
    """Test that unexpected programming errors (not AIServiceError) do not trigger fallback."""
    # Raise a generic exception, not AIServiceError
    mock_gemini.evaluate_answer.side_effect = ValueError("Malformed internal state")
    
    with pytest.raises(AIServiceError) as exc_info:
        await ai_service.evaluate_answer("Q?", "A!", "technical", "easy")
        
    assert "Unexpected failure in gemini" in str(exc_info.value)
    
    # Gemini should only be called once (no retries for unexpected errors)
    mock_gemini.evaluate_answer.assert_called_once()
    # Fallback should never be called
    mock_fallback.evaluate_answer.assert_not_called()
