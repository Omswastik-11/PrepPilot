"""
HuggingFace AI Provider.

Implementation of the BaseAIProvider for HuggingFace Inference API.
Used as a fallback when Gemini is unavailable.
"""

import json
import httpx

from app.config import get_settings
from app.exceptions import AIServiceError
from app.schemas.ai import GeneratedQuestion, EvaluationResult
from app.services.ai.base import BaseAIProvider

settings = get_settings()


class HuggingFaceProvider(BaseAIProvider):
    def __init__(self):
        if not settings.HF_TOKEN:
            raise ValueError("HF_TOKEN is not set")
        self.api_url = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL}"
        self.headers = {
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            "Content-Type": "application/json",
        }
        self.timeout = settings.HF_TIMEOUT_SECONDS

    async def _make_request(self, prompt: str) -> dict:
        """Helper to call HF Inference API and parse JSON."""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1000,
                "return_full_text": False,
                "temperature": 0.7,
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # HF usually returns [{"generated_text": "..."}]
                text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
                
                # Try to extract JSON from the text
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
                
            except Exception as e:
                raise AIServiceError(f"HuggingFace request failed: {str(e)}")

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
        prompt = f"""[INST] You are a senior technical interviewer at {company_text}.{bg_text}
Generate {num_questions} {difficulty} {interview_type} interview questions.

Return ONLY a valid JSON array of objects. Do not include markdown formatting or explanations.
Each object must have:
- "question_text" (string)
- "time_limit_seconds" (integer, 60-300)
- "ideal_answer_hints" (array of strings)

Example output:
[
  {{
    "question_text": "...",
    "time_limit_seconds": 120,
    "ideal_answer_hints": ["...", "..."]
  }}
]
[/INST]"""

        data = await self._make_request(prompt)
        if not isinstance(data, list):
            raise AIServiceError("HuggingFace returned invalid structure for questions")
            
        return [GeneratedQuestion(**item) for item in data]

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
        # Fallback to standard generic question generation for HF
        questions = await self.generate_questions(
            interview_type=interview_type,
            difficulty=target_difficulty,
            num_questions=1,
            company=company,
            candidate_background=candidate_background,
        )
        return questions[0]

    async def generate_questions_from_context(
        self,
        context: str,
        domain: str,
        topic: str,
        company: str | None,
        num_questions: int,
    ) -> list[GeneratedQuestion]:
        company_text = company if company else "a top tech company"
        prompt = f"""[INST] You are a senior technical interviewer at {company_text}.
Generate {num_questions} interview questions based SPECIFICALLY on the following content.

Domain: {domain}
Topic: {topic}
Content: {context}

Return ONLY a valid JSON array of objects. Do not include markdown formatting or explanations.
Each object must have:
- "question_text" (string, derived specifically from the content)
- "time_limit_seconds" (integer, 60-300)
- "ideal_answer_hints" (array of strings)

Example output:
[
  {{
    "question_text": "...",
    "time_limit_seconds": 120,
    "ideal_answer_hints": ["...", "..."]
  }}
]
[/INST]"""

        data = await self._make_request(prompt)
        if not isinstance(data, list):
            raise AIServiceError("HuggingFace returned invalid structure for context questions")
            
        return [GeneratedQuestion(**item) for item in data]

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        interview_type: str,
        difficulty: str,
    ) -> EvaluationResult:
        prompt = f"""[INST] You are evaluating a candidate's answer.
Question: {question_text}
Candidate's Answer: {user_answer}

Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
The object must have:
- "score" (float 0.0-10.0)
- "feedback" (string)
- "strengths" (array of strings)
- "weaknesses" (array of strings)
- "ideal_answer" (string)
[/INST]"""

        data = await self._make_request(prompt)
        if not isinstance(data, dict):
            raise AIServiceError("HuggingFace returned invalid structure for evaluation")
            
        return EvaluationResult(**data)

    async def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        # HF doesn't strictly have a system instruction unless we format it, so we'll just prepend it.
        if system_instruction:
            full_prompt = f"[INST] <<SYS>>\n{system_instruction}\n<</SYS>>\n\n{prompt} [/INST]"
        else:
            full_prompt = f"[INST] {prompt} [/INST]"
            
        # The base _make_request method currently tries to parse JSON.
        # We need it to just return text for this method, or we can use the raw post directly.
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "return_full_text": False,
                "temperature": 0.7,
            }
        }
        
        import httpx
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
                return text
            except Exception as e:
                raise AIServiceError(f"HuggingFace generic generation failed: {str(e)}")
