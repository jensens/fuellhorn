"""add color field to location

Revision ID: 5a895943927c
Revises: 094bc98ee7ff
Create Date: 2025-11-30 19:30:13.853980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a895943927c'
down_revision: Union[str, Sequence[str], None] = '094bc98ee7ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('location', sa.Column('color', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('location', 'color')
