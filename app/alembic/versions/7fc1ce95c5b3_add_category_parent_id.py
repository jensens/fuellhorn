"""add_category_parent_id

Revision ID: 7fc1ce95c5b3
Revises: d34a94a28640
Create Date: 2026-02-07 16:58:32.271030

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


# Parent-child relationships for existing categories
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

# New parent categories to create (with shelf-life data)
# Format: (name, color, storage_type, months_min, months_max, children)
NEW_PARENTS: list[tuple[str, str, str, int, int, list[str]]] = [
    ("Gekochtes", "#8D6E63", "frozen", 2, 3, ["Suppen", "Eintöpfe", "Fertiggerichte"]),
    ("Fruchtaufstriche", "#E91E63", "ambient", 12, 24, ["Marmelade", "Gelee"]),
    ("Soßen", "#EF5350", "ambient", 6, 12, ["Tomatensoße", "Sugo", "Ketchup", "Pesto"]),
    ("Würziges", "#FF7043", "ambient", 3, 12, ["Chutney", "Relish", "Senf"]),
]

# New leaf categories (with shelf-life)
# Format: (name, color, parent_name, storage_type, months_min, months_max)
NEW_LEAF_CATEGORIES: list[tuple[str, str, str, str, int, int]] = [
    ("Meeresfrüchte", "#0097A7", "Fisch", "frozen", 2, 4),
]

# New categories without shelf-life (for PURCHASED_FRESH)
# Format: (name, color)
FRESH_ONLY_CATEGORIES: list[tuple[str, str]] = [
    ("Nudeln & Pasta", "#FFCC80"),
    ("Reis & Getreide", "#D7CCC8"),
    ("Backzutaten", "#FFECB3"),
    ("Konserven", "#90A4AE"),
    ("Gewürze", "#A1887F"),
    ("Öle & Essig", "#C8E6C9"),
    ("Getränke", "#81D4FA"),
    ("Snacks", "#FFE082"),
    ("Eier", "#FFF3E0"),
    ("Aufschnitt", "#FFAB91"),
    ("Milchprodukte (frisch)", "#E1BEE7"),
]


def _get_connection() -> sa.Connection:
    return op.get_bind()


def _get_category_id(conn: sa.Connection, name: str) -> int | None:
    result = conn.execute(sa.text("SELECT id FROM category WHERE name = :name"), {"name": name})
    row = result.fetchone()
    return row[0] if row else None


def _get_system_user_id(conn: sa.Connection) -> int:
    result = conn.execute(sa.text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
    row = result.fetchone()
    if row:
        return row[0]
    result = conn.execute(sa.text("SELECT id FROM users LIMIT 1"))
    row = result.fetchone()
    if row:
        return row[0]
    return 1


def _create_category(conn: sa.Connection, name: str, color: str, user_id: int) -> int:
    existing_id = _get_category_id(conn, name)
    if existing_id is not None:
        return existing_id
    conn.execute(
        sa.text(
            "INSERT INTO category (name, color, sort_order, created_at, created_by) "
            "VALUES (:name, :color, 0, datetime('now'), :user_id)"
        ),
        {"name": name, "color": color, "user_id": user_id},
    )
    return _get_category_id(conn, name)  # type: ignore[return-value]


def _create_shelf_life(
    conn: sa.Connection, category_id: int, storage_type: str, months_min: int, months_max: int
) -> None:
    result = conn.execute(
        sa.text("SELECT id FROM category_shelf_life WHERE category_id = :cat_id AND storage_type = :st"),
        {"cat_id": category_id, "st": storage_type},
    )
    if result.fetchone():
        return
    conn.execute(
        sa.text(
            "INSERT INTO category_shelf_life (category_id, storage_type, months_min, months_max) "
            "VALUES (:cat_id, :st, :min, :max)"
        ),
        {"cat_id": category_id, "st": storage_type, "min": months_min, "max": months_max},
    )


def upgrade() -> None:
    """Upgrade schema and migrate seed data."""
    # Schema change
    op.add_column("category", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_category_parent", "category", "category", ["parent_id"], ["id"])

    # Data migration
    conn = _get_connection()
    user_id = _get_system_user_id(conn)

    # 1. Set parent_id for existing categories
    for parent_name, children in PARENT_CHILDREN.items():
        parent_id = _get_category_id(conn, parent_name)
        if parent_id is None:
            continue
        for child_name in children:
            child_id = _get_category_id(conn, child_name)
            if child_id is not None:
                conn.execute(
                    sa.text("UPDATE category SET parent_id = :pid WHERE id = :cid"),
                    {"pid": parent_id, "cid": child_id},
                )

    # 2. Create new parent categories with shelf-life and assign children
    for name, color, storage_type, months_min, months_max, children in NEW_PARENTS:
        parent_id = _create_category(conn, name, color, user_id)
        _create_shelf_life(conn, parent_id, storage_type, months_min, months_max)
        for child_name in children:
            child_id = _get_category_id(conn, child_name)
            if child_id is not None:
                conn.execute(
                    sa.text("UPDATE category SET parent_id = :pid WHERE id = :cid"),
                    {"pid": parent_id, "cid": child_id},
                )

    # 3. Create new leaf categories with shelf-life
    for name, color, parent_name, storage_type, months_min, months_max in NEW_LEAF_CATEGORIES:
        parent_id = _get_category_id(conn, parent_name)
        cat_id = _create_category(conn, name, color, user_id)
        if parent_id is not None:
            conn.execute(
                sa.text("UPDATE category SET parent_id = :pid WHERE id = :cid"),
                {"pid": parent_id, "cid": cat_id},
            )
        _create_shelf_life(conn, cat_id, storage_type, months_min, months_max)

    # 4. Create FRESH-only categories (no shelf-life, no parent)
    for name, color in FRESH_ONLY_CATEGORIES:
        _create_category(conn, name, color, user_id)

    # 5. Remove Konfitüre: reassign items to Marmelade, then delete
    konfituere_id = _get_category_id(conn, "Konfitüre")
    marmelade_id = _get_category_id(conn, "Marmelade")
    if konfituere_id is not None and marmelade_id is not None:
        conn.execute(
            sa.text("UPDATE item SET category_id = :mid WHERE category_id = :kid"),
            {"mid": marmelade_id, "kid": konfituere_id},
        )
        conn.execute(
            sa.text("DELETE FROM category_shelf_life WHERE category_id = :kid"),
            {"kid": konfituere_id},
        )
        conn.execute(
            sa.text("DELETE FROM category WHERE id = :kid"),
            {"kid": konfituere_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_category_parent", "category", type_="foreignkey")
    op.drop_column("category", "parent_id")
