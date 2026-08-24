from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    content = Column(Text, nullable=False)          # Extracted raw text
    parsed_json = Column(Text, nullable=True)       # LLM structured output
    status = Column(String(50), nullable=False, default="pending")  # pending, processed, failed
    error_message = Column(Text, nullable=True)

    user = relationship("User", backref="documents")
