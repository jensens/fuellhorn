"""UI Tests: Haltbarkeitsstatus auf den echten Seiten (Issue #363).

Vorratsliste, Dashboard und Bottom-Sheet müssen den Status aus ``expiry_service``
zeigen. Vorher rechnete jede Stelle selbst und zeigte frisch eingefrorene Artikel
als abgelaufen bzw. zählte sie als "bald ablaufend".
"""

from app.models import ItemType
from app.models import LocationType
from app.models import StorageType
from app.services import category_service
from app.services import item_service
from app.services import location_service
from app.services import shelf_life_service
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="expiry_world")
def expiry_world_fixture(isolated_test_database) -> dict[str, int]:
    """Truhe + Kühlschrank, Kategorie 'Suppen' (FROZEN 2–3 Monate), Kategorie 'Reste' ohne Haltbarkeit."""
    with Session(isolated_test_database) as session:
        freezer = location_service.create_location(session, "Truhe", LocationType.FROZEN, created_by=1)
        fridge = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, created_by=1)
        soups = category_service.create_category(session, "Suppen", created_by=1)
        rest = category_service.create_category(session, "Reste", created_by=1)
        assert soups.id is not None
        shelf_life_service.create_shelf_life(session, soups.id, StorageType.FROZEN, months_min=2, months_max=3)
        assert freezer.id and fridge.id and rest.id
        return {"freezer": freezer.id, "fridge": fridge.id, "soups": soups.id, "rest": rest.id}


def _frozen_item(session: Session, world: dict[str, int], name: str, category: str, days_ago: int = 0) -> int:
    freeze = date.today() - timedelta(days=days_ago)
    item = item_service.create_item(
        session,
        product_name=name,
        best_before_date=freeze,
        quantity=1,
        unit="l",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=world["freezer"],
        created_by=1,
        category_id=world[category],
        freeze_date=freeze,
    )
    assert item.id is not None
    return item.id


def _mhd_item(session: Session, world: dict[str, int], name: str, days: int) -> int:
    item = item_service.create_item(
        session,
        product_name=name,
        best_before_date=date.today() + timedelta(days=days),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=world["fridge"],
        created_by=1,
        category_id=world["rest"],
    )
    assert item.id is not None
    return item.id


def _item_cards(user: User) -> list[ui.card]:
    return [card for card in user.find(kind=ui.card).elements if "sp-item-card" in card.classes]


# --- Vorratsliste / Item-Card -------------------------------------------------------


async def test_items_page_frozen_item_without_shelf_life_shows_unknown(
    logged_in_user: User, isolated_test_database, expiry_world: dict[str, int]
) -> None:
    """Eingefrorener Artikel, dessen Kategorie die Haltbarkeit verloren hat, zeigt 'Keine Haltbarkeitsdaten'."""
    with Session(isolated_test_database) as session:
        _frozen_item(session, expiry_world, "Eingefrorene Reste", "soups", days_ago=60)
        # Anlegen braucht eine passende Haltbarkeit (Issue #385); danach entfernt → unknown
        shelf_life = shelf_life_service.get_shelf_life(session, expiry_world["soups"], StorageType.FROZEN)
        assert shelf_life is not None and shelf_life.id is not None
        shelf_life_service.delete_shelf_life(session, shelf_life.id)

    await logged_in_user.open("/items")
    await logged_in_user.should_see("Keine Haltbarkeitsdaten")
    await logged_in_user.should_not_see("Abgelaufen")


async def test_items_page_fresh_frozen_soup_is_ok(
    logged_in_user: User, isolated_test_database, expiry_world: dict[str, int]
) -> None:
    """Heute eingefrorene Suppe (2–3 Monate) hat Status ok: kein farbiger Rahmen, Idealdatum im Badge."""
    with Session(isolated_test_database) as session:
        _frozen_item(session, expiry_world, "Kürbissuppe", "soups")

    await logged_in_user.open("/items")
    await logged_in_user.should_see("Kürbissuppe")
    optimal = date.today() + relativedelta(months=2)
    await logged_in_user.should_see(optimal.strftime("%d.%m.%y"))
    (card,) = _item_cards(logged_in_user)
    assert "status-critical" not in card.classes and "status-warning" not in card.classes


async def test_items_page_soup_past_optimal_date_is_warning_not_critical(
    logged_in_user: User, isolated_test_database, expiry_world: dict[str, int]
) -> None:
    """Idealdatum vor 10 Tagen überschritten, Maximum in ~20 Tagen → warning (die Karte zeigte bisher critical)."""
    with Session(isolated_test_database) as session:
        _frozen_item(session, expiry_world, "Alte Suppe", "soups", days_ago=71)

    await logged_in_user.open("/items")
    await logged_in_user.should_see("Alte Suppe")
    (card,) = _item_cards(logged_in_user)
    assert "status-warning" in card.classes
    assert "status-critical" not in card.classes


# --- Dashboard ----------------------------------------------------------------------


async def test_dashboard_counts_only_warning_and_critical_items(
    logged_in_user: User, isolated_test_database, expiry_world: dict[str, int]
) -> None:
    """Frisch eingefrorene Suppe zählt nicht als 'bald ablaufend', Joghurt mit MHD in 2 Tagen schon."""
    with Session(isolated_test_database) as session:
        _frozen_item(session, expiry_world, "Kürbissuppe", "soups")
        _mhd_item(session, expiry_world, "Joghurt", days=2)

    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Bald ablaufend (1)")
    await logged_in_user.should_see("Joghurt")


# --- Bottom-Sheet -------------------------------------------------------------------


async def test_bottom_sheet_shows_optimal_date_for_frozen_item(
    user: User, isolated_test_database, expiry_world: dict[str, int]
) -> None:
    """Bottom-Sheet zeigt für eingefrorene Artikel 'Ideal bis' + Idealdatum statt 'Abgelaufen'."""
    with Session(isolated_test_database) as session:
        item_id = _frozen_item(session, expiry_world, "Kürbissuppe", "soups")

    await user.open(f"/test/bottom-sheet/{item_id}")
    await user.should_see("Ideal bis")
    await user.should_see((date.today() + relativedelta(months=2)).strftime("%d.%m.%Y"))
    await user.should_not_see("Abgelaufen")
