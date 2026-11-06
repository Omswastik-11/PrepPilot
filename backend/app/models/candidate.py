from sqlalchemy import Column, String, Integer, Text, Float, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.config import get_settings

settings = get_settings()

class CandidateProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "candidate_profiles"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    institute = Column(String(200), nullable=True)
    qualification = Column(String(200), nullable=True)
    target_roles = Column(ARRAY(String), nullable=True)
    target_companies = Column(ARRAY(String), nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(String(500), nullable=True)
    preferred_interview_types = Column(ARRAY(String), nullable=True)
    bio = Column(Text, nullable=True)
    preferred_tone = Column(String(50), default="professional", server_default="professional", nullable=False)

    user = relationship("User", backref="candidate_profile")

class CandidateMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "candidate_memories"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.5)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    interview_id = Column(ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="memories")
    interview = relationship("Interview", backref="memories")
