"""Migrationstests für 7fc1ce95c5b3 (Kategorie-Hierarchie, Issue #368).

Alembic läuft gegen eine echte Datenbank: zuerst bis zum Initialschema, dann
Bestandsdaten im alten Format (flache Kategorien, Enum-NAMEN in
``category_shelf_life.storage_type``), dann ``upgrade head``. Danach muss das
ORM alle Tabellen lesen können und die Daten müssen erhalten sein.

Standard ist eine SQLite-Datei im Temp-Verzeichnis. Mit
``MIGRATION_TEST_DATABASE_URL=postgresql://user:pass@host:port/db`` laufen
dieselben Tests gegen PostgreSQL (die Datenbank wird dabei geleert).
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import StorageType
from app.models import User
from datetime import date
from datetime import datetime
from pathlib import Path
import sqlalchemy as sa
from sqlmodel import Session
from sqlmodel import select


INITIAL_REVISION = "d34a94a28640"
PARENT_ID_REVISION = "7fc1ce95c5b3"
MIGRATION_FILE = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "alembic"
    / "versions"
    / f"{PARENT_ID_REVISION}_add_category_parent_id.py"
)

NOW = datetime(2026, 1, 1, 12, 0, 0)

# Leichtgewichtige Tabellenobjekte für dialektneutrale INSERTs (SQLite und PostgreSQL).
# Enum-Spalten brauchen den Enum-Typ, sonst schickt psycopg VARCHAR und PostgreSQL lehnt ab.
storage_type_enum = sa.Enum("FROZEN", "CHILLED", "AMBIENT", name="storagetype")
location_type_enum = sa.Enum("FROZEN", "CHILLED", "AMBIENT", name="locationtype")
item_type_enum = sa.Enum(
    "PURCHASED_FRESH",
    "PURCHASED_FROZEN",
    "PURCHASED_THEN_FROZEN",
    "HOMEMADE_FROZEN",
    "HOMEMADE_PRESERVED",
    name="itemtype",
)
users_table = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
    sa.column("password_hash", sa.String),
    sa.column("email", sa.String),
    sa.column("role", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)
category_table = sa.table(
    "category",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("sort_order", sa.Integer),
    sa.column("created_at", sa.DateTime),
    sa.column("created_by", sa.Integer),
)
shelf_life_table = sa.table(
    "category_shelf_life",
    sa.column("category_id", sa.Integer),
    sa.column("storage_type", storage_type_enum),
    sa.column("months_min", sa.Integer),
    sa.column("months_max", sa.Integer),
)
location_table = sa.table(
    "location",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("location_type", location_type_enum),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
    sa.column("created_by", sa.Integer),
)
item_table = sa.table(
    "item",
    sa.column("id", sa.Integer),
    sa.column("product_name", sa.String),
    sa.column("best_before_date", sa.Date),
    sa.column("quantity", sa.Float),
    sa.column("unit", sa.String),
    sa.column("item_type", item_type_enum),
    sa.column("location_id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("is_consumed", sa.Boolean),
    sa.column("created_at", sa.DateTime),
    sa.column("created_by", sa.Integer),
)


def _insert_legacy_data(engine: sa.Engine, *, with_marmelade: bool = True) -> None:
    """Bestandsdaten, wie sie der alte Seed vor der Hierarchie angelegt hat."""
    categories = [(1, "Fleisch"), (2, "Hackfleisch"), (4, "Konfitüre"), (5, "Gemüse")]
    shelf_lives = [(1, "FROZEN"), (2, "FROZEN"), (4, "AMBIENT"), (5, "FROZEN")]
    if with_marmelade:
        categories.append((3, "Marmelade"))
        shelf_lives.append((3, "AMBIENT"))

    with engine.begin() as conn:
        conn.execute(
            users_table.insert().values(
                id=1,
                username="admin",
                password_hash="hash",
                email="admin@test.local",
                role="admin",
                is_active=True,
                created_at=NOW,
            )
        )
        conn.execute(
            category_table.insert(),
            [
                {"id": cat_id, "name": name, "sort_order": 0, "created_at": NOW, "created_by": 1}
                for cat_id, name in categories
            ],
        )
        conn.execute(
            shelf_life_table.insert(),
            [
                {"category_id": cat_id, "storage_type": storage_type, "months_min": 6, "months_max": 12}
                for cat_id, storage_type in shelf_lives
            ],
        )
        conn.execute(
            location_table.insert().values(
                id=1, name="Keller", location_type="AMBIENT", is_active=True, created_at=NOW, created_by=1
            )
        )
        conn.execute(
            item_table.insert().values(
                id=1,
                product_name="Erdbeerkonfitüre",
                best_before_date=date(2026, 6, 30),
                quantity=1.0,
                unit="Glas",
                item_type="HOMEMADE_PRESERVED",
                location_id=1,
                category_id=4,
                is_consumed=False,
                created_at=NOW,
                created_by=1,
            )
        )


def _upgrade_with_legacy_data(cfg: AlembicConfig, engine: sa.Engine, target: str = "head", **kwargs: bool) -> None:
    command.upgrade(cfg, INITIAL_REVISION)
    _insert_legacy_data(engine, **kwargs)
    command.upgrade(cfg, target)


def test_upgrade_keeps_shelf_lives_readable_by_orm(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Nach der Migration liest das ORM alle Haltbarkeiten ohne LookupError."""
    cfg, engine = migration_db
    _upgrade_with_legacy_data(cfg, engine)

    with Session(engine) as session:
        shelf_lives = session.exec(select(CategoryShelfLife)).all()

    assert len(shelf_lives) >= 4
    assert {sl.storage_type for sl in shelf_lives} <= set(StorageType)


