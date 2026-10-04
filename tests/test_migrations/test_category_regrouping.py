"""Migrationstests für die Neugruppierung der Standard-Kategorien (Issue #456).

Ausgangslage ist der Datenstand des Seeds vor #456. Die Migration darf nur Werte im
unveränderten Originalzustand anfassen, keinen Artikel umhängen und kein berechnetes
Ablaufdatum verändern.
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import StorageType
from app.models import User
from app.models.item import ItemType
from app.models.location import Location
from app.models.location import LocationType
from app.seed import seed_shelf_life_defaults
from app.services import category_service
from app.services.expiry_service import ExpiryView
from app.services.expiry_service import get_expiry_views
from collections.abc import Callable
from datetime import date
import sqlalchemy as sa
from sqlmodel import Session
from sqlmodel import select
from tests.test_services.test_seed_category_structure import EXPECTED_GROUPS


PREVIOUS_REVISION = "c3a81f5b2e47"
TODAY = date(2026, 10, 4)

# Seed-Stand vor #456 (aus app/seed.py, origin/main b4714c1): (Name, Farbe, Gruppe, [(Lagertyp, min, max)])
OLD_SEED: list[tuple[str, str, str | None, list[tuple[str, int, int]]]] = [
    ("Gemüse", "#4CAF50", None, [("FROZEN", 6, 12)]),
    ("Kräuter", "#8BC34A", None, [("FROZEN", 3, 4)]),
    ("Obst", "#FF9800", None, [("FROZEN", 9, 12)]),
    ("Fleisch", "#F44336", None, [("FROZEN", 3, 12)]),
    ("Rindfleisch", "#D32F2F", "Fleisch", [("FROZEN", 9, 12)]),
    ("Schweinefleisch", "#E57373", "Fleisch", [("FROZEN", 4, 7)]),
    ("Geflügel", "#FFEB3B", "Fleisch", [("FROZEN", 3, 12)]),
    ("Hackfleisch", "#C62828", "Fleisch", [("FROZEN", 1, 3)]),
    ("Wurst", "#795548", "Fleisch", [("FROZEN", 1, 6)]),
    ("Fisch", "#2196F3", None, [("FROZEN", 2, 4)]),
    ("Fisch (mager)", "#64B5F6", "Fisch", [("FROZEN", 4, 6)]),
    ("Fisch (fett)", "#1976D2", "Fisch", [("FROZEN", 2, 3)]),
    ("Meeresfrüchte", "#0097A7", "Fisch", [("FROZEN", 2, 4)]),
    ("Backwaren", "#FFC107", None, [("FROZEN", 1, 3)]),
    ("Brot", "#FFE082", "Backwaren", [("FROZEN", 1, 3)]),
    ("Kuchen", "#FF80AB", "Backwaren", [("FROZEN", 2, 4)]),
    ("Milchprodukte", "#FFFFFF", None, [("FROZEN", 2, 6)]),
    ("Butter", "#FFF9C4", "Milchprodukte", [("FROZEN", 6, 8)]),
    ("Käse", "#FFE0B2", "Milchprodukte", [("FROZEN", 2, 4)]),
    ("Gekochtes", "#8D6E63", None, [("FROZEN", 2, 3)]),
    ("Suppen", "#FFCCBC", "Gekochtes", [("FROZEN", 2, 3)]),
    ("Eintöpfe", "#BCAAA4", "Gekochtes", [("FROZEN", 2, 3)]),
    ("Fertiggerichte", "#9E9E9E", "Gekochtes", [("FROZEN", 2, 3)]),
    ("Fruchtaufstriche", "#E91E63", None, [("AMBIENT", 12, 24)]),
    ("Marmelade", "#C2185B", "Fruchtaufstriche", [("AMBIENT", 12, 24)]),
    ("Gelee", "#CE93D8", "Fruchtaufstriche", [("AMBIENT", 12, 24)]),
    ("Obstmus", "#FF8A65", None, [("AMBIENT", 12, 18)]),
    ("Apfelmus", "#A5D6A7", "Obstmus", [("AMBIENT", 12, 18)]),
    ("Pflaumenmus", "#7E57C2", "Obstmus", [("AMBIENT", 12, 18)]),
    ("Kompott", "#FFAB91", "Obstmus", [("AMBIENT", 12, 12)]),
    ("Eingelegtes", "#AED581", None, [("AMBIENT", 6, 12)]),
    ("Essiggurken", "#689F38", "Eingelegtes", [("AMBIENT", 6, 12)]),
    ("Mixed Pickles", "#7CB342", "Eingelegtes", [("AMBIENT", 6, 12)]),
    ("Soßen", "#EF5350", None, [("AMBIENT", 6, 12)]),
    ("Tomatensoße", "#E53935", "Soßen", [("AMBIENT", 12, 12)]),
    ("Sugo", "#D32F2F", "Soßen", [("AMBIENT", 12, 12)]),
    ("Ketchup", "#C62828", "Soßen", [("AMBIENT", 6, 12)]),
    ("Pesto", "#558B2F", "Soßen", [("AMBIENT", 6, 12)]),
    ("Würziges", "#FF7043", None, [("AMBIENT", 3, 12)]),
    ("Chutney", "#E64A19", "Würziges", [("AMBIENT", 6, 12)]),
    ("Relish", "#8D6E63", "Würziges", [("AMBIENT", 6, 12)]),
    ("Senf", "#FFCA28", "Würziges", [("AMBIENT", 3, 6)]),
    ("Antipasti", "#FFA726", None, [("AMBIENT", 3, 6)]),
    ("Fruchtsirup", "#AB47BC", None, [("AMBIENT", 12, 12)]),
    ("Sauerkraut", "#C5E1A5", None, [("AMBIENT", 6, 12)]),
    ("Nudeln & Pasta", "#FFCC80", None, []),
    ("Reis & Getreide", "#D7CCC8", None, []),
    ("Backzutaten", "#FFECB3", None, []),
    ("Konserven", "#90A4AE", None, []),
    ("Gewürze", "#A1887F", None, []),
    ("Öle & Essig", "#C8E6C9", None, []),
    ("Getränke", "#81D4FA", None, []),
    ("Snacks", "#FFE082", None, []),
    ("Eier", "#FFF3E0", None, []),
    ("Aufschnitt", "#FFAB91", None, []),
    ("Milchprodukte (frisch)", "#E1BEE7", None, []),
]

Mutation = Callable[[Session], None]


def _create_old_state(engine: sa.Engine, mutate: Mutation | None = None) -> None:
    """Datenbank im Seed-Stand vor #456 anlegen, optional mit Nutzeränderungen."""
    with Session(engine) as session:
        admin = User(username="admin", email="admin@test.local", role="admin")
        admin.set_password("secret")
        session.add(admin)
        session.commit()
        assert admin.id is not None
        by_name: dict[str, Category] = {}
        for name, color, parent, shelf_lives in OLD_SEED:
            category = Category(
                name=name, color=color, parent_id=by_name[parent].id if parent else None, created_by=admin.id
            )
            session.add(category)
            session.commit()
            by_name[name] = category
            for storage_type, months_min, months_max in shelf_lives:
                session.add(
                    CategoryShelfLife(
                        category_id=category.id,  # type: ignore[arg-type]
                        storage_type=StorageType[storage_type],
                        months_min=months_min,
                        months_max=months_max,
                        source_url="https://example.org",
                    )
                )
        session.add(Location(name="Keller", location_type=LocationType.AMBIENT, created_by=admin.id))
        session.commit()
        if mutate:
            mutate(session)
            session.commit()


