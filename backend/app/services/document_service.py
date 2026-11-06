from uuid import UUID
from typing import Optional, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import json

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.candidate_service import CandidateService
from app.schemas.candidate import CandidateProfileUpdate, CandidateMemoryCreate
from app.services.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

# Pydantic schema for structured AI extraction
class ExtractedMemory(BaseModel):
    memory_type: str = Field(description="strength, experience, or skill")
    content: str = Field(description="The actual memory fact extracted")

class ResumeExtraction(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    target_roles: List[str] = Field(default_factory=list)
    memories: List[ExtractedMemory] = Field(default_factory=list)

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.doc_repo = DocumentRepository(session)
        self.candidate_service = CandidateService(session)
        self.ai_provider = GeminiProvider()  # For parsing

    async def ingest_document(self, user_id: UUID, filename: str, file_type: str, raw_text: str) -> Document:
        """
        Creates the document record and kicks off processing.
        """
        # 1. Save document in pending state
        doc = await self.doc_repo.create(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            content=raw_text,
            status="pending"
        )
        
        # 2. Process document (ideally background task, but keeping simple for MVP)
        try:
            await self._process_resume(user_id, doc.id, raw_text)
            doc = await self.doc_repo.update(doc.id, status="processed")
        except Exception as e:
            logger.error(f"Failed to process document {doc.id}: {e}")
            doc = await self.doc_repo.update(doc.id, status="failed", error_message=str(e))
            
        return doc
        
    async def _process_resume(self, user_id: UUID, doc_id: UUID, text: str):
        prompt = f"""
        Extract the following information from this candidate's resume/document.
        Return structured data containing their skills, years of experience, potential target roles, 
        and notable 'memories' (specific achievements, experiences, or strengths).
        
        Document Text:
        {text[:15000]}  # limit text to avoid token limits if extremely long
        """
        
        from google.genai.types import GenerateContentConfig
        
        try:
            response = await self.ai_provider.client.aio.models.generate_content(
                model=self.ai_provider.model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResumeExtraction,
                    system_instruction="You are an expert technical recruiter."
                )
            )
            data = json.loads(response.text)
            extraction = ResumeExtraction(**data)
            json_str = response.text
        except Exception as e:
            logger.error(f"Failed to parse LLM extraction: {e}")
            raise

            
        # Update Profile
        await self.candidate_service.update_profile(
            user_id=user_id,
            profile_data=CandidateProfileUpdate(
                skills=extraction.skills,
                experience_years=extraction.experience_years,
                target_roles=extraction.target_roles
            )
        )
        
        # Create Memories
        for mem in extraction.memories:
            await self.candidate_service.upsert_memory(
                user_id=user_id,
                memory_type=mem.memory_type,
                content=mem.content,
                source="resume",
                confidence=0.8  # Resume facts have high initial confidence
            )
        
        # Save structured JSON in DB
        await self.doc_repo.update(doc_id, parsed_json=json_str)
