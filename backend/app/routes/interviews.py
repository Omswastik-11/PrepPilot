"""
Interview Routes.

Endpoints for managing the interview lifecycle.
Thin HTTP adapters delegating to InterviewService.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status, Query

from app.dependencies import get_interview_service, get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    InterviewListResponse,
    InterviewSummary,
    InterviewTitleUpdate,
)
from app.schemas.question import AnswerCreate, AnswerResponse
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Start a new interview."""
    interview = await interview_service.create_interview(current_user.id, data)
    return interview


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    status: str | None = Query(None, description="Filter by status (e.g., in_progress, completed)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """List user's interviews."""
    items, total = await interview_service.list_interviews(current_user.id, status, limit, offset)
    return InterviewListResponse(
        items=items,  # type: ignore
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Get interview details (including questions and answers)."""
    return await interview_service.get_interview(interview_id, current_user.id)


@router.post("/{interview_id}/questions/{question_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    interview_id: UUID,
    question_id: UUID,
    data: AnswerCreate,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Submit an answer to a specific question."""
    answer = await interview_service.submit_answer(interview_id, question_id, current_user.id, data)
    return answer


@router.post("/{interview_id}/abandon", response_model=InterviewSummary)
async def abandon_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Abandon an in-progress interview."""
    interview = await interview_service.abandon_interview(interview_id, current_user.id)
    return interview


@router.post("/{interview_id}/complete", response_model=InterviewSummary)
async def complete_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Complete an interview (requires all questions to be answered)."""
    interview = await interview_service.complete_interview(interview_id, current_user.id)
    return interview

@router.patch("/{interview_id}/title", response_model=InterviewSummary)
async def update_interview_title(
    interview_id: UUID,
    data: InterviewTitleUpdate,
    current_user: User = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Update interview title."""
    interview = await interview_service.update_title(interview_id, current_user.id, data.title)
    return interview
