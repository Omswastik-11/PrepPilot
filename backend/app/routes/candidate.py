from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.database import get_db
from app.dependencies import get_current_user, get_ai_service
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
    CandidateProfileResponse,
    CandidateMemoryCreate,
    CandidateMemoryResponse,
)
from app.schemas.document import DocumentResponse
from app.services.candidate_service import CandidateService
from app.services.document_service import DocumentService
from app.utils.text_extraction import extract_text

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])

def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    return CandidateService(db)

def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(db)

def _ensure_access(current_user: User, user_id: UUID) -> None:
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this candidate's data"
        )

@router.post("/profiles", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: CandidateProfileCreate,
    user_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service),
    db: AsyncSession = Depends(get_db)
):
    target_user_id = user_id or current_user.id
    _ensure_access(current_user, target_user_id)
    try:
        profile = await service.create_profile(target_user_id, profile_data)
        await db.commit()
        return profile
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/profiles/me", response_model=CandidateProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service)
):
    profile = await service.get_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

@router.get("/profiles/{user_id}", response_model=CandidateProfileResponse)
async def get_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service)
):
    _ensure_access(current_user, user_id)
    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

@router.patch("/profiles/me", response_model=CandidateProfileResponse)
async def update_my_profile(
    profile_data: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service),
    db: AsyncSession = Depends(get_db)
):
    profile = await service.update_profile(current_user.id, profile_data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await db.commit()
    return profile

@router.patch("/profiles/{user_id}", response_model=CandidateProfileResponse)
async def update_profile(
    user_id: UUID,
    profile_data: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service),
    db: AsyncSession = Depends(get_db)
):
    _ensure_access(current_user, user_id)
    profile = await service.update_profile(user_id, profile_data)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await db.commit()
    return profile

@router.get("/memories", response_model=List[CandidateMemoryResponse])
async def get_my_memories(
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service)
):
    return await service.get_memories(current_user.id, memory_type)

@router.get("/memories/{user_id}", response_model=List[CandidateMemoryResponse])
async def get_memories(
    user_id: UUID,
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service)
):
    _ensure_access(current_user, user_id)
    return await service.get_memories(user_id, memory_type)

@router.post("/memories", response_model=CandidateMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_my_memory(
    memory_data: CandidateMemoryCreate,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service),
    db: AsyncSession = Depends(get_db)
):
    memory = await service.upsert_memory(
        user_id=current_user.id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        source=memory_data.source,
        confidence=memory_data.confidence,
        interview_id=memory_data.interview_id
    )
    await db.commit()
    return memory

@router.post("/memories/{user_id}", response_model=CandidateMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    user_id: UUID,
    memory_data: CandidateMemoryCreate,
    current_user: User = Depends(get_current_user),
    service: CandidateService = Depends(get_candidate_service),
    db: AsyncSession = Depends(get_db)
):
    _ensure_access(current_user, user_id)
    memory = await service.upsert_memory(
        user_id=user_id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        source=memory_data.source,
        confidence=memory_data.confidence,
        interview_id=memory_data.interview_id
    )
    await db.commit()
    return memory

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        raw_text = extract_text(file.filename, file.content_type, file_bytes)
        doc = await service.ingest_document(
            user_id=current_user.id,
            filename=file.filename,
            file_type=file.content_type,
            raw_text=raw_text
        )
        await db.commit()
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/synthesize", status_code=status.HTTP_200_OK)
async def synthesize_profile(
    current_user: User = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    ai_service = Depends(get_ai_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers AI synthesis of candidate's memories into high-level strengths/weaknesses.
    """
    try:
        await candidate_service.summarize_and_update_insights(current_user.id, ai_service)
        await db.commit()
        return {"detail": "Profile synthesized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to synthesize profile: {str(e)}")
