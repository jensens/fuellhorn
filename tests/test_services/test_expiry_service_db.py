"""DB-gestützte Tests für expiry_service (Issue #363).

Deckt das Nachschlagen der Kategorie-Haltbarkeit, die Schwellen aus den
Systemeinstellungen, die Bulk-Variante und ``get_items_expiring_soon`` ab.
"""

from app.models import Item
from app.models import ItemType
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import category_service
from app.services import item_service
from app.services import location_service
from app.services import preferences_service
from app.services import shelf_life_service
from app.services.expiry_service import get_expiry_views
from app.services.expiry_service import get_item_expiry_view
from app.services.expiry_service import get_items_expiring_soon
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(session: Session, test_admin: User) -> dict:
    """Lagerorte, Kategorien und Haltbarkeiten für die Tests."""
    assert test_admin.id is not None
    fridge = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, test_admin.id)
    freezer = location_service.create_location(session, "Truhe", LocationType.FROZEN, test_admin.id)
    soups = category_service.create_category(session, "Suppen", test_admin.id)
    dairy = category_service.create_category(session, "Milchprodukte", test_admin.id)
    assert soups.id is not None and dairy.id is not None
    shelf_life_service.create_shelf_life(session, soups.id, StorageType.FROZEN, months_min=2, months_max=3)
    return {"admin": test_admin.id, "fridge": fridge.id, "freezer": freezer.id, "soups": soups.id, "dairy": dairy.id}


def _mhd_item(session: Session, world: dict, name: str, days: int) -> Item:
    return item_service.create_item(
        session,
        product_name=name,
        best_before_date=date.today() + timedelta(days=days),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=world["fridge"],
        created_by=world["admin"],
        category_id=world["dairy"],
    )


def _frozen_item(session: Session, world: dict, name: str, frozen_days_ago: int, category_key: str = "soups") -> Item:
    freeze = date.today() - timedelta(days=frozen_days_ago)
    return item_service.create_item(
        session,
        product_name=name,
        best_before_date=freeze,
        quantity=1,
        unit="l",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=world["freezer"],
        created_by=world["admin"],
        category_id=world[category_key],
        freeze_date=freeze,
    )


def test_get_item_expiry_view_looks_up_category_shelf_life(session: Session, world: dict) -> None:
    """Heute eingefrorene Suppe mit 2–3 Monaten Haltbarkeit → ok, Idealdatum in 2 Monaten."""
    soup = _frozen_item(session, world, "Kürbissuppe", frozen_days_ago=0)
    view = get_item_expiry_view(session, soup)
    assert (view.status, view.display_date) == ("ok", date.today() + relativedelta(months=2))


def test_get_item_expiry_view_is_unknown_without_shelf_life(session: Session, world: dict) -> None:
    """Eingefrorener Artikel in einer Kategorie ohne FROZEN-Haltbarkeit → unknown."""
    item = _frozen_item(session, world, "Eingefrorene Milch", frozen_days_ago=0, category_key="dairy")
    assert get_item_expiry_view(session, item).status == "unknown"


def test_get_item_expiry_view_uses_system_setting_thresholds(session: Session, world: dict) -> None:
    """Warnschwelle 20 Tage aus den Systemeinstellungen macht ein MHD in 10 Tagen zu warning."""
    preferences_service.set_system_setting(session, "expiry_warning_days", "20", world["admin"])
    item = _mhd_item(session, world, "Joghurt", days=10)
    assert get_item_expiry_view(session, item).status == "warning"


def test_get_expiry_views_returns_view_per_item_id(session: Session, world: dict) -> None:
    """Bulk-Variante liefert für jeden Artikel den gleichen View wie die Einzelvariante."""
    soup = _frozen_item(session, world, "Suppe", frozen_days_ago=0)
    yoghurt = _mhd_item(session, world, "Joghurt", days=2)
    views = get_expiry_views(session, [soup, yoghurt])
    assert views == {soup.id: get_item_expiry_view(session, soup), yoghurt.id: get_item_expiry_view(session, yoghurt)}


def test_get_items_expiring_soon_uses_status_not_best_before_date(session: Session, world: dict) -> None:
    """Review-Szenario: frisch eingefrorene Suppe ist NICHT 'bald ablaufend', MHD in 2 Tagen schon."""
    _frozen_item(session, world, "Kürbissuppe", frozen_days_ago=0)
    _mhd_item(session, world, "Joghurt", days=2)
    assert [i.product_name for i in get_items_expiring_soon(session)] == ["Joghurt"]


def test_get_items_expiring_soon_includes_warning_and_critical_sorted_by_date(session: Session, world: dict) -> None:
    """warning (MHD in 6 Tagen) und critical (MHD in 1 Tag) zählen, ok (30 Tage) nicht; Reihenfolge nach Datum."""
    _mhd_item(session, world, "Käse", days=6)
    _mhd_item(session, world, "Quark", days=1)
    _mhd_item(session, world, "Butter", days=30)
    assert [i.product_name for i in get_items_expiring_soon(session)] == ["Quark", "Käse"]


def test_get_items_expiring_soon_includes_frozen_item_past_optimal_date(session: Session, world: dict) -> None:
    """Suppe, deren Idealdatum überschritten ist, ist 'bald ablaufend'."""
    _frozen_item(session, world, "Alte Suppe", frozen_days_ago=75)
    assert [i.product_name for i in get_items_expiring_soon(session)] == ["Alte Suppe"]


def test_get_items_expiring_soon_excludes_unknown_and_consumed(session: Session, world: dict) -> None:
    """unknown (keine Haltbarkeit) und verbrauchte Artikel erscheinen nicht."""
    _frozen_item(session, world, "Eingefrorene Milch", frozen_days_ago=400, category_key="dairy")
    consumed = _mhd_item(session, world, "Verbrauchter Joghurt", days=1)
    assert consumed.id is not None
    item_service.mark_item_consumed(session, consumed.id, world["admin"])
    assert get_items_expiring_soon(session) == []