def _add_items_everywhere(session: Session) -> None:
    """Ein Artikel je Kategorie und Artikeltyp: jede Kategorie ist belegt."""
    admin_id = session.exec(select(User.id)).one()
    location_id = session.exec(select(Location.id)).one()
    for category in session.exec(select(Category)).all():
        for item_type in ItemType:
            session.add(
                Item(
                    product_name=f"{category.name} {item_type.value}",
                    best_before_date=date(2026, 3, 1),
                    freeze_date=date(2026, 3, 1),
                    quantity=1,
                    unit="Stück",
                    item_type=item_type,
                    location_id=location_id,  # type: ignore[arg-type]
                    category_id=category.id,
                    created_by=admin_id,  # type: ignore[arg-type]
                )
            )


def _category(session: Session, name: str) -> Category | None:
    return session.exec(select(Category).where(Category.name == name)).first()


def _parent_name(session: Session, name: str) -> str | None:
    category = _category(session, name)
    assert category is not None, name
    if category.parent_id is None:
        return None
    parent = session.get(Category, category.parent_id)
    assert parent is not None
    return parent.name


def _shelf_life(session: Session, name: str, storage_type: StorageType) -> tuple[int, int] | None:
    category = _category(session, name)
    assert category is not None, name
    row = session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category.id, CategoryShelfLife.storage_type == storage_type
        )
    ).first()
    return (row.months_min, row.months_max) if row else None


def _expiry_by_item(engine: sa.Engine) -> dict[str, ExpiryView]:
    with Session(engine) as session:
        items = list(session.exec(select(Item)).all())
        views = get_expiry_views(session, items, today=TODAY)
        return {item.product_name: views[item.id] for item in items if item.id is not None}


def _state(engine: sa.Engine) -> set[tuple[str, str | None, str | None]]:
    """(Name, Farbe, Gruppe) aller Kategorien."""
    with Session(engine) as session:
        return {(c.name, c.color, _parent_name(session, c.name)) for c in session.exec(select(Category)).all()}


