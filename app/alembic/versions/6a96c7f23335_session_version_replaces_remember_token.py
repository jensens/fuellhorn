"""session_version_replaces_remember_token

Revision ID: 6a96c7f23335
Revises: 7fc1ce95c5b3
Create Date: 2026-10-04 14:00:00.000000

Issue #384: Das Remember-Me-Token wurde nie zurückgelesen. An seine Stelle tritt
``users.session_version``: Jede Passwortänderung erhöht die Version, Sitzungen
mit alter Version werden beim nächsten Request abgemeldet. Bestehende Benutzer
starten mit Version 0.
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence
from typing import Union


# revision identifiers, used by Alembic.
revision: str = "6a96c7f23335"
down_revision: Union[str, Sequence[str], None] = "7fc1ce95c5b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table: SQLite baut die Tabelle neu, PostgreSQL macht normale ALTERs
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
        batch_op.drop_column("remember_token")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("remember_token", sa.String(), nullable=True))
        batch_op.drop_column("session_version")
