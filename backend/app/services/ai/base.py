"""
Base AI Provider Interface.

Defines the contract that all AI providers (Gemini, HuggingFace, etc.) must implement.
The core AIService orchestrates these providers.
"""

from abc import ABC, abstractmethod

from app.schemas.ai import GeneratedQuestion, EvaluationResult


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.
    All providers must implement these methods and return the domain Pydantic models.
    """

    @abstractmethod
    async def generate_questions(
        self,
        interview_type: str,
        difficulty: str,
        num_questions: int,
        company: str | None,
    ) -> list[GeneratedQuestion]:
        """Generate interview questions."""
        pass

    @abstractmethod
    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        """Evaluate a user's answer."""
        pass

    @abstractmethod
    async def generate_response(
        self, prompt: str, system_instruction: str = None
    ) -> str:
        """Fallback method for unstructured text generation."""
        pass
