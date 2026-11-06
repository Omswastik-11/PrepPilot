from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/candidate/analytics", tags=["Analytics"])

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    return await service.get_analytics(current_user.id)
