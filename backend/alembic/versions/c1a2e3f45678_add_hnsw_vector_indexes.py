"""add hnsw vector indexes

Revision ID: c1a2e3f45678
Revises: b6a1d9303b08
Create Date: 2026-09-03 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2e3f45678'
down_revision: Union[str, None] = 'b6a1d9303b08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create HNSW indexes on vector embeddings for fast approximate nearest neighbor search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_question_bank_embedding_hnsw "
        "ON question_bank USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_candidate_memories_embedding_hnsw "
        "ON candidate_memories USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_candidate_memories_embedding_hnsw;")
    op.execute("DROP INDEX IF EXISTS ix_question_bank_embedding_hnsw;")
