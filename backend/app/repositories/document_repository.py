from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Optional, List
from uuid import UUID

from app.models.document import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> List[Document]:
        result = await self.session.execute(
            select(Document).where(Document.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Document:
        doc = Document(**kwargs)
        self.session.add(doc)
        return doc

    async def update(self, document_id: UUID, **kwargs) -> Optional[Document]:
        result = await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(**kwargs)
            .returning(Document)
        )
        return result.scalar_one_or_none()
