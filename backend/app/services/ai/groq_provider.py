"""
Groq AI Provider.

Implementation of the BaseAIProvider for Groq's API.
Used as a fallback when Gemini is unavailable.
"""

import json
import logging

from groq import AsyncGroq

from app.config import get_settings
from app.exceptions import AIServiceError
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.services.ai.base import BaseAIProvider

settings = get_settings()
logger = logging.getLogger(__name__)

class GroqProvider(BaseAIProvider):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")
        self.client = AsyncGroq(
            api_key=settings.GROQ_API_KEY, 
            timeout=settings.GROQ_TIMEOUT_SECONDS
        )
        self.model_name = settings.GROQ_MODEL

    async def _make_request(self, system_instruction: str, prompt: str, json_mode: bool = False) -> str:
        """Helper to call Groq API."""
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            completion = await self.client.chat.completions.create(**kwargs)
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            raise AIServiceError(f"Groq request failed: {str(e)}")

    async def _parse_json_response(self, text: str) -> dict | list:
        # Try to extract JSON from the text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start_idx = text.find("{")
            start_array_idx = text.find("[")
            
            if start_array_idx != -1 and (start_idx == -1 or start_array_idx < start_idx):
                end_idx = text.rfind("]") + 1
                json_str = text[start_array_idx:end_idx]
            else:
                start_idx = max(0, start_idx)
                end_idx = text.rfind("}") + 1
                json_str = text[start_idx:end_idx]
                
            return json.loads(json_str)

    async def generate_questions(
        self,
        interview_type: str,
        difficulty: str,
        num_questions: int,
        company: str | None,
        candidate_background: str | None = None,
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        bg_text = f" Candidate Background: {candidate_background}." if candidate_background else ""
        system_instruction = f"You are a senior technical interviewer at {company_text}.{bg_text}"
        prompt = f"""Generate {num_questions} {difficulty} {interview_type} interview questions.

Return ONLY a valid JSON object with a single key "questions" containing an array of objects. Do not include markdown formatting or explanations.
Each object in the array must have:
- "question_text" (string)
- "time_limit_seconds" (integer, 60-300)
- "ideal_answer_hints" (array of strings)"""

        response_text = await self._make_request(system_instruction, prompt, json_mode=True)
        data = await self._parse_json_response(response_text)
        
        questions_data = data.get("questions", data) if isinstance(data, dict) else data
            
        if not isinstance(questions_data, list):
            raise AIServiceError("Groq returned invalid structure for questions")
            
        return [GeneratedQuestion(**item) for item in questions_data]

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
        bg_text = f"Candidate Background: {candidate_background}." if candidate_background else ""
        role_text = f" for the role of {role}" if role else ""
        
        type_instructions = ""
        if interview_type.lower() == "behavioral":
            type_instructions = "This is a BEHAVIORAL interview. Focus strictly on past experiences, teamwork, leadership, conflict resolution, and soft skills using the STAR method. DO NOT ask coding, algorithm, or technical questions."
        elif interview_type.lower() == "system_design":
            type_instructions = "This is a SYSTEM DESIGN interview. Focus on architecture, scalability, tradeoffs, API design, and databases. DO NOT ask simple LeetCode-style algorithm questions."
        else:
            type_instructions = "This is a TECHNICAL interview. Focus on data structures, algorithms, coding, and problem-solving."
        
        system_instruction = f"""You are a senior interviewer at {company_text} conducting a {interview_type} interview{role_text}. {bg_text}
{type_instructions}
Your task is to ask the next logical interview question based on the candidate's previous responses and the target difficulty."""

        history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history])
        
        prompt = f"""Conversation History:
{history_text}

Task: Generate question #{question_number} at '{target_difficulty}' difficulty. 
If the candidate's last answer was incomplete, this should be a follow-up question. If it was complete, ask a new question.

Return ONLY a valid JSON object containing exactly ONE question. Do not include markdown formatting.
The object must have:
- "question_text" (string)
- "time_limit_seconds" (integer, 60-300)
- "ideal_answer_hints" (array of strings)"""

        response_text = await self._make_request(system_instruction, prompt, json_mode=True)
        data = await self._parse_json_response(response_text)
        
        if not isinstance(data, dict):
            raise AIServiceError("Groq returned invalid structure for next question")
            
        return GeneratedQuestion(**data)

    async def generate_questions_from_context(
        self,
        context: str,
        domain: str,
        topic: str,
        company: str | None,
        num_questions: int,
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        system_instruction = f"You are a senior technical interviewer at {company_text}."
        prompt = f"""Generate {num_questions} interview questions based SPECIFICALLY on the following content.

Domain: {domain}
Topic: {topic}
Content: {context}

Return ONLY a valid JSON object with a single key "questions" containing an array of objects. Do not include markdown formatting or explanations.
Each object must have:
- "question_text" (string, derived specifically from the content)
- "time_limit_seconds" (integer, 60-300)
- "ideal_answer_hints" (array of strings)"""

        response_text = await self._make_request(system_instruction, prompt, json_mode=True)
        data = await self._parse_json_response(response_text)
        
        questions_data = data.get("questions", data) if isinstance(data, dict) else data
            
        if not isinstance(questions_data, list):
            raise AIServiceError("Groq returned invalid structure for context questions")
            
        return [GeneratedQuestion(**item) for item in questions_data]

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        system_instruction = "You are an expert technical interviewer evaluating a candidate's answer."
        prompt = f"""Question: {question_text}
Candidate's Answer: {user_answer}
Target Difficulty: {difficulty}
Interview Type: {interview_type}

Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
The object must have:
- "score" (float 0.0-10.0, adjust expectation based on Target Difficulty)
- "feedback" (string)
- "strengths" (array of strings)
- "weaknesses" (array of strings)
- "ideal_answer" (string)"""

        response_text = await self._make_request(system_instruction, prompt, json_mode=True)
        data = await self._parse_json_response(response_text)
        
        if not isinstance(data, dict):
            raise AIServiceError("Groq returned invalid structure for evaluation")
            
        return EvaluationResult(**data)

    async def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        return await self._make_request(system_instruction, prompt, json_mode=False)
