"""add_category_parent_id

Revision ID: 7fc1ce95c5b3
Revises: d34a94a28640
Create Date: 2026-02-07 16:58:32.271030

Schema: ``category.parent_id`` (selbstreferenzierender Fremdschlüssel) für die
einstufige Kategorie-Hierarchie (#351).

Daten: Bestehende Kinder werden ihren bereits vorhandenen Eltern zugeordnet und
das Duplikat "Konfitüre" geht in "Marmelade" auf. Neue Kategorien und
Haltbarkeiten legt die Migration bewusst nicht an (#368): Dafür braucht es
einen Benutzer für ``created_by`` (Helm führt ``migrate`` vor ``create-admin``
aus) und die Daten gehören nur an eine Stelle. Zuständig ist der idempotente
Seed ``fuellhorn seed shelf-life-defaults`` (``app/seed.py``), der auch die
Eltern der neuen Gruppen (Gekochtes, Fruchtaufstriche, Soßen, Würziges) setzt.
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence
from typing import Union


# revision identifiers, used by Alembic.
revision: str = "7fc1ce95c5b3"
down_revision: Union[str, Sequence[str], None] = "d34a94a28640"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Kinder, deren Eltern im alten Seed bereits als eigene Kategorie existierten.
# Zuordnung ausschließlich per Name; fehlende Kategorien werden übersprungen.
PARENT_CHILDREN: dict[str, list[str]] = {
    # FROZEN
    "Fleisch": ["Rindfleisch", "Schweinefleisch", "Geflügel", "Hackfleisch", "Wurst"],
    "Fisch": ["Fisch (mager)", "Fisch (fett)"],
    "Backwaren": ["Brot", "Kuchen"],
    "Milchprodukte": ["Butter", "Käse"],
    # AMBIENT
    "Obstmus": ["Apfelmus", "Pflaumenmus", "Kompott"],
    "Eingelegtes": ["Essiggurken", "Mixed Pickles"],
}

# Duplikate: alter Name -> Zielkategorie
OBSOLETE_CATEGORIES: dict[str, str] = {
    "Konfitüre": "Marmelade",
}


def _get_category_id(conn: sa.Connection, name: str) -> int | None:
    result = conn.execute(sa.text("SELECT id FROM category WHERE name = :name"), {"name": name})
    row = result.fetchone()
    return row[0] if row else None


def _assign_existing_children(conn: sa.Connection) -> None:
    for parent_name, children in PARENT_CHILDREN.items():
        parent_id = _get_category_id(conn, parent_name)
        if parent_id is None:
            continue
        for child_name in children:
            conn.execute(
                sa.text("UPDATE category SET parent_id = :pid WHERE name = :name AND id != :pid"),
                {"pid": parent_id, "name": child_name},
            )


def _merge_obsolete_categories(conn: sa.Connection) -> None:
    for old_name, new_name in OBSOLETE_CATEGORIES.items():
        old_id = _get_category_id(conn, old_name)
        if old_id is None:
            continue
        new_id = _get_category_id(conn, new_name)
        if new_id is None:
            # Ziel fehlt: umbenennen, Artikel und Haltbarkeiten bleiben erhalten
            conn.execute(
                sa.text("UPDATE category SET name = :new_name WHERE id = :old_id"),
                {"new_name": new_name, "old_id": old_id},
            )
            continue
        conn.execute(
            sa.text("UPDATE item SET category_id = :new_id WHERE category_id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )
        conn.execute(
            sa.text("UPDATE category SET parent_id = :new_id WHERE parent_id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )
        conn.execute(
            sa.text("DELETE FROM category_shelf_life WHERE category_id = :old_id"),
            {"old_id": old_id},
        )
        conn.execute(sa.text("DELETE FROM category WHERE id = :old_id"), {"old_id": old_id})


def upgrade() -> None:
    """Spalte parent_id anlegen, bestehende Kategorien zuordnen, Duplikate zusammenführen."""
    # Batch-Modus: SQLite kann Fremdschlüssel nicht per ALTER TABLE ergänzen
    with op.batch_alter_table("category") as batch_op:
        batch_op.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_category_parent", "category", ["parent_id"], ["id"])

    conn = op.get_bind()
    _assign_existing_children(conn)
    _merge_obsolete_categories(conn)


def downgrade() -> None:
    """Spalte parent_id entfernen (Zusammenführung von Duplikaten bleibt bestehen)."""
    with op.batch_alter_table("category") as batch_op:
        batch_op.drop_constraint("fk_category_parent", type_="foreignkey")
        batch_op.drop_column("parent_id")
