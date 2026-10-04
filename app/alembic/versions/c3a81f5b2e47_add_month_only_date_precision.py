"""add_month_only_date_precision

Revision ID: c3a81f5b2e47
Revises: b7c4d2e1f9a0
Create Date: 2026-10-04 18:00:00.000000

Issue #347: MHD und Einmachdaten sind oft nur monatsgenau bekannt. Gespeichert wird
weiterhin ein echtes Datum, nämlich der 1. des Monats; die beiden Kennzeichen halten
fest, dass der Tag nicht erfasst wurde. Bestehende Artikel bleiben tagesgenau.
"""

from alembic import op
from collections.abc import Sequence
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3a81f5b2e47"
down_revision: str | Sequence[str] | None = "b7c4d2e1f9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: SQLite baut die Tabelle neu, PostgreSQL macht normale ALTERs
    with op.batch_alter_table("item") as batch_op:
        batch_op.add_column(
            sa.Column("best_before_month_only", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column("freeze_date_month_only", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("item") as batch_op:
        batch_op.drop_column("freeze_date_month_only")
        batch_op.drop_column("best_before_month_only")
