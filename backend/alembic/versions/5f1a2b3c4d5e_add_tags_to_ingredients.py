"""add tags column to ingredients

Revision ID: 5f1a2b3c4d5e
Revises: 4e8f033ff937
Create Date: 2026-05-30 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f1a2b3c4d5e'
down_revision: Union[str, None] = '4e8f033ff937'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('tags', sa.JSON(), nullable=False, server_default='[]')
        )


def downgrade() -> None:
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.drop_column('tags')
