"""
Embedding service for generating text embeddings using Google Gemini.
"""

from google import genai
from google.genai import types
import logging
from typing import List

from app.config import get_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Thin wrapper around the Gemini embedding API."""

    def __init__(self):
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text string."""
        if not text or not text.strip():
            logger.warning("Attempted to embed empty text, returning zero vector.")
            return [0.0] * self.dimension
            
        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension
                ),
            )
            if not response.embeddings or not response.embeddings[0].values:
                raise ValueError("Embedding generation returned empty result")
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text strings."""
        if not texts:
            return []
            
        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension
                ),
            )
            if not response.embeddings or len(response.embeddings) != len(texts):
                raise ValueError("Embedding batch generation returned mismatched results")
            return [e.values for e in response.embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise
