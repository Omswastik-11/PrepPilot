from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.knowledge import KnowledgeSourceCreate, KnowledgeSourceResponse, QuestionBankCreate, QuestionBankResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)

# We use a router-level dependency for the auth, or add it to each endpoint.
# Adding it to each endpoint is simpler and explicitly requested by user.

@router.post("/sources", response_model=KnowledgeSourceResponse)
async def create_source(
    source_data: KnowledgeSourceCreate,
    current_user: User = Depends(require_role("admin")),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return await service.add_source(source_data)

@router.post("/questions", response_model=QuestionBankResponse)
async def create_question(
    question_data: QuestionBankCreate,
    current_user: User = Depends(require_role("admin")),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    return await service.add_question(question_data)

class URLIngestRequest(BaseModel):
    url: str
    domain: str
    topic: str
    company: str | None = None

@router.post("/ingest", response_model=List[QuestionBankResponse])
async def ingest_url(
    req: URLIngestRequest,
    current_user: User = Depends(require_role("admin")),
    service: KnowledgeService = Depends(get_knowledge_service)
):
    try:
        return await service.ingest_url(req.url, req.domain, req.topic, req.company)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