def test_upgrade_assigns_existing_children_to_existing_parents(
    migration_db: tuple[AlembicConfig, sa.Engine],
) -> None:
    """Hackfleisch hängt nach der Migration unter Fleisch, Gemüse bleibt eigenständig."""
    cfg, engine = migration_db
    # nur bis zu dieser Revision: #456 benennt Fleisch später um
    _upgrade_with_legacy_data(cfg, engine, PARENT_ID_REVISION)

    with Session(engine) as session:
        by_name = {c.name: c for c in session.exec(select(Category)).all()}

    assert by_name["Hackfleisch"].parent_id == by_name["Fleisch"].id
    assert by_name["Fleisch"].parent_id is None
    assert by_name["Gemüse"].parent_id is None


def test_upgrade_merges_konfituere_into_marmelade(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Artikel von Konfitüre wandern zu Marmelade, Konfitüre und ihre Haltbarkeit verschwinden."""
    cfg, engine = migration_db
    _upgrade_with_legacy_data(cfg, engine)

    with Session(engine) as session:
        by_name = {c.name: c for c in session.exec(select(Category)).all()}
        item = session.exec(select(Item)).one()
        orphan_shelf_lives = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == 4)).all()

    assert "Konfitüre" not in by_name
    assert item.category_id == by_name["Marmelade"].id
    assert orphan_shelf_lives == []


def test_upgrade_renames_konfituere_when_marmelade_is_missing(
    migration_db: tuple[AlembicConfig, sa.Engine],
) -> None:
    """Gibt es keine Marmelade, wird Konfitüre umbenannt statt gelöscht (Artikel und Haltbarkeit bleiben)."""
    cfg, engine = migration_db
    _upgrade_with_legacy_data(cfg, engine, with_marmelade=False)

    with Session(engine) as session:
        by_name = {c.name: c for c in session.exec(select(Category)).all()}
        item = session.exec(select(Item)).one()
        shelf_lives = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == 4)).all()

    assert "Konfitüre" not in by_name
    assert by_name["Marmelade"].id == 4
    assert item.category_id == 4
    assert len(shelf_lives) == 1


def test_upgrade_never_creates_rows_for_missing_users(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Auf einer leeren Datenbank (Helm: migrate läuft vor create-admin) entstehen keine Waisen mit created_by=1."""
    cfg, engine = migration_db
    command.upgrade(cfg, "head")

    with Session(engine) as session:
        users = session.exec(select(User)).all()
        categories = session.exec(select(Category)).all()
        shelf_lives = session.exec(select(CategoryShelfLife)).all()

    assert users == []
    assert categories == []
    assert shelf_lives == []


def test_downgrade_removes_parent_id_column(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """``downgrade -1`` läuft mit Bestandsdaten fehlerfrei durch und entfernt parent_id."""
    cfg, engine = migration_db
    _upgrade_with_legacy_data(cfg, engine)

    command.downgrade(cfg, INITIAL_REVISION)

    columns = {column["name"] for column in sa.inspect(engine).get_columns("category")}
    assert "parent_id" not in columns


def test_migration_uses_no_sqlite_only_sql_and_no_lowercase_enum_values() -> None:
    """Akzeptanzkriterium aus #368: kein datetime('now'), keine Enum-WERTE statt -NAMEN."""
    source = MIGRATION_FILE.read_text(encoding="utf-8")

    assert "datetime('now')" not in source
    assert "'frozen'" not in source
    assert "'ambient'" not in source
