"""remove expiry_date and item_category

Revision ID: 094bc98ee7ff
Revises: cc65fe88891e
Create Date: 2025-11-28 15:42:58.913000

Schema changes:
- Remove expiry_date from item table (calculated dynamically now)
- Drop item_category junction table (replaced by direct category_id on item)
- Remove freeze_time_months from category table (replaced by category_shelf_life)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '094bc98ee7ff'
down_revision: Union[str, Sequence[str], None] = 'cc65fe88891e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add category_id column to item table if not exists
    with op.batch_alter_table('item') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_item_category_id',
            'category',
            ['category_id'],
            ['id']
        )

    # 2. Migrate data from item_category to item.category_id
    # Get connection for data migration
    conn = op.get_bind()

    # Copy category_id from item_category to item
    # (taking first category if multiple exist for an item)
    conn.execute(sa.text("""
        UPDATE item
        SET category_id = (
            SELECT category_id
            FROM item_category
            WHERE item_category.item_id = item.id
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM item_category WHERE item_category.item_id = item.id
        )
    """))

    # 3. Drop item_category junction table
    op.drop_table('item_category')

    # 4. Drop expiry_date column from item table
    with op.batch_alter_table('item') as batch_op:
        batch_op.drop_column('expiry_date')

    # 5. Drop freeze_time_months column from category table
    with op.batch_alter_table('category') as batch_op:
        batch_op.drop_column('freeze_time_months')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Add freeze_time_months back to category
    with op.batch_alter_table('category') as batch_op:
        batch_op.add_column(sa.Column('freeze_time_months', sa.Integer(), nullable=True))

    # 2. Add expiry_date back to item
    with op.batch_alter_table('item') as batch_op:
        batch_op.add_column(sa.Column('expiry_date', sa.Date(), nullable=True))

    # Update expiry_date to best_before_date as default
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE item SET expiry_date = best_before_date"))

    # Make expiry_date not nullable
    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('expiry_date', nullable=False)

    # 3. Recreate item_category junction table
    op.create_table(
        'item_category',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['category.id']),
        sa.ForeignKeyConstraint(['item_id'], ['item.id']),
        sa.PrimaryKeyConstraint('item_id', 'category_id'),
    )

    # 4. Migrate data from item.category_id to item_category
    conn.execute(sa.text("""
        INSERT INTO item_category (item_id, category_id)
        SELECT id, category_id FROM item WHERE category_id IS NOT NULL
    """))

    # 5. Drop category_id column from item
    with op.batch_alter_table('item') as batch_op:
        batch_op.drop_constraint('fk_item_category_id', type_='foreignkey')
        batch_op.drop_column('category_id')
