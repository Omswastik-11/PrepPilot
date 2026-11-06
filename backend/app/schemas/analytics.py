from pydantic import BaseModel
from typing import List, Dict, Optional

class ActivityDay(BaseModel):
    date: str
    count: int

class AnalyticsResponse(BaseModel):
    total_interviews: int
    average_overall_score: Optional[float]
    score_by_type: Dict[str, float]
    difficulty_breakdown: Dict[str, int]
    activity_heatmap: List[ActivityDay]
    strengths: List[str]
    areas_for_improvement: List[str]
