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

        # Semantic Deduplication (Threshold 0.88 similarity -> distance < 0.12)
        if embedding is not None:
            existing = await self.question_repo.find_similar_question(embedding, threshold=0.88)
            if existing:
                logger.info(f"Duplicate question detected via vector similarity (matched ID: {existing.id}). Enriching rather than duplicating.")
                if question_data.company and not existing.company:
                    existing.company = question_data.company
                return existing

        return await self.question_repo.create_question(
            domain=question_data.domain,
            topic=question_data.topic,
            difficulty=question_data.difficulty,
            company=question_data.company,
            question_text=question_data.question_text,
            expected_key_points=question_data.expected_key_points,
            embedding=embedding,
            status="accepted"
        )

    async def _fetch_url_content(self, url: str) -> str:
        """
        Resilient fetcher:
        1. Attempts direct fetch with standard browser headers.
        2. If anti-bot/JS/SPA blocks, falls back to open Reader proxy (r.jina.ai).
        """
        import httpx
        from app.utils.text_extraction import strip_html

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # 1. Direct fetch
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    cleaned = strip_html(resp.text)
                    if len(cleaned.strip()) > 250:
                        return cleaned[:12000]
        except Exception as e:
            logger.warning(f"Direct fetch failed or timed out for {url}: {e}. Retrying via Reader proxy...")

        # 2. Resilient Reader proxy fallback (executes JS & handles client-side rendering)
        reader_url = f"https://r.jina.ai/{url}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                resp = await client.get(reader_url, headers={"X-Target-Selector": "body"})
                if resp.status_code == 200 and len(resp.text.strip()) > 100:
                    return resp.text[:12000]
        except Exception as e:
            logger.error(f"Reader fallback also failed for {url}: {e}")

        raise ValueError(f"Unable to extract readable text from {url} (page may require login or blocked requests).")

    async def ingest_url(self, url: str, domain: str, topic: str, company: Optional[str] = None) -> List[QuestionBank]:
        """
        Fetches a URL, extracts text, and generates question bank entries using AI.
        """
        from app.services.ai.service import AIService
        
        try:
            text_content = await self._fetch_url_content(url)
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
                company=company,
                question_text=gq.question_text,
                expected_key_points="\n".join(gq.ideal_answer_hints),
                knowledge_source_id=source.id
            ))
            questions.append(q)
            
        return questions
