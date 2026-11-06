from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
from uuid import UUID

from app.schemas.knowledge import KnowledgeSourceCreate, QuestionBankCreate
from app.models.knowledge import KnowledgeSource, QuestionBank
from app.repositories.knowledge_repository import KnowledgeRepository, QuestionBankRepository
from app.services.ai.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.knowledge_repo = KnowledgeRepository(session)
        self.question_repo = QuestionBankRepository(session)
        self.embedding_service = EmbeddingService()

    async def add_source(self, source_data: KnowledgeSourceCreate) -> KnowledgeSource:
        try:
            embedding = await self.embedding_service.embed_text(source_data.content)
        except Exception as e:
            logger.warning(f"Failed to generate embedding for source: {e}")
            embedding = None

        return await self.knowledge_repo.create_source(
            source_type=source_data.source_type,
            reference=source_data.reference,
            content=source_data.content,
            embedding=embedding
        )

    async def add_question(self, question_data: QuestionBankCreate) -> QuestionBank:
        embed_text = f"{question_data.domain} {question_data.topic} {question_data.question_text}"
        if question_data.expected_key_points:
            embed_text += f" {question_data.expected_key_points}"
            
        try:
            embedding = await self.embedding_service.embed_text(embed_text)
        except Exception as e:
            logger.warning(f"Failed to generate embedding for question: {e}")
            embedding = None

        return await self.question_repo.create_question(
            domain=question_data.domain,
            topic=question_data.topic,
            difficulty=question_data.difficulty,
            question_text=question_data.question_text,
            expected_key_points=question_data.expected_key_points,
            embedding=embedding,
            status="accepted"
        )

    async def ingest_url(self, url: str, domain: str, topic: str, company: Optional[str] = None) -> List[QuestionBank]:
        """
        Fetches a URL, extracts text, and generates question bank entries using AI.
        """
        import httpx
        from app.services.ai.service import AIService
        from app.utils.text_extraction import strip_html
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                text_content = strip_html(resp.text)[:10000] # simple truncation for MVP
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise ValueError(f"Could not fetch URL: {e}")
            
        # Create knowledge source
        source = await self.add_source(KnowledgeSourceCreate(
            source_type="url",
            reference=url,
            content=text_content
        ))
        
        # Generate questions
        ai_service = AIService()
        
        try:
            generated = await ai_service.generate_questions_from_context(
                context=text_content,
                domain=domain,
                topic=topic,
                company=company,
                num_questions=3
            )
        except Exception as e:
            logger.error(f"AI failed to generate questions from URL: {e}")
            return []
            
        questions = []
        for gq in generated:
            q = await self.add_question(QuestionBankCreate(
                domain=domain,
                topic=topic,
                difficulty="Mid",
                question_text=gq.question_text,
                expected_key_points="\n".join(gq.ideal_answer_hints),
                knowledge_source_id=source.id
            ))
            questions.append(q)
            
        return questions
