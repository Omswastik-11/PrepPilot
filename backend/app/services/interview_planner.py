from typing import List, Optional
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.schemas.interview_state import InterviewState, PlannedQuestion
from app.models.interview import Interview
from app.models.question import Question, Answer
from app.services.candidate_service import CandidateService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    "Junior": ["Junior", "Mid"],
    "Mid": ["Junior", "Mid", "Senior"],
    "Senior": ["Mid", "Senior", "Principal"],
    "Principal": ["Senior", "Principal"],
}

class InterviewPlanner:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.candidate_service = CandidateService(session)
        self.retrieval_service = RetrievalService(session)

    async def determine_next_question(self, interview_id: UUID) -> PlannedQuestion:
        # 1. Rebuild state
        state, user_id = await self._build_interview_state(interview_id)
        
        # 2. Adjust difficulty based on recent performance
        next_difficulty = self._compute_next_difficulty(state)
        
        # 3. Select next skill/topic to test
        next_skill = self._select_next_skill(state)
        
        # 4. Gather context (memories) for this skill
        memories = await self.retrieval_service.retrieve_memories(
            user_id=user_id,
            query=f"Experience with {next_skill} for {next_difficulty} level",
            limit=2
        )
        context_str = " | ".join([m.content for m in memories]) if memories else None
        
        # 5. Hybrid Retrieval from Question Bank
        retrieved_questions = await self.retrieval_service.retrieve_questions(
            query=f"Interview question for {next_skill}",
            domain="Software Engineering", # default for MVP
            difficulty=next_difficulty,
            limit=1
        )
        
        if retrieved_questions:
            q = retrieved_questions[0]
            return PlannedQuestion(
                domain=q.domain,
                topic=next_skill,
                difficulty=next_difficulty,
                adaptation_reason=f"Candidate's recent performance led to {next_difficulty} level. Testing {next_skill}.",
                context_used=context_str,
                question_bank_id=q.id,
                question_text=q.question_text,
                expected_key_points=q.expected_key_points
            )
            
        # 6. Fallback: Generate dynamically
        return PlannedQuestion(
            domain="Software Engineering",
            topic=next_skill,
            difficulty=next_difficulty,
            adaptation_reason="Fallback to dynamic generation",
            context_used=context_str
        )

    async def _build_interview_state(self, interview_id: UUID) -> tuple[InterviewState, UUID]:
        result = await self.session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        q_result = await self.session.execute(
            select(Question)
            .options(selectinload(Question.answer))
            .where(Question.interview_id == interview_id)
            .order_by(Question.question_order)
        )
        questions = list(q_result.scalars().all())
        
        recent_scores = []
        skills_tested = []
        current_diff = "Junior"
        
        for q in questions:
            if q.topic:
                skills_tested.append(q.topic)
            if q.difficulty:
                current_diff = q.difficulty
            if q.answer and q.answer.score is not None:
                recent_scores.append(q.answer.score)
        
        # Try to get target skills from profile
        profile = await self.candidate_service.get_profile(interview.user_id)
        skills_to_test = profile.skills if profile and profile.skills else ["Python", "System Design", "Database", "API Design"]
        
        state = InterviewState(
            interview_id=interview.id,
            current_difficulty=current_diff,
            skills_to_test=skills_to_test,
            skills_tested=skills_tested,
            recent_performance=recent_scores,
        )
        return state, interview.user_id

    def _compute_next_difficulty(self, state: InterviewState) -> str:
        if not state.recent_performance:
            return state.current_difficulty
            
        avg_score = sum(state.recent_performance[-2:]) / min(len(state.recent_performance), 2)
        current = state.current_difficulty
        
        if current not in ALLOWED_TRANSITIONS:
            return "Junior"
            
        if avg_score >= 0.8:
            idx = ALLOWED_TRANSITIONS[current].index(current)
            if idx + 1 < len(ALLOWED_TRANSITIONS[current]):
                return ALLOWED_TRANSITIONS[current][idx + 1]
        elif avg_score < 0.5:
            idx = ALLOWED_TRANSITIONS[current].index(current)
            if idx - 1 >= 0:
                return ALLOWED_TRANSITIONS[current][idx - 1]
                
        return current

    def _select_next_skill(self, state: InterviewState) -> str:
        untested = [s for s in state.skills_to_test if s not in state.skills_tested]
        if untested:
            return untested[0]
        return "General Engineering"
