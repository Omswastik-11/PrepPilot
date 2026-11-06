"""
Gemini AI Provider.

Implementation of the BaseAIProvider for Google Gemini.
Uses structured output to guarantee Pydantic model conformant JSON.
"""

import json
from google import genai
from google.genai import types

from app.config import get_settings
from app.exceptions import AIServiceError
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.services.ai.base import BaseAIProvider

settings = get_settings()


class GeminiProvider(BaseAIProvider):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    async def generate_questions(
        self,
        interview_type: str,
        difficulty: str,
        num_questions: int,
        company: str | None,
        candidate_background: str | None = None,
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        bg_text = f"\nCandidate Background: {candidate_background}\n" if candidate_background else ""
        prompt = f"""
You are a senior technical interviewer at {company_text}.
Generate {num_questions} {difficulty} {interview_type} interview questions.{bg_text}
Requirements:
- Questions should be realistic and commonly asked in real interviews
- Each question should be distinct and cover different aspects
- For behavioral: use the STAR method expectation
- For technical: include problem-solving and coding concepts
- For system_design: include scale, trade-offs, and architecture
"""
        
        try:
            # We use the sync client with asyncio.to_thread or run it sync since google-genai supports async?
            # Actually, google-genai 1.0.0 has async client via `client.aio.models.generate_content`
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[GeneratedQuestion],
                    temperature=0.7,
                )
            )
            
            # The response text should be a JSON array matching the schema
            data = json.loads(response.text)
            return [GeneratedQuestion(**item) for item in data]
            
        except Exception as e:
            # Log the detailed exception internally in a real app
            raise AIServiceError(f"Gemini generation failed: {str(e)}")

    async def generate_next_interview_question(
        self,
        interview_type: str,
        target_difficulty: str,
        company: str | None,
        role: str | None,
        candidate_background: str | None,
        conversation_history: list[dict],
        question_number: int,
    ) -> GeneratedQuestion:
        company_text = company if company else "a top tech company"
        role_text = role if role else "Software Engineer"
        bg_text = f"\nCANDIDATE CONTEXT:\n{candidate_background}\n" if candidate_background else ""
        
        history_text = ""
        for msg in conversation_history[-6:]:  # Last 3 Q&A pairs
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
            if msg.get('score') is not None:
                history_text += f"SCORE: {msg['score']}/10\n"
            history_text += "---\n"
            
        type_instructions = ""
        if interview_type.lower() == "behavioral":
            type_instructions = "This is a BEHAVIORAL interview. Focus strictly on past experiences, soft skills, and scenario-based questions (STAR method). DO NOT ask coding or algorithmic questions."
        elif interview_type.lower() == "system_design":
            type_instructions = "This is a SYSTEM DESIGN interview. Focus on architecture, scalability, tradeoffs, and API design."
        else:
            type_instructions = "This is a TECHNICAL interview. Focus on data structures, algorithms, coding, and problem-solving."
            
        prompt = f"""
You are a senior {interview_type} interviewer at {company_text} interviewing a candidate for a {role_text} position.

INTERVIEW STYLE:
- {type_instructions}
- This is question #{question_number} of a live interview.
- Target difficulty: {target_difficulty}. Calibrate your questions to this level.
- PROGRESSIVE DIFFICULTY: Start with a warm-up if this is question 1-2, then gradually increase.
- FOLLOW-UPS: If the candidate's last answer was incomplete or had an interesting angle, ask a follow-up that digs deeper into that specific topic rather than jumping to something unrelated.
- CONVERSATIONAL: Reference the candidate's previous answers when relevant. Say things like "You mentioned X earlier, let's explore that further".
{bg_text}
CONVERSATION SO FAR:
{history_text}

Generate the next interview question. If the previous answer scored below 5/10, consider asking a simpler question on the same topic to let them recover. If it scored above 8/10, push harder.
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedQuestion,
                    temperature=0.7,
                )
            )
            data = json.loads(response.text)
            return GeneratedQuestion(**data)
        except Exception as e:
            raise AIServiceError(f"Gemini next question generation failed: {str(e)}")

    async def generate_questions_from_context(
        self,
        context: str,
        domain: str,
        topic: str,
        company: str | None,
        num_questions: int,
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        prompt = f"""
You are a senior technical interviewer at {company_text}.
Generate {num_questions} interview questions based SPECIFICALLY on the following content.

Domain: {domain}
Topic: {topic}
Content: {context}

Requirements:
- The questions MUST be derived from the specific details and claims in the provided content.
- Do NOT generate generic questions about the domain/topic.
- Each question should test the candidate's understanding of the provided content.
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[GeneratedQuestion],
                    temperature=0.7,
                )
            )
            
            data = json.loads(response.text)
            return [GeneratedQuestion(**item) for item in data]
            
        except Exception as e:
            raise AIServiceError(f"Gemini generation from context failed: {str(e)}")

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        prompt = f"""
You are evaluating a candidate's answer in a real interview setting.

Question: {question_text}
Interview Type: {interview_type}
Difficulty: {difficulty}
Candidate's Answer: {user_answer}

SCORING RUBRIC (calibrated to {difficulty} difficulty):
- For EASY questions: Award 7+ for demonstrating basic understanding. Only score below 5 for completely wrong answers.
- For MEDIUM questions: Award 7+ for solid answers with good structure. Score 5-7 for partial answers. Below 5 for fundamental misunderstandings.
- For HARD questions: Award 7+ for exceptional depth and production-level thinking. Score 5-7 for reasonable approaches with gaps. Below 5 for surface-level answers.

FEEDBACK STYLE:
- Be encouraging but honest
- Strengths: Mention 1-3 SPECIFIC things they did well (not generic praise)
- Weaknesses: Frame as "areas to improve" with actionable advice (e.g., "Practice stack-based problems focusing on monotonic stack patterns" NOT "improve at stacks")
- Keep feedback THEMATIC, not overly granular about one specific problem
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EvaluationResult,
                    temperature=0.3,
                )
            )
            data = json.loads(response.text)
            return EvaluationResult(**data)
            
        except Exception as e:
            raise AIServiceError(f"Gemini evaluation failed: {str(e)}")

    async def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        try:
            config_kwargs = {"temperature": 0.7}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
                
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return response.text
        except Exception as e:
            raise AIServiceError(f"Gemini generic generation failed: {str(e)}")
