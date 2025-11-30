"""merge heads

Revision ID: 83f2c87ee2a6
Revises: 86ddeb1af50f, b404d025312d
Create Date: 2025-11-30 20:25:44.807785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83f2c87ee2a6'
down_revision: Union[str, Sequence[str], None] = ('86ddeb1af50f', 'b404d025312d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
