"""
AI Service Orchestrator.

Orchestrates the configured AI providers, managing retries and fallback logic.
This service is completely unaware of the database and only returns domain Pydantic models.
"""
import logging
from typing import Optional

from app.config import get_settings
from app.exceptions import AIServiceError
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.services.ai.base import BaseAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.huggingface_provider import HuggingFaceProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class AIService:
    """
    Business logic layer for AI integration.
    Handles the primary and fallback provider routing.
    """

    def __init__(self):
        self.primary_name = settings.AI_PRIMARY_PROVIDER
        self.fallback_name = settings.AI_FALLBACK_PROVIDER
        
        self.providers: dict[str, Optional[BaseAIProvider]] = {
            "gemini": None,
            "huggingface": None,
        }
        
        # Lazy initialization
        self._init_provider(self.primary_name)
        if self.fallback_name:
            self._init_provider(self.fallback_name)

    def _init_provider(self, name: str) -> None:
        try:
            if name == "gemini":
                self.providers["gemini"] = GeminiProvider()
            elif name == "huggingface":
                self.providers["huggingface"] = HuggingFaceProvider()
        except ValueError as e:
            logger.warning(f"Failed to initialize AI provider '{name}': {str(e)}")

    def _get_provider(self, name: str) -> BaseAIProvider:
        provider = self.providers.get(name)
        if not provider:
            raise AIServiceError(f"Provider '{name}' is not properly configured")
        return provider

    async def _execute_with_fallback(self, method_name: str, *args, **kwargs):
        """
        Executes an AI method with configured retries and fallback.
        Only falls back on AIServiceError (which represents transient/provider errors).
        """
        primary = self._get_provider(self.primary_name)
        
        # Try Primary
        for attempt in range(settings.GEMINI_MAX_RETRIES + 1):
            try:
                method = getattr(primary, method_name)
                return await method(*args, **kwargs)
            except AIServiceError as e:
                logger.warning(
                    f"AI Provider '{self.primary_name}' failed on attempt {attempt + 1}. Error: {str(e)}"
                )
                if attempt == settings.GEMINI_MAX_RETRIES:
                    break # Exhausted retries
            except Exception as e:
                # Programming/deterministic errors -> don't retry, let it crash
                logger.error(f"Unexpected error in '{self.primary_name}': {str(e)}")
                raise AIServiceError(f"Unexpected failure in {self.primary_name}") from e

        # Primary failed entirely. Try Fallback.
        if self.fallback_name and self.fallback_name != self.primary_name:
            try:
                fallback = self._get_provider(self.fallback_name)
                logger.info(f"Attempting fallback to '{self.fallback_name}'")
                
                for attempt in range(settings.HF_MAX_RETRIES + 1):
                    try:
                        method = getattr(fallback, method_name)
                        return await method(*args, **kwargs)
                    except AIServiceError as e:
                        logger.warning(
                            f"Fallback Provider '{self.fallback_name}' failed on attempt {attempt + 1}. Error: {str(e)}"
                        )
                    except Exception as e:
                        logger.error(f"Unexpected error in '{self.fallback_name}': {str(e)}")
                        raise AIServiceError(f"Unexpected failure in {self.fallback_name}") from e
                        
            except AIServiceError as e:
                # Initialization error or configuration error for fallback
                pass
                
        # Both failed
        raise AIServiceError("All AI providers failed to satisfy the request")


    async def generate_questions(
        self,
        interview_type: str,
        difficulty: str,
        num_questions: int,
        company: str | None,
    ) -> list[GeneratedQuestion]:
        return await self._execute_with_fallback(
            "generate_questions", interview_type, difficulty, num_questions, company
        )

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        return await self._execute_with_fallback(
            "evaluate_answer", question_text, user_answer, interview_type, difficulty
        )

    async def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        return await self._execute_with_fallback(
            "generate_response", prompt, system_instruction=system_instruction
        )
