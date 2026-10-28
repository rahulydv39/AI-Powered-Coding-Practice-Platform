"""add_index_on_submissions_created_at

Revision ID: 53cf65bd103f
Revises: dea036f5600f
Create Date: 2026-10-27 21:40:09.280770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53cf65bd103f'
down_revision: Union[str, None] = 'dea036f5600f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_submissions_created_at'), 'submissions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_submissions_created_at'), table_name='submissions')
