"""add sort_order to category

Revision ID: 86ddeb1af50f
Revises: 094bc98ee7ff
Create Date: 2025-11-30 19:23:09.369029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86ddeb1af50f'
down_revision: Union[str, Sequence[str], None] = '094bc98ee7ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add sort_order column with server default for existing rows
    op.add_column(
        'category',
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('category', 'sort_order')