def _upgrade_from_old_state(cfg: AlembicConfig, engine: sa.Engine, mutate: Mutation | None = None) -> None:
    command.upgrade(cfg, PREVIOUS_REVISION)
    _create_old_state(engine, mutate)
    command.upgrade(cfg, "head")


def test_upgrade_regroups_untouched_seed_data(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Unveränderter Seed-Stand: umbenannt, umgehängt, leere Altkategorien entfernt, Farben ersetzt."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine)

    with Session(engine) as session:
        for old in ("Fleisch", "Milchprodukte", "Fruchtaufstriche", "Würziges", "Obstmus", "Aufschnitt"):
            assert _category(session, old) is None, old
        assert _category(session, "Milchprodukte (frisch)") is None
        assert _parent_name(session, "Wurst") == "Fleisch & Wurst"
        assert _parent_name(session, "Butter") == "Milchprodukte & Eier"
        assert _parent_name(session, "Eier") == "Milchprodukte & Eier"
        assert _parent_name(session, "Marmelade") == "Süßes Eingemachtes"
        for name in ("Apfelmus", "Pflaumenmus", "Kompott", "Fruchtsirup"):
            assert _parent_name(session, name) == "Süßes Eingemachtes", name
        assert _parent_name(session, "Sauerkraut") == "Eingelegtes"
        assert _parent_name(session, "Antipasti") == "Eingelegtes"
        assert _parent_name(session, "Ketchup") == "Würzsaucen"
        assert _parent_name(session, "Senf") == "Würzsaucen"
        assert _shelf_life(session, "Milchprodukte & Eier", StorageType.FROZEN) is None
        assert _category(session, "Butter").color == "#F9A825"  # type: ignore[union-attr]
        assert _category(session, "Eier").color == "#D4A373"  # type: ignore[union-attr]
        assert _category(session, "Milchprodukte & Eier").color == "#78909C"  # type: ignore[union-attr]


def test_upgrade_then_seed_yields_new_structure(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Migration plus Seed ergeben dieselbe Struktur wie eine neue Installation."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine)

    with Session(engine) as session:
        seed_shelf_life_defaults(session)
        grouped = category_service.get_grouped_categories_for_item_type(session, ItemType.PURCHASED_FRESH)

    # Reihenfolge innerhalb der Gruppen folgt in Bestands-DBs den alten IDs
    assert {name: {c.name for c in cats} for name, cats in grouped} == {
        name: set(cats) for name, cats in EXPECTED_GROUPS.items()
    }


def _delete_apfelmus_shelf_life(session: Session) -> None:
    """Nutzer hat die eigene Haltbarkeit von Apfelmus gelöscht: es erbt von Obstmus."""
    apfelmus = _category(session, "Apfelmus")
    assert apfelmus is not None
    row = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == apfelmus.id)).one()
    session.delete(row)


def test_upgrade_and_seed_keep_every_expiry_date(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Kein Artikel ändert sein berechnetes Ablaufdatum – weder durch die Migration noch durch den Seed danach."""
    cfg, engine = migration_db

    def mutate(session: Session) -> None:
        _delete_apfelmus_shelf_life(session)
        # Gruppe ohne eigene Gefrierzeit: der Seed darf sie nicht nachtragen (#462)
        backwaren = _category(session, "Backwaren")
        assert backwaren is not None
        session.delete(
            session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == backwaren.id)).one()
        )
        _add_items_everywhere(session)

    command.upgrade(cfg, PREVIOUS_REVISION)
    _create_old_state(engine, mutate)
    before = _expiry_by_item(engine)

    command.upgrade(cfg, "head")
    assert _expiry_by_item(engine) == before

    with Session(engine) as session:
        seed_shelf_life_defaults(session)
    assert _expiry_by_item(engine) == before


def test_upgrade_keeps_occupied_categories_and_their_inheritance(
    migration_db: tuple[AlembicConfig, sa.Engine],
) -> None:
    """Belegte Kategorien bleiben; was ein Ablaufdatum verschieben würde, bleibt liegen."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine, lambda s: (_delete_apfelmus_shelf_life(s), _add_items_everywhere(s)))

    with Session(engine) as session:
        # belegt: nicht gelöscht
        for name in ("Obstmus", "Aufschnitt", "Milchprodukte (frisch)"):
            assert _category(session, name) is not None, name
        # Artikel direkt in der Gruppe nutzen ihre Gefrierzeit: bleibt
        assert _shelf_life(session, "Milchprodukte & Eier", StorageType.FROZEN) == (2, 6)
        # Eier würde die Gefrierzeit der Gruppe erben: bleibt ohne Gruppe
        assert _parent_name(session, "Eier") is None
        assert _parent_name(session, "Aufschnitt") is None
        # Apfelmus erbt von Obstmus (12–18), Süßes Eingemachtes hätte 12–24: bleibt
        assert _parent_name(session, "Apfelmus") == "Obstmus"
        # eigene Haltbarkeit: unbedenklich umgehängt
        assert _parent_name(session, "Pflaumenmus") == "Süßes Eingemachtes"
        assert _parent_name(session, "Sauerkraut") == "Eingelegtes"
        # kein Artikel hat die Kategorie gewechselt
        for item in session.exec(select(Item)).all():
            category = session.get(Category, item.category_id)
            assert category is not None
            assert item.product_name.startswith(category.name + " ") or item.product_name.startswith(
                _renamed_from(category.name) + " "
            ), item.product_name


def _renamed_from(new_name: str) -> str:
    return {
        "Fleisch & Wurst": "Fleisch",
        "Milchprodukte & Eier": "Milchprodukte",
        "Süßes Eingemachtes": "Fruchtaufstriche",
        "Würzsaucen": "Würziges",
    }.get(new_name, new_name)


def _user_changes(session: Session) -> None:
    """Typische Nutzeränderungen an Standardkategorien."""
    wuerziges = _category(session, "Würziges")
    butter = _category(session, "Butter")
    ketchup = _category(session, "Ketchup")
    eingelegtes = _category(session, "Eingelegtes")
    milchprodukte = _category(session, "Milchprodukte")
    assert wuerziges and butter and ketchup and eingelegtes and milchprodukte
    wuerziges.name = "Pikantes"
    butter.color = "#000000"
    ketchup.parent_id = eingelegtes.id
    frozen = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == milchprodukte.id)).one()
    frozen.months_min, frozen.months_max = 3, 5
    session.add_all([wuerziges, butter, ketchup, frozen])


