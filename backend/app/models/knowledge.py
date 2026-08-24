from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.config import get_settings

settings = get_settings()

class KnowledgeSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_sources"
    
    source_type = Column(String(50), nullable=False) # url, document, manual
    reference = Column(String(500), nullable=False)  # URL or title
    content = Column(Text, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    status = Column(String(50), nullable=False, server_default='discovered') # discovered, processed, failed

    __table_args__ = (
        UniqueConstraint('reference', name='uq_knowledge_source_reference'),
    )

class QuestionBank(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "question_bank"
    
    domain = Column(String(100), nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    expected_key_points = Column(Text, nullable=True)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    knowledge_source_id = Column(ForeignKey("knowledge_sources.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, server_default='pending_review') # pending_review, accepted, rejected

    source = relationship("KnowledgeSource")
