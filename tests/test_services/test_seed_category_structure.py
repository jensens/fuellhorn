"""Tests: Standard-Kategorien nach der Neugruppierung (Issue #456)."""

from app.models.category import Category
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from app.models.item import ItemType
from app.models.user import User
from app.seed import seed_shelf_life_defaults
from app.services import category_service
from sqlmodel import Session
from sqlmodel import select


EXPECTED_GROUPS: dict[str, list[str]] = {
    "Obst & Gemüse": ["Gemüse", "Obst", "Kräuter"],
    "Fleisch & Wurst": ["Rindfleisch", "Schweinefleisch", "Geflügel", "Hackfleisch", "Wurst"],
    "Fisch": ["Fisch (mager)", "Fisch (fett)", "Meeresfrüchte"],
    "Milchprodukte & Eier": [
        "Butter",
        "Käse",
        "Milch",
        "Sahne",
        "Topfen",
        "Frischkäse",
        "Joghurt",
        "Sauerrahm & Schmand",
        "Eier",
    ],
    "Backwaren": ["Brot", "Kuchen"],
    "Gekochtes": ["Suppen", "Eintöpfe", "Fertiggerichte"],
    "Süßes Eingemachtes": ["Marmelade", "Gelee", "Apfelmus", "Pflaumenmus", "Kompott", "Fruchtsirup"],
    "Eingelegtes": ["Essiggurken", "Mixed Pickles", "Sauerkraut", "Antipasti"],
    "Soßen": ["Tomatensoße", "Sugo", "Pesto"],
    "Würzsaucen": ["Ketchup", "Senf", "Chutney", "Relish"],
    "Getrocknetes": ["Trockenobst", "Trockengemüse", "Getrocknete Pilze", "Getrocknete Kräuter & Tee"],
    "Vorrat": [
        "Nudeln & Pasta",
        "Reis & Getreide",
        "Backzutaten",
        "Konserven",
        "Gewürze",
        "Öle & Essig",
        "Getränke",
        "Snacks",
    ],
}


def _names(categories: list[Category]) -> set[str]:
    return {c.name for c in categories}


def test_seed_creates_expected_groups_in_order(session: Session, test_admin: User) -> None:
    """Neue Installation: jede Standardkategorie gehört zu ihrer Gruppe, Gruppen in fester Reihenfolge."""
    seed_shelf_life_defaults(session)

    grouped = category_service.get_grouped_categories_for_item_type(session, ItemType.PURCHASED_FRESH)

    assert [(name, [c.name for c in cats]) for name, cats in grouped] == list(EXPECTED_GROUPS.items())


def test_seed_leaves_no_standard_category_ungrouped(session: Session, test_admin: User) -> None:
    """Keine Standardkategorie landet unter „Sonstiges“."""
    seed_shelf_life_defaults(session)

    grouped = category_service.get_grouped_categories_for_item_type(session, ItemType.PURCHASED_FRESH)

    assert all(name is not None for name, _ in grouped)


def test_seed_removes_obsolete_standard_categories(session: Session, test_admin: User) -> None:
    """Ersetzte Kategorien legt der Seed nicht mehr an."""
    seed_shelf_life_defaults(session)

    names = _names(list(session.exec(select(Category)).all()))
    for obsolete in ("Fleisch", "Milchprodukte", "Fruchtaufstriche", "Obstmus", "Würziges", "Aufschnitt"):
        assert obsolete not in names
    assert "Milchprodukte (frisch)" not in names


def test_frozen_offers_only_freezable_dairy(session: Session, test_admin: User) -> None:
    """Beim Einfrieren gibt es Milch, Sahne, Topfen, Butter, Käse – nichts, was grießig wird."""
    seed_shelf_life_defaults(session)

    frozen = _names(category_service.get_categories_for_item_type(session, ItemType.PURCHASED_THEN_FROZEN))

    assert {"Butter", "Käse", "Milch", "Sahne", "Topfen"} <= frozen
    assert not {"Frischkäse", "Joghurt", "Sauerrahm & Schmand", "Eier"} & frozen


def test_frozen_and_preserved_offer_no_pantry_categories(session: Session, test_admin: User) -> None:
    """Vorrat-Kategorien haben keine Haltbarkeit und erscheinen nur bei frisch Gekauftem."""
    seed_shelf_life_defaults(session)

    frozen = _names(category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN))
    preserved = _names(category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_PRESERVED))

    assert not set(EXPECTED_GROUPS["Vorrat"]) & (frozen | preserved)


