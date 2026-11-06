"""merge

Revision ID: c572bee71c40
Revises: c1a2e3f45678, d2a3b4c5d6e7
Create Date: 2026-09-03 18:46:49.175003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c572bee71c40'
down_revision: Union[str, None] = ('c1a2e3f45678', 'd2a3b4c5d6e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
