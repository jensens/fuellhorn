"""regroup_standard_categories

Revision ID: e5f1a9c3d2b8
Revises: c3a81f5b2e47
Create Date: 2026-10-04 20:00:00.000000

Daten: Neugruppierung der Standard-Kategorien (#456). Bestehende Daten dürfen
dabei nicht verfälscht werden, deshalb gilt für jeden Schritt:

- Nur Originalzustand ändern: Name, Gruppe, Farbe und Haltbarkeit werden nur
  angefasst, wenn sie noch exakt dem Seed-Stand vor #456 entsprechen.
- Kein Artikel wechselt die Kategorie. Wegfallende Kategorien werden nur gelöscht,
  wenn sie leer sind; belegte bleiben stehen und werden von Hand aufgeräumt.
- Kein Ablaufdatum ändert sich: Das Ablaufdatum wird aus der Haltbarkeit der
  Kategorie berechnet, ersatzweise aus der ihrer Gruppe (#395). Umhängen und das
  Entfernen einer Gruppen-Haltbarkeit unterbleiben, wenn belegte Kategorien
  dadurch eine andere Haltbarkeit erben würden.

Neue Kategorien und Gruppen (Milch, Sahne, Obst & Gemüse, Vorrat, ...) legt wie
bei #368 der Seed an (``fuellhorn seed shelf-life-defaults``), nicht die Migration.

Downgrade macht Umbenennungen, Umhängungen, Farben und die Gefrierzeit der
Milchprodukte nach denselben Regeln rückgängig. Gelöschte leere Kategorien
werden nicht wiederhergestellt (der alte Seed legt sie bei Bedarf neu an).
"""

from alembic import op
from collections.abc import Sequence
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f1a9c3d2b8"
down_revision: str | Sequence[str] | None = "c3a81f5b2e47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


STORAGE_TYPES = ("FROZEN", "CHILLED", "AMBIENT")

category = sa.table(
    "category",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("color", sa.String),
    sa.column("parent_id", sa.Integer),
)
shelf_life = sa.table(
    "category_shelf_life",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("storage_type", sa.Enum(*STORAGE_TYPES, name="storagetype")),
    sa.column("months_min", sa.Integer),
    sa.column("months_max", sa.Integer),
    sa.column("source_url", sa.String),
)
item = sa.table("item", sa.column("id", sa.Integer), sa.column("category_id", sa.Integer))

# Gruppen: alter Name -> neuer Name
RENAMES: list[tuple[str, str]] = [
    ("Fleisch", "Fleisch & Wurst"),
    ("Milchprodukte", "Milchprodukte & Eier"),
    ("Fruchtaufstriche", "Süßes Eingemachtes"),
    ("Würziges", "Würzsaucen"),
]

# Gefrierzeit der Milchprodukte-Gruppe: Frischkäse, Joghurt, Eier & Co. sollen sie nicht erben
DAIRY_GROUP = "Milchprodukte & Eier"
DAIRY_FROZEN = (2, 6, "https://verbraucherschutzzentrale.be/wie-lange-halten-lebensmittel-im-gefrierfach/")

# Kategorie, bisherige Gruppe (Name nach RENAMES), neue Gruppe
REPARENTS: list[tuple[str, str | None, str]] = [
    ("Sauerkraut", None, "Eingelegtes"),
    ("Antipasti", None, "Eingelegtes"),
    ("Fruchtsirup", None, "Süßes Eingemachtes"),
    ("Apfelmus", "Obstmus", "Süßes Eingemachtes"),
    ("Pflaumenmus", "Obstmus", "Süßes Eingemachtes"),
    ("Kompott", "Obstmus", "Süßes Eingemachtes"),
    ("Ketchup", "Soßen", "Würzsaucen"),
    ("Aufschnitt", None, "Fleisch & Wurst"),
    ("Eier", None, "Milchprodukte & Eier"),
    ("Milchprodukte (frisch)", None, "Milchprodukte & Eier"),
]

# Ersetzte Kategorien: nur löschen, wenn leer
OBSOLETE: list[str] = ["Obstmus", "Aufschnitt", "Milchprodukte (frisch)"]

# Kontrastarme Farben: Name (nach RENAMES), alte Farbe, neue Farbe
COLORS: list[tuple[str, str, str]] = [
    ("Butter", "#FFF9C4", "#F9A825"),
    ("Käse", "#FFE0B2", "#FFB74D"),
    ("Eier", "#FFF3E0", "#D4A373"),
    ("Milchprodukte & Eier", "#FFFFFF", "#78909C"),
]


def _category_id(conn: sa.Connection, name: str) -> int | None:
    return conn.execute(sa.select(category.c.id).where(category.c.name == name)).scalar()


def _parent_id(conn: sa.Connection, category_id: int) -> int | None:
    return conn.execute(sa.select(category.c.parent_id).where(category.c.id == category_id)).scalar()


def _shelf_life(conn: sa.Connection, category_id: int | None, storage_type: str) -> tuple[int, int] | None:
    if category_id is None:
        return None
    row = conn.execute(
        sa.select(shelf_life.c.months_min, shelf_life.c.months_max).where(
            shelf_life.c.category_id == category_id, shelf_life.c.storage_type == storage_type
        )
    ).first()
    return (row[0], row[1]) if row else None


