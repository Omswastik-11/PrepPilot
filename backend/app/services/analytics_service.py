from uuid import UUID
from collections import defaultdict
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.interview import Interview
from app.models.candidate import CandidateMemory
from app.schemas.analytics import AnalyticsResponse, ActivityDay

class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_analytics(self, user_id: UUID) -> AnalyticsResponse:
        # 1. Total Interviews & Average Score
        # Only count completed interviews for scores
        interviews_query = select(Interview).where(Interview.user_id == user_id, Interview.status == "completed")
        result = await self.session.execute(interviews_query)
        completed_interviews = list(result.scalars().all())

        total_interviews = len(completed_interviews)
        
        score_by_type = defaultdict(list)
        difficulty_breakdown = {"easy": 0, "medium": 0, "hard": 0}
        
        for interview in completed_interviews:
            if interview.total_score is not None:
                score_by_type[interview.interview_type].append(interview.total_score)
                
            diff = interview.difficulty.lower()
            if diff in difficulty_breakdown:
                difficulty_breakdown[diff] += 1
            else:
                difficulty_breakdown["medium"] += 1 # fallback

        avg_overall = None
        if total_interviews > 0:
            total_scores = [i.total_score for i in completed_interviews if i.total_score is not None]
            if total_scores:
                avg_overall = round(sum(total_scores) / len(total_scores), 2)

        avg_by_type = {}
        for itype, scores in score_by_type.items():
            if scores:
                avg_by_type[itype] = round(sum(scores) / len(scores), 2)

        # 2. Activity Heatmap
        # Count interviews started per day (including in_progress/abandoned)
        heatmap_query = select(Interview.started_at).where(Interview.user_id == user_id, Interview.started_at.is_not(None))
        result = await self.session.execute(heatmap_query)
        started_ats = list(result.scalars().all())
        
        day_counts = defaultdict(int)
        for dt in started_ats:
            day_str = dt.strftime("%Y-%m-%d")
            day_counts[day_str] += 1
            
        activity_heatmap = [ActivityDay(date=k, count=v) for k, v in day_counts.items()]

        # 3. Strengths & Areas for Improvement (from memories)
        memories_query = select(CandidateMemory).where(
            CandidateMemory.user_id == user_id,
            CandidateMemory.memory_type.in_(["strength", "weakness"])
        ).order_by(CandidateMemory.confidence.desc())
        
        result = await self.session.execute(memories_query)
        memories = list(result.scalars().all())
        
        strengths = []
        areas = []
        for m in memories:
            if m.memory_type == "strength" and len(strengths) < 5:
                strengths.append(m.content)
            elif m.memory_type == "weakness" and len(areas) < 5:
                areas.append(m.content)

        return AnalyticsResponse(
            total_interviews=total_interviews,
            average_overall_score=avg_overall,
            score_by_type=avg_by_type,
            difficulty_breakdown=difficulty_breakdown,
            activity_heatmap=activity_heatmap,
            strengths=strengths,
            areas_for_improvement=areas
        )
