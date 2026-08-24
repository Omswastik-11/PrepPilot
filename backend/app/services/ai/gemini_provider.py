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
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        prompt = f"""
You are a senior technical interviewer at {company_text}.
Generate {num_questions} {difficulty} {interview_type} interview questions.

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

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        prompt = f"""
You are evaluating a candidate's answer to an interview question.

Question: {question_text}
Interview Type: {interview_type}
Difficulty: {difficulty}
Candidate's Answer: {user_answer}

Evaluate the answer based on correctness, clarity, and completeness.
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
