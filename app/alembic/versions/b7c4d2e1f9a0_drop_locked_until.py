"""drop_locked_until

Revision ID: b7c4d2e1f9a0
Revises: 6a96c7f23335
Create Date: 2026-10-04 16:00:00.000000

Issue #402: ``users.locked_until`` (manuelles Admin-Lock) hatte keinen Schreiber
und keine UI; Deaktivieren über ``is_active`` deckt den Anwendungsfall ab.
"""

from alembic import op
from collections.abc import Sequence
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c4d2e1f9a0"
down_revision: str | Sequence[str] | None = "6a96c7f23335"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: SQLite baut die Tabelle neu, PostgreSQL macht normale ALTERs
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("locked_until")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(), nullable=True))