def _has_items(conn: sa.Connection, category_id: int) -> bool:
    return conn.execute(sa.select(item.c.id).where(item.c.category_id == category_id).limit(1)).first() is not None


def _children(conn: sa.Connection, category_id: int) -> list[int]:
    return list(conn.execute(sa.select(category.c.id).where(category.c.parent_id == category_id)).scalars())


def _inheritance_unchanged(conn: sa.Connection, child_id: int, old_parent: int | None, new_parent: int | None) -> bool:
    """Erbt die Kategorie nach dem Umhängen für jeden Lagertyp dieselbe Haltbarkeit?"""
    for storage_type in STORAGE_TYPES:
        if _shelf_life(conn, child_id, storage_type) is not None:
            continue  # eigene Haltbarkeit, Gruppe egal
        if _shelf_life(conn, old_parent, storage_type) != _shelf_life(conn, new_parent, storage_type):
            return False
    return True


def _rename(conn: sa.Connection, old: str, new: str) -> None:
    old_id = _category_id(conn, old)
    if old_id is None or _category_id(conn, new) is not None or _parent_id(conn, old_id) is not None:
        return
    conn.execute(sa.update(category).where(category.c.id == old_id).values(name=new))


def _reparent(conn: sa.Connection, child: str, expected: str | None, target: str | None) -> None:
    child_id = _category_id(conn, child)
    if child_id is None:
        return
    expected_id = _category_id(conn, expected) if expected else None
    target_id = _category_id(conn, target) if target else None
    if expected and expected_id is None or target and target_id is None:
        return
    if _parent_id(conn, child_id) != expected_id:
        return  # vom Nutzer umgehängt
    if _has_items(conn, child_id) and not _inheritance_unchanged(conn, child_id, expected_id, target_id):
        return  # würde Ablaufdaten verschieben
    conn.execute(sa.update(category).where(category.c.id == child_id).values(parent_id=target_id))


def _group_frozen_is_inherited(conn: sa.Connection, group_id: int) -> bool:
    """Nutzt ein Artikel die Gefrierzeit der Gruppe (direkt oder geerbt)?"""
    if _has_items(conn, group_id):
        return True
    return any(
        _has_items(conn, child_id) and _shelf_life(conn, child_id, "FROZEN") is None
        for child_id in _children(conn, group_id)
    )


def _remove_dairy_frozen(conn: sa.Connection) -> None:
    group_id = _category_id(conn, DAIRY_GROUP)
    if group_id is None or _shelf_life(conn, group_id, "FROZEN") != DAIRY_FROZEN[:2]:
        return
    if _group_frozen_is_inherited(conn, group_id):
        return
    conn.execute(
        sa.delete(shelf_life).where(shelf_life.c.category_id == group_id, shelf_life.c.storage_type == "FROZEN")
    )


def _restore_dairy_frozen(conn: sa.Connection) -> None:
    group_id = _category_id(conn, DAIRY_GROUP)
    if group_id is None or _shelf_life(conn, group_id, "FROZEN") is not None:
        return
    if _group_frozen_is_inherited(conn, group_id):
        return
    months_min, months_max, source_url = DAIRY_FROZEN
    conn.execute(
        sa.insert(shelf_life).values(
            category_id=group_id,
            storage_type="FROZEN",
            months_min=months_min,
            months_max=months_max,
            source_url=source_url,
        )
    )


def _delete_if_empty(conn: sa.Connection, name: str) -> None:
    category_id = _category_id(conn, name)
    if category_id is None or _has_items(conn, category_id) or _children(conn, category_id):
        return
    conn.execute(sa.delete(shelf_life).where(shelf_life.c.category_id == category_id))
    conn.execute(sa.delete(category).where(category.c.id == category_id))


def _recolor(conn: sa.Connection, name: str, old: str, new: str) -> None:
    conn.execute(sa.update(category).where(category.c.name == name, category.c.color == old).values(color=new))


def upgrade() -> None:
    """Standard-Kategorien neu gruppieren, ohne Nutzerdaten oder Ablaufdaten zu verändern."""
    conn = op.get_bind()
    for old, new in RENAMES:
        _rename(conn, old, new)
    _remove_dairy_frozen(conn)
    for child, expected, target in REPARENTS:
        _reparent(conn, child, expected, target)
    for name in OBSOLETE:
        _delete_if_empty(conn, name)
    for name, old_color, new_color in COLORS:
        _recolor(conn, name, old_color, new_color)


def downgrade() -> None:
    """Umbenennungen, Umhängungen, Farben und Gefrierzeit nach denselben Regeln zurücknehmen."""
    conn = op.get_bind()
    for name, old_color, new_color in COLORS:
        _recolor(conn, name, new_color, old_color)
    for child, expected, target in reversed(REPARENTS):
        _reparent(conn, child, target, expected)
    _restore_dairy_frozen(conn)
    for old, new in reversed(RENAMES):
        _rename(conn, new, old)