def test_upgrade_keeps_user_changes(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Vom Nutzer Verändertes bleibt, wie es ist."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine, _user_changes)

    with Session(engine) as session:
        assert _category(session, "Pikantes") is not None
        assert _category(session, "Würzsaucen") is None
        assert _parent_name(session, "Senf") == "Pikantes"
        assert _category(session, "Butter").color == "#000000"  # type: ignore[union-attr]
        assert _parent_name(session, "Ketchup") == "Eingelegtes"
        assert _shelf_life(session, "Milchprodukte & Eier", StorageType.FROZEN) == (3, 5)


def test_downgrade_restores_old_structure(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Downgrade stellt Namen, Gruppen, Farben und Gefrierzeit wieder her; nur leere Altkategorien fehlen."""
    cfg, engine = migration_db
    command.upgrade(cfg, PREVIOUS_REVISION)
    _create_old_state(engine)
    original = _state(engine)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, PREVIOUS_REVISION)

    deleted = {"Obstmus", "Aufschnitt", "Milchprodukte (frisch)"}
    expected = {row for row in original if row[0] not in deleted}
    # Kinder von Obstmus hängen nach dem Löschen der leeren Gruppe bei Süßes Eingemachtes = Fruchtaufstriche
    expected = {
        (name, color, "Fruchtaufstriche" if parent == "Obstmus" else parent) for name, color, parent in expected
    }
    assert _state(engine) == expected
    with Session(engine) as session:
        assert _shelf_life(session, "Milchprodukte", StorageType.FROZEN) == (2, 6)


def test_upgrade_downgrade_upgrade_is_stable(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Erneutes Upgrade nach einem Downgrade ergibt denselben Stand."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine)
    after_first = _state(engine)

    command.downgrade(cfg, PREVIOUS_REVISION)
    command.upgrade(cfg, "head")

    assert _state(engine) == after_first


def _user_built_subgroups(session: Session) -> None:
    """Nutzer hat Sauerkraut zur Gruppe gemacht und Eingelegtes unter Gekochtes gehängt."""
    sauerkraut = _category(session, "Sauerkraut")
    eingelegtes = _category(session, "Eingelegtes")
    gekochtes = _category(session, "Gekochtes")
    admin_id = session.exec(select(User.id)).one()
    assert sauerkraut and eingelegtes and gekochtes
    session.add(Category(name="Rotkraut", parent_id=sauerkraut.id, created_by=admin_id))  # type: ignore[arg-type]
    # Zielgruppe hängt selbst in einer Gruppe: Antipasti darf nicht darunter
    eingelegtes.parent_id = gekochtes.id
    session.add(eingelegtes)


def test_upgrade_never_creates_a_second_group_level(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    """Die Hierarchie bleibt einstufig: keine Gruppe wird Kind, kein Kind bekommt Kinder."""
    cfg, engine = migration_db
    _upgrade_from_old_state(cfg, engine, _user_built_subgroups)

    with Session(engine) as session:
        assert _parent_name(session, "Sauerkraut") is None
        assert _parent_name(session, "Antipasti") is None
