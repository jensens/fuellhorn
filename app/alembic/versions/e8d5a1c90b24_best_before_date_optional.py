"""best_before_date_optional

Revision ID: e8d5a1c90b24
Revises: e5f1a9c3d2b8
Create Date: 2026-10-04 20:00:00.000000

Issue #463: Die Schnellerfassung im Keller kennt nur Ort, Name, Menge, Einheit und Typ.
Das Datum wird später nachgepflegt, also muss die Spalte leer bleiben dürfen. Artikel
ohne Datum zeigen den schon vorhandenen Status „Keine Haltbarkeitsdaten“.

Der Rückweg setzt die Spalte wieder auf NOT NULL; das schlägt fehl, solange Artikel
ohne Datum existieren. Diese müssten vorher ein Datum bekommen oder gelöscht werden.
"""

from alembic import op
from collections.abc import Sequence
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8d5a1c90b24"
down_revision: str | Sequence[str] | None = "e5f1a9c3d2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: SQLite baut die Tabelle neu, PostgreSQL macht ein normales ALTER
    with op.batch_alter_table("item") as batch_op:
        batch_op.alter_column("best_before_date", existing_type=sa.Date(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("item") as batch_op:
        batch_op.alter_column("best_before_date", existing_type=sa.Date(), nullable=False)
