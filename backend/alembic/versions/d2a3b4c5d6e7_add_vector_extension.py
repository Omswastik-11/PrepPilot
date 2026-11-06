"""add_vector_extension

Revision ID: d2a3b4c5d6e7
Revises: ebaaf4083004
Create Date: 2026-09-03 17:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd2a3b4c5d6e7'
down_revision: Union[str, None] = 'ebaaf4083004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