def test_groups_without_uniform_shelf_life_have_none(session: Session, test_admin: User) -> None:
    """Gruppen, deren Kategorien unterschiedlich haltbar sind, vererben keine Haltbarkeit."""
    seed_shelf_life_defaults(session)

    for group in ("Obst & Gemüse", "Milchprodukte & Eier", "Getrocknetes", "Vorrat"):
        group_id = session.exec(select(Category.id).where(Category.name == group)).one()
        shelf_lives = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == group_id)).all()
        assert shelf_lives == [], group


def test_new_freezable_dairy_has_sourced_shelf_life(session: Session, test_admin: User) -> None:
    """Neue Gefrierzeiten tragen eine Quelle."""
    seed_shelf_life_defaults(session)

    expected = {"Milch": (2, 3), "Sahne": (2, 3), "Topfen": (10, 12)}
    for name, months in expected.items():
        category_id = session.exec(select(Category.id).where(Category.name == name)).one()
        shelf_life = session.exec(
            select(CategoryShelfLife).where(
                CategoryShelfLife.category_id == category_id,
                CategoryShelfLife.storage_type == StorageType.FROZEN,
            )
        ).one()
        assert (shelf_life.months_min, shelf_life.months_max) == months, name
        assert shelf_life.source_url and shelf_life.source_url.startswith("https://"), name


DRIED = ["Trockenobst", "Trockengemüse", "Getrocknete Pilze", "Getrocknete Kräuter & Tee"]


def test_dried_categories_have_sourced_ambient_shelf_life(session: Session, test_admin: User) -> None:
    """Getrocknetes hält bei Raumtemperatur 6–12 Monate, jeweils mit Quelle (#476)."""
    seed_shelf_life_defaults(session)

    for name in DRIED:
        category_id = session.exec(select(Category.id).where(Category.name == name)).one()
        shelf_life = session.exec(
            select(CategoryShelfLife).where(
                CategoryShelfLife.category_id == category_id,
                CategoryShelfLife.storage_type == StorageType.AMBIENT,
            )
        ).one()
        assert (shelf_life.months_min, shelf_life.months_max) == (6, 12), name
        assert shelf_life.source_url and shelf_life.source_url.startswith("https://"), name


def test_dried_categories_offered_for_homemade_preserved_not_for_frozen(session: Session, test_admin: User) -> None:
    """Selbst Getrocknetes läuft als „selbst eingemacht“; beim Einfrieren erscheint es nicht (#476)."""
    seed_shelf_life_defaults(session)

    preserved = _names(category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_PRESERVED))
    frozen = _names(category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN))
    fresh = _names(category_service.get_categories_for_item_type(session, ItemType.PURCHASED_FRESH))

    assert set(DRIED) <= preserved
    assert set(DRIED) <= fresh  # gekaufte Rosinen: MHD von der Packung
    assert not set(DRIED) & frozen


def test_seed_keeps_user_created_trockenobst_and_groups_it(session: Session, test_admin: User) -> None:
    """Selbst angelegtes „Trockenobst“ behält seine Haltbarkeit und kommt in die neue Gruppe (#460, #462, #476)."""
    own = Category(name="Trockenobst", color="#123456", created_by=test_admin.id)  # type: ignore[arg-type]
    session.add(own)
    session.commit()
    session.add(
        CategoryShelfLife(
            category_id=own.id,  # type: ignore[arg-type]
            storage_type=StorageType.AMBIENT,
            months_min=9,
            months_max=9,
            source_url="eigene Erfahrung",
        )
    )
    session.commit()

    seed_shelf_life_defaults(session)

    category = session.exec(select(Category).where(Category.name == "Trockenobst")).one()
    group_id = session.exec(select(Category.id).where(Category.name == "Getrocknetes")).one()
    shelf_lives = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == category.id)).all()
    assert category.parent_id == group_id
    assert category.color == "#123456"
    assert [(s.storage_type, s.months_min, s.months_max, s.source_url) for s in shelf_lives] == [
        (StorageType.AMBIENT, 9, 9, "eigene Erfahrung")
    ]


def test_seed_leaves_user_grouped_trockenobst_in_its_group(session: Session, test_admin: User) -> None:
    """Hat der Nutzer „Trockenobst“ schon einer Gruppe zugeordnet, bleibt es dort."""
    sweet = Category(name="Süßes Eingemachtes", created_by=test_admin.id)  # type: ignore[arg-type]
    session.add(sweet)
    session.commit()
    session.add(Category(name="Trockenobst", parent_id=sweet.id, created_by=test_admin.id))  # type: ignore[arg-type]
    session.commit()

    seed_shelf_life_defaults(session)

    category = session.exec(select(Category).where(Category.name == "Trockenobst")).one()
    assert category.parent_id == sweet.id
