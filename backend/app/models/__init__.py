"""
PrepPilot Models Package — Model Registry.

ENGINEERING PATTERN:
  This __init__.py serves as a "model registry." By importing all models
  here, any code can do:

    from app.models import User, Interview, Question, Answer

  Instead of:

    from app.models.user import User
    from app.models.interview import Interview
    from app.models.question import Question, Answer

  More importantly, this ensures Alembic can discover ALL models by
  importing this single package. Without this, you'd need to manually
  import each model in alembic/env.py — and forgetting one means
  Alembic won't generate migrations for it.

  The Base class is also re-exported here for convenience.
"""

from app.models.base import Base
from app.models.user import User
from app.models.interview import Interview
from app.models.question import Question, Answer
from app.models.candidate import CandidateProfile, CandidateMemory
from app.models.document import Document
from app.models.knowledge import KnowledgeSource, QuestionBank

__all__ = [
    "Base", "User", "Interview", "Question", "Answer",
    "CandidateProfile", "CandidateMemory", "Document",
    "KnowledgeSource", "QuestionBank"
]
