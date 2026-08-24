from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import logging
from uuid import UUID

from app.models.knowledge import QuestionBank, KnowledgeSource
from app.models.candidate import CandidateMemory
from app.services.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = EmbeddingService()

    async def retrieve_questions(
        self, 
        query: str, 
        domain: Optional[str] = None, 
        difficulty: Optional[str] = None,
        limit: int = 5
    ) -> List[QuestionBank]:
        """
        Hybrid retrieval: Structured SQL filters + pgvector similarity.
        """
        try:
            query_embedding = await self.embedding_service.embed_text(query)
        except Exception as e:
            logger.error(f"Failed to embed query for retrieval: {e}")
            return []

        sql_query = select(QuestionBank).where(QuestionBank.status == 'accepted')
        
        if domain:
            sql_query = sql_query.where(QuestionBank.domain == domain)
        if difficulty:
            sql_query = sql_query.where(QuestionBank.difficulty == difficulty)

        # Order by vector distance (L2 distance <->)
        # SQLAlchemy pgvector syntax: Model.embedding.l2_distance(vector)
        sql_query = sql_query.order_by(
            QuestionBank.embedding.l2_distance(query_embedding)
        ).limit(limit)
        
        result = await self.session.execute(sql_query)
        return list(result.scalars().all())

    async def retrieve_memories(
        self,
        user_id: UUID,
        query: str,
        limit: int = 3
    ) -> List[CandidateMemory]:
        """
        Retrieve relevant candidate memories for context.
        """
        try:
            query_embedding = await self.embedding_service.embed_text(query)
        except Exception as e:
            logger.error(f"Failed to embed query for memory retrieval: {e}")
            return []

        sql_query = (
            select(CandidateMemory)
            .where(CandidateMemory.user_id == user_id)
            .order_by(CandidateMemory.embedding.l2_distance(query_embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(sql_query)
        return list(result.scalars().all())
