"""drop freeze_time_config table

Revision ID: cc65fe88891e
Revises: c800634c7cf4
Create Date: 2025-11-28 10:57:43.443312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'cc65fe88891e'
down_revision: Union[str, Sequence[str], None] = 'c800634c7cf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create category_shelf_life table (new shelf life configuration)
    op.create_table('category_shelf_life',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('storage_type', sa.Enum('FROZEN', 'CHILLED', 'AMBIENT', name='storagetype'), nullable=False),
        sa.Column('months_min', sa.Integer(), nullable=False),
        sa.Column('months_max', sa.Integer(), nullable=False),
        sa.Column('source_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'storage_type', name='uq_category_storage')
    )

    # Drop old freeze_time_config table
    op.drop_table('freeze_time_config')

    # Add category_id column to item table (for primary category)
    op.add_column('item', sa.Column('category_id', sa.Integer(), nullable=True))

    # Note: SQLite doesn't support adding foreign keys to existing tables without
    # recreating the table. The foreign key will be enforced at the application level.
    # For PostgreSQL in production, the foreign key constraint would be added here.


def downgrade() -> None:
    """Downgrade schema."""
    # Remove category_id column from item
    op.drop_column('item', 'category_id')

    # Recreate freeze_time_config table
    op.create_table('freeze_time_config',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('category_id', sa.INTEGER(), nullable=True),
        sa.Column('item_type', sa.VARCHAR(length=21), nullable=False),
        sa.Column('freeze_time_months', sa.INTEGER(), nullable=False),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.Column('created_by', sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'item_type', name='uq_category_item_type')
    )

    # Drop category_shelf_life table
    op.drop_table('category_shelf_life')
