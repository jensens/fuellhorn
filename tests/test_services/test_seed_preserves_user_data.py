"""Tests: Seed legt nur Fehlendes an und überschreibt keine Nutzerdaten (Issue #460)."""

from app.models.category import Category
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from app.models.user import User
from app.seed import seed_shelf_life_defaults
from sqlmodel import Session
from sqlmodel import select


def _category(session: Session, name: str) -> Category:
    return session.exec(select(Category).where(Category.name == name)).one()


def _shelf_life(session: Session, name: str, storage_type: StorageType) -> CategoryShelfLife:
    category = _category(session, name)
    return session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category.id,
            CategoryShelfLife.storage_type == storage_type,
        )
    ).one()


def test_seed_keeps_user_changed_shelf_life(session: Session, test_admin: User) -> None:
    """Eine vom Nutzer angepasste Haltbarkeit übersteht einen weiteren Seed-Lauf."""
    seed_shelf_life_defaults(session)
    shelf_life = _shelf_life(session, "Rindfleisch", StorageType.FROZEN)
    shelf_life.months_min = 5
    shelf_life.months_max = 7
    shelf_life.source_url = "eigene Erfahrung"
    session.add(shelf_life)
    session.commit()

    seed_shelf_life_defaults(session)

    shelf_life = _shelf_life(session, "Rindfleisch", StorageType.FROZEN)
    assert (shelf_life.months_min, shelf_life.months_max, shelf_life.source_url) == (5, 7, "eigene Erfahrung")


def test_seed_keeps_user_moved_category(session: Session, test_admin: User) -> None:
    """Eine vom Nutzer in eine andere Gruppe umgehängte Kategorie bleibt dort."""
    seed_shelf_life_defaults(session)
    wurst = _category(session, "Wurst")
    wurst.parent_id = _category(session, "Gekochtes").id
    session.add(wurst)
    session.commit()

    seed_shelf_life_defaults(session)

    assert _category(session, "Wurst").parent_id == _category(session, "Gekochtes").id


def test_seed_keeps_user_ungrouped_category_in_existing_group(session: Session, test_admin: User) -> None:
    """Hat der Nutzer eine Kategorie aus einer bestehenden Gruppe gelöst, bleibt sie ohne Gruppe."""
    seed_shelf_life_defaults(session)
    wurst = _category(session, "Wurst")
    wurst.parent_id = None
    session.add(wurst)
    session.commit()

    seed_shelf_life_defaults(session)

    assert _category(session, "Wurst").parent_id is None


def test_seed_keeps_user_changed_color(session: Session, test_admin: User) -> None:
    """Eine vom Nutzer geänderte Farbe bleibt erhalten."""
    seed_shelf_life_defaults(session)
    senf = _category(session, "Senf")
    senf.color = "#123456"
    session.add(senf)
    session.commit()

    seed_shelf_life_defaults(session)

    assert _category(session, "Senf").color == "#123456"


def test_seed_groups_existing_categories_under_newly_created_group(session: Session, test_admin: User) -> None:
    """Datenbank vor #351: Kinder einer neu angelegten Gruppe werden ihr zugeordnet."""
    suppen = Category(name="Suppen", color="#FFCCBC", created_by=test_admin.id)  # type: ignore[arg-type]
    session.add(suppen)
    session.commit()

    seed_shelf_life_defaults(session)

    assert _category(session, "Suppen").parent_id == _category(session, "Gekochtes").id


def test_seed_keeps_deleted_shelf_life_of_existing_category(session: Session, test_admin: User) -> None:
    """Eine gelöschte Haltbarkeit bleibt gelöscht: sonst bekämen Artikel plötzlich ein Ablaufdatum (#462)."""
    seed_shelf_life_defaults(session)
    session.delete(_shelf_life(session, "Senf", StorageType.AMBIENT))
    session.commit()

    seed_shelf_life_defaults(session)

    senf = _category(session, "Senf")
    assert session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == senf.id)).all() == []


def test_seed_adds_missing_category_with_shelf_life(session: Session, test_admin: User) -> None:
    """Fehlende Kategorien werden samt Standard-Haltbarkeit angelegt."""
    seed_shelf_life_defaults(session)
    session.delete(_shelf_life(session, "Senf", StorageType.AMBIENT))
    session.commit()
    session.delete(_category(session, "Senf"))
    session.delete(_category(session, "Getränke"))
    session.commit()

    seed_shelf_life_defaults(session)

    senf_shelf_life = _shelf_life(session, "Senf", StorageType.AMBIENT)
    assert (senf_shelf_life.months_min, senf_shelf_life.months_max) == (3, 6)
    assert _category(session, "Getränke").parent_id is None


def test_seed_is_idempotent(session: Session, test_admin: User) -> None:
    """Ein zweiter Lauf legt nichts doppelt an."""
    seed_shelf_life_defaults(session)
    categories = len(session.exec(select(Category)).all())
    shelf_lives = len(session.exec(select(CategoryShelfLife)).all())

    seed_shelf_life_defaults(session)

    assert len(session.exec(select(Category)).all()) == categories
    assert len(session.exec(select(CategoryShelfLife)).all()) == shelf_lives
