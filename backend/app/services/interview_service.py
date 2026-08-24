"""
Interview Service.

Orchestrates the interview lifecycle.
Integrates AIService for generation/evaluation.
Owns transaction boundaries.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.exceptions import NotFoundError, InvalidStateError, AuthorizationError, AlreadyExistsError
from app.models.interview import Interview
from app.models.question import Question, Answer
from app.repositories.interview_repository import InterviewRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.answer_repository import AnswerRepository
from app.schemas.interview import InterviewCreate
from app.schemas.question import AnswerCreate
from app.services.ai.service import AIService
from app.services.interview_planner import InterviewPlanner
from app.services.candidate_service import CandidateService


class InterviewService:
    def __init__(self, db: AsyncSession, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        self.interview_repo = InterviewRepository(db)
        self.question_repo = QuestionRepository(db)
        self.answer_repo = AnswerRepository(db)

    async def create_interview(self, user_id: UUID, data: InterviewCreate) -> Interview:
        """
        Creates a new interview and generates the FIRST question adaptively.
        """
        # 1. Persist Interview
        interview = Interview(
            user_id=user_id,
            interview_type=data.interview_type,
            difficulty=data.difficulty,
            num_questions=data.num_questions,
            company=data.company,
            status="in_progress",
        )
        self.interview_repo.add(interview)
        await self.db.flush() # get interview.id
        
        # 2. Plan first question
        planner = InterviewPlanner(self.db)
        planned_q = await planner.determine_next_question(interview.id)
        
        if not planned_q.question_text:
            # Generate via AI if not from question bank
            # Note: For real app, AIService should take planned_q
            generated_questions = await self.ai_service.generate_questions(
                interview_type=data.interview_type,
                difficulty=planned_q.difficulty,
                num_questions=1,
                company=data.company,
            )
            q_text = generated_questions[0].question_text
            ideal_answer = "\n".join(generated_questions[0].ideal_answer_hints)
        else:
            q_text = planned_q.question_text
            ideal_answer = planned_q.expected_key_points
            
        q = Question(
            interview_id=interview.id,
            question_text=q_text,
            question_order=1,
            time_limit_seconds=120,
            ideal_answer=ideal_answer,
            domain=planned_q.domain,
            topic=planned_q.topic,
            difficulty=planned_q.difficulty,
            context_used=planned_q.context_used,
            adaptation_reason=planned_q.adaptation_reason
        )
        self.question_repo.add(q)
        await self.db.commit()
        
        return await self.get_interview(interview.id, user_id)

    async def get_interview(self, interview_id: UUID, user_id: UUID) -> Interview:
        interview = await self.interview_repo.get_by_id_with_questions(interview_id)
        if not interview:
            raise NotFoundError("Interview not found")
        if interview.user_id != user_id:
            raise AuthorizationError("Not authorized to access this interview")
        return interview

    async def list_interviews(
        self, user_id: UUID, status: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> tuple[list[Interview], int]:
        return await self.interview_repo.list_by_user(user_id, status, limit, offset)

    async def submit_answer(
        self, interview_id: UUID, question_id: UUID, user_id: UUID, data: AnswerCreate
    ) -> Answer:
        """
        Submits an answer.
        AI evaluation happens BEFORE the database transaction for the Answer starts.
        """
        # 1. Fetch resources and validate state
        interview = await self.get_interview(interview_id, user_id)
        
        if interview.status != "in_progress":
            raise InvalidStateError(f"Cannot submit answer. Interview is {interview.status}")

        question = await self.question_repo.get_with_answer(question_id)
        if not question or question.interview_id != interview_id:
            raise NotFoundError("Question not found in this interview")
            
        if question.answer is not None:
            raise InvalidStateError("This question has already been answered")

        # 2. Evaluate answer via AI
        evaluation = await self.ai_service.evaluate_answer(
            question_text=question.question_text,
            user_answer=data.user_answer,
            interview_type=interview.interview_type,
            difficulty=interview.difficulty,
        )

        # 3. Resolve Candidate Memories (External AI calls for embeddings)
        candidate_service = CandidateService(self.db)
        memory_plans = []
        if evaluation.strengths:
            for s in evaluation.strengths:
                plan = await candidate_service.resolve_memory_upsert(
                    user_id=user_id, memory_type="strength", content=s, source="interview_answer", interview_id=interview_id
                )
                memory_plans.append(plan)
        if evaluation.weaknesses:
            for w in evaluation.weaknesses:
                plan = await candidate_service.resolve_memory_upsert(
                    user_id=user_id, memory_type="weakness", content=w, source="interview_answer", interview_id=interview_id
                )
                memory_plans.append(plan)

        # 4. Plan Next Question if not finished (External AI calls)
        current_q_count = len(interview.questions)
        next_q = None
        if current_q_count < interview.num_questions:
            planner = InterviewPlanner(self.db)
            planned_q = await planner.determine_next_question(interview_id)
            
            if not planned_q.question_text:
                generated = await self.ai_service.generate_questions(
                    interview_type=interview.interview_type,
                    difficulty=planned_q.difficulty,
                    num_questions=1,
                    company=interview.company,
                )
                q_text = generated[0].question_text
                ideal_answer = "\n".join(generated[0].ideal_answer_hints)
            else:
                q_text = planned_q.question_text
                ideal_answer = planned_q.expected_key_points
                
            next_q = Question(
                interview_id=interview_id,
                question_text=q_text,
                question_order=current_q_count + 1,
                time_limit_seconds=120,
                ideal_answer=ideal_answer,
                domain=planned_q.domain,
                topic=planned_q.topic,
                difficulty=planned_q.difficulty,
                context_used=planned_q.context_used,
                adaptation_reason=planned_q.adaptation_reason
            )

        # 5. Persist Answer and all resolved data in a single transaction
        answer = Answer(
            question_id=question_id,
            user_answer=data.user_answer,
            time_taken_seconds=data.time_taken_seconds,
            score=evaluation.score,
            feedback=evaluation.feedback,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            submitted_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.answer_repo.add(answer)
        
        for plan in memory_plans:
            await candidate_service.apply_memory_upsert(plan)
            
        if next_q:
            self.question_repo.add(next_q)

        try:
            await self.db.commit()
            await self.db.refresh(answer)
        except IntegrityError:
            await self.db.rollback()
            raise AlreadyExistsError("Concurrent answer submission detected")
            
        return answer

    async def abandon_interview(self, interview_id: UUID, user_id: UUID) -> Interview:
        interview = await self.get_interview(interview_id, user_id)
        
        if interview.status != "in_progress":
            raise InvalidStateError(f"Cannot abandon. Interview is {interview.status}")
            
        interview.status = "abandoned"
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def complete_interview(self, interview_id: UUID, user_id: UUID) -> Interview:
        interview = await self.get_interview(interview_id, user_id)
        
        if interview.status != "in_progress":
            raise InvalidStateError(f"Cannot complete. Interview is {interview.status}")
            
        unanswered_count = await self.question_repo.get_unanswered_count(interview_id)
        if unanswered_count > 0:
            raise InvalidStateError("Cannot complete interview. Not all questions are answered.")
            
        # Compute total score
        # Note: we already have interview.questions loaded with answers due to get_interview()
        total_score = 0.0
        answered = 0
        for q in interview.questions:
            if q.answer and q.answer.score is not None:
                total_score += q.answer.score
                answered += 1
                
        if answered > 0:
            interview.total_score = round(total_score / answered, 2)
            
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        await self.db.commit()
        await self.db.refresh(interview)
        return interview
