from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.schemas.candidate import CandidateProfileCreate, CandidateProfileUpdate, CandidateProfileResponse, CandidateMemoryCreate, CandidateMemoryResponse
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])

def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    return CandidateService(db)

@router.post("/profiles", response_model=CandidateProfileResponse)
async def create_profile(
    profile_data: CandidateProfileCreate,
    # In a real app, user_id comes from the authenticated current_user
    user_id: UUID,
    service: CandidateService = Depends(get_candidate_service)
):
    try:
        return await service.create_profile(user_id, profile_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profiles/{user_id}", response_model=CandidateProfileResponse)
async def get_profile(
    user_id: UUID,
    service: CandidateService = Depends(get_candidate_service)
):
    profile = await service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.patch("/profiles/{user_id}", response_model=CandidateProfileResponse)
async def update_profile(
    user_id: UUID,
    profile_data: CandidateProfileUpdate,
    service: CandidateService = Depends(get_candidate_service)
):
    profile = await service.update_profile(user_id, profile_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/memories/{user_id}", response_model=List[CandidateMemoryResponse])
async def get_memories(
    user_id: UUID,
    memory_type: Optional[str] = None,
    service: CandidateService = Depends(get_candidate_service)
):
    return await service.get_memories(user_id, memory_type)

@router.post("/memories/{user_id}", response_model=CandidateMemoryResponse)
async def create_memory(
    user_id: UUID,
    memory_data: CandidateMemoryCreate,
    service: CandidateService = Depends(get_candidate_service)
):
    return await service.upsert_memory(
        user_id=user_id,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        source=memory_data.source,
        confidence=memory_data.confidence,
        interview_id=memory_data.interview_id
    )
