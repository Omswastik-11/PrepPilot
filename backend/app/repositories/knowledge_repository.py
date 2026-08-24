from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID

from app.models.knowledge import KnowledgeSource, QuestionBank

class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source(self, **kwargs) -> KnowledgeSource:
        reference = kwargs.get('reference')
        if reference:
            existing = await self.session.execute(
                select(KnowledgeSource).where(KnowledgeSource.reference == reference)
            )
            existing_source = existing.scalar_one_or_none()
            if existing_source:
                return existing_source

        source = KnowledgeSource(**kwargs)
        self.session.add(source)
        return source

    async def get_source(self, source_id: UUID) -> Optional[KnowledgeSource]:
        result = await self.session.execute(select(KnowledgeSource).where(KnowledgeSource.id == source_id))
        return result.scalar_one_or_none()

class QuestionBankRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question(self, **kwargs) -> QuestionBank:
        question = QuestionBank(**kwargs)
        self.session.add(question)
        return question

    async def get_question(self, question_id: UUID) -> Optional[QuestionBank]:
        result = await self.session.execute(select(QuestionBank).where(QuestionBank.id == question_id))
        return result.scalar_one_or_none()

    async def list_questions(self, domain: Optional[str] = None) -> List[QuestionBank]:
        query = select(QuestionBank)
        if domain:
            query = query.where(QuestionBank.domain == domain)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def accept_question(self, question_id: UUID) -> Optional[QuestionBank]:
        question = await self.get_question(question_id)
        if question:
            question.status = 'accepted'
            self.session.add(question)
        return question

    async def reject_question(self, question_id: UUID) -> Optional[QuestionBank]:
        question = await self.get_question(question_id)
        if question:
            question.status = 'rejected'
            self.session.add(question)
        return question
