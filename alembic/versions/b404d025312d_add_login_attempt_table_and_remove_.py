"""add login_attempt table and remove failed_login_attempts

Revision ID: b404d025312d
Revises: 094bc98ee7ff
Create Date: 2025-11-30 19:28:58.156482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b404d025312d'
down_revision: Union[str, Sequence[str], None] = '094bc98ee7ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create login_attempt table for IP-based rate limiting
    op.create_table('login_attempt',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('fail_count', sa.Integer(), nullable=False),
    sa.Column('last_attempt', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_attempt_ip_address'), 'login_attempt', ['ip_address'], unique=False)

    # Remove failed_login_attempts from users table (now IP-based)
    op.drop_column('users', 'failed_login_attempts')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add failed_login_attempts to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))

    # Drop login_attempt table
    op.drop_index(op.f('ix_login_attempt_ip_address'), table_name='login_attempt')
    op.drop_table('login_attempt')
