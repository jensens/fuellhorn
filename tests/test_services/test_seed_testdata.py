"""Testdaten-Seed für die lokale Entwicklung (Issue #468).

Ein neuer Worktree startet mit leerer Datenbank; ``./scripts/dev-server.sh`` spielt die
Testdaten ein. Seit der zentralen Passwortregel (#383) scheiterte das am Passwort
``admin``, der Worktree blieb ohne Admin und ohne Beispieldaten.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import StorageType
from app.models.user import Role
from app.seed import TESTDATA_ADMIN_PASSWORD
from app.seed import seed_testdata
from app.services import expiry_service
from app.services import item_service
from app.services.auth_service import authenticate_user
from app.services.auth_service import create_user
from sqlmodel import Session
from sqlmodel import select


def test_seed_runs_on_an_empty_database(session: Session) -> None:
    result = seed_testdata(session)

    assert result["admin"] == 1
    assert result["items"] > 0


def test_documented_admin_can_log_in(session: Session) -> None:
    seed_testdata(session)

    assert authenticate_user(session, "admin", TESTDATA_ADMIN_PASSWORD).username == "admin"


def test_existing_admin_keeps_its_password(session: Session) -> None:
    """Der Seed ergänzt nur (#460): ein vorhandener Admin behält sein Passwort."""
    create_user(session, username="admin", email="admin@example.com", password="eigenes-passwort", role=Role.ADMIN)

    result = seed_testdata(session)

    assert result["admin"] == 0
    assert authenticate_user(session, "admin", "eigenes-passwort").username == "admin"


def test_seeded_items_need_no_completion(session: Session) -> None:
    """Beispielartikel erfüllen dieselben Regeln wie erfasste (#385): nichts steht in der Nachpflege-Liste."""
    seed_testdata(session)

    assert [entry.item.product_name for entry in expiry_service.get_items_needing_completion(session)] == []


def test_every_seeded_item_has_a_known_expiry(session: Session) -> None:
    """Ohne Haltbarkeit der Kategorie zeigte die Hälfte der Beispiele "Keine Haltbarkeitsdaten"."""
    seed_testdata(session)

    items = item_service.get_active_items(session)
    views = expiry_service.get_expiry_views(session, items)
    unknown = [item.product_name for item in items if item.id is not None and views[item.id].status == "unknown"]
    assert unknown == []


def test_existing_shelf_life_of_a_test_category_stays(session: Session) -> None:
    """Der Seed ergänzt fehlende Haltbarkeiten, überschreibt aber keine angepassten (#460)."""
    admin = create_user(
        session, username="admin", email="admin@example.com", password="eigenes-passwort", role=Role.ADMIN
    )
    assert admin.id is not None
    meat = Category(name="Fleisch", created_by=admin.id)
    session.add(meat)
    session.commit()
    session.refresh(meat)
    assert meat.id is not None
    session.add(CategoryShelfLife(category_id=meat.id, storage_type=StorageType.FROZEN, months_min=1, months_max=2))
    session.commit()

    seed_testdata(session)

    shelf_life = session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == meat.id, CategoryShelfLife.storage_type == StorageType.FROZEN
        )
    ).one()
    assert (shelf_life.months_min, shelf_life.months_max) == (1, 2)
