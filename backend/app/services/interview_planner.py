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

DIFFICULTY_MAP = {
    "easy": "Junior",
    "medium": "Mid",
    "hard": "Senior",
    "junior": "Junior",
    "mid": "Mid",
    "senior": "Senior",
    "principal": "Principal",
}

def normalize_difficulty(diff: Optional[str]) -> str:
    if not diff:
        return "Mid"
    return DIFFICULTY_MAP.get(str(diff).strip().lower(), "Mid")


class InterviewPlanner:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.candidate_service = CandidateService(session)
        self.retrieval_service = RetrievalService(session)

    async def determine_next_question(self, interview_id: UUID) -> PlannedQuestion:
        # 1. Rebuild state
        state, user_id, company, interview_type = await self._build_interview_state(interview_id)
        
        # 2. Adjust difficulty based on recent performance
        next_difficulty = self._compute_next_difficulty(state)
        
        # 3. Select next skill/topic to test
        next_skill = self._select_next_skill(state, interview_type)
        
        # 4. Gather context (memories) for this skill
        memories = await self.retrieval_service.retrieve_memories(
            user_id=user_id,
            query=f"Experience with {next_skill} for {next_difficulty} level",
            limit=2
        )
        
        profile = await self.candidate_service.get_profile(user_id)
        context_parts = []
        if profile:
            if profile.experience_years is not None:
                context_parts.append(f"Candidate has {profile.experience_years} years of experience.")
            if profile.target_roles:
                context_parts.append(f"Candidate is targeting roles: {', '.join(profile.target_roles)}")
                
        if memories:
            context_parts.append("Candidate specific memories/achievements: " + " | ".join([m.content for m in memories]))
            
        context_str = "\n".join(context_parts) if context_parts else None
        
        role_str = f" for the {state.target_role} role" if state.target_role else ""
        query_text = f"Interview question for {next_skill}{role_str}"
        
        # Determine domain dynamically based on interview type
        if interview_type == "behavioral":
            domain = "Behavioral Competencies"
        elif interview_type == "system_design":
            domain = "System Design"
        else:
            domain = state.target_role if state.target_role else "Software Engineering"
        
        # 5. Hybrid Retrieval from Question Bank
        retrieved_questions = await self.retrieval_service.retrieve_questions(
            query=query_text,
            domain=domain,
            difficulty=next_difficulty,
            company=company,
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
            domain=domain,
            topic=next_skill,
            difficulty=next_difficulty,
            adaptation_reason="Fallback to dynamic generation",
            context_used=context_str
        )

    async def _build_interview_state(self, interview_id: UUID) -> tuple[InterviewState, UUID, Optional[str], str]:
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
        current_diff = normalize_difficulty(interview.difficulty)
        
        for q in questions:
            if q.topic:
                skills_tested.append(q.topic)
            if q.difficulty:
                current_diff = normalize_difficulty(q.difficulty)
            if q.answer and q.answer.score is not None:
                recent_scores.append(q.answer.score)
        
        # Determine skills to test intelligently based on interview_type and role
        itype = (interview.interview_type or "").strip().lower()
        target_role = interview.metadata_.get("role") if interview.metadata_ else None
        profile = await self.candidate_service.get_profile(interview.user_id)

        if itype == "behavioral":
            skills_to_test = [
                "Conflict Resolution",
                "Leadership & Ownership",
                "Teamwork & Collaboration",
                "Communication",
                "Problem Solving",
                "Adaptability & Growth",
            ]
        elif itype == "system_design":
            skills_to_test = [
                "System Architecture",
                "Scalability & Caching",
                "Data Modeling & Storage",
                "API Design & Protocols",
                "Reliability & Fault Tolerance",
            ]
        else:
            # Technical interview: use candidate profile skills if provided
            if profile and profile.skills:
                skills_to_test = profile.skills
            elif target_role:
                r_lower = target_role.lower()
                if any(k in r_lower for k in ["front", "react", "web", "ui", "ux"]):
                    skills_to_test = ["JavaScript", "React", "TypeScript", "State Management", "Web Performance"]
                elif any(k in r_lower for k in ["python", "data", "ml", "ai", "machine"]):
                    skills_to_test = ["Python", "Data Processing", "SQL & Databases", "Machine Learning", "System Optimization"]
                elif any(k in r_lower for k in ["java", "spring"]):
                    skills_to_test = ["Java", "Spring Boot", "REST APIs", "Databases", "Concurrency"]
                elif any(k in r_lower for k in ["cloud", "devops", "sre", "infra"]):
                    skills_to_test = ["CI/CD Pipelines", "Docker & Kubernetes", "Cloud Architecture", "Monitoring & Logging", "Infrastructure"]
                elif any(k in r_lower for k in ["mobile", "android", "ios", "flutter"]):
                    skills_to_test = ["Mobile Architecture", "State Management", "Offline Sync", "UI Performance", "Networking"]
                else:
                    skills_to_test = ["Data Structures", "Algorithms", "System Architecture", "Databases", "API Design"]
            else:
                skills_to_test = ["Data Structures", "Algorithms", "System Architecture", "Databases", "API Design"]

        state = InterviewState(
            interview_id=interview.id,
            current_difficulty=current_diff,
            target_role=target_role,
            skills_to_test=skills_to_test,
            skills_tested=skills_tested,
            recent_performance=recent_scores,
        )
        return state, interview.user_id, interview.company, itype

    def _compute_next_difficulty(self, state: InterviewState) -> str:
        if not state.recent_performance:
            return normalize_difficulty(state.current_difficulty)
            
        avg_score = sum(state.recent_performance[-2:]) / min(len(state.recent_performance), 2)
        current = normalize_difficulty(state.current_difficulty)
        
        if current not in ALLOWED_TRANSITIONS:
            return "Mid"
            
        # EvaluationResult scores are on a 0.0 to 10.0 scale
        if avg_score >= 8.0:
            idx = ALLOWED_TRANSITIONS[current].index(current)
            if idx + 1 < len(ALLOWED_TRANSITIONS[current]):
                return ALLOWED_TRANSITIONS[current][idx + 1]
        elif avg_score < 5.0:
            idx = ALLOWED_TRANSITIONS[current].index(current)
            if idx - 1 >= 0:
                return ALLOWED_TRANSITIONS[current][idx - 1]
                
        return current

    def _select_next_skill(self, state: InterviewState, interview_type: str = "technical") -> str:
        untested = [s for s in state.skills_to_test if s not in state.skills_tested]
        if untested:
            return untested[0]
        if interview_type == "behavioral":
            return "Situational Judgment"
        elif interview_type == "system_design":
            return "Distributed Systems"
        return "Core Engineering"
