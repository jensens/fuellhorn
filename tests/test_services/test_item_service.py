"""Tests for item_service."""

from app.models import ItemType
from app.models import LocationType
from app.models import User
from app.services import category_service
from app.services import freeze_time_service
from app.services import item_service
from app.services import location_service
from datetime import date
from datetime import timedelta
import pytest
from sqlmodel import Session


def test_create_item(session: Session, test_admin: User) -> None:
    """Test creating an item with automatic expiry calculation."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.PURCHASED_FROZEN,
        freeze_time_months=12,
        created_by=test_admin.id,
    )

    item = item_service.create_item(
        session=session,
        product_name="Rindfleisch",
        best_before_date=date(2024, 1, 1),
        freeze_date=date(2024, 6, 1),
        quantity=1.5,
        unit="kg",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
    )

    assert item.id is not None
    assert item.product_name == "Rindfleisch"
    assert item.expiry_date == date(2025, 6, 1)  # freeze_date + 12 months
    assert item.is_consumed is False


def test_create_item_with_categories(session: Session, test_admin: User) -> None:
    """Test creating an item with categories."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    cat1 = category_service.create_category(
        session=session,
        name="Fleisch",
        created_by=test_admin.id,
    )
    cat2 = category_service.create_category(
        session=session,
        name="Bio",
        created_by=test_admin.id,
    )

    assert cat1.id is not None
    assert cat2.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Hähnchenbrust",
        best_before_date=date(2024, 12, 1),
        quantity=0.5,
        unit="kg",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_ids=[cat1.id, cat2.id],
    )

    assert item.id is not None
    categories = item_service.get_item_categories(session, item.id)
    assert len(categories) == 2
    assert cat1.id in [c.id for c in categories]
    assert cat2.id in [c.id for c in categories]


def test_get_all_items(session: Session, test_admin: User) -> None:
    """Test getting all items."""
    location = location_service.create_location(
        session=session,
        name="Vorratsraum",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    item_service.create_item(
        session=session,
        product_name="Tomaten",
        best_before_date=date(2025, 6, 1),
        quantity=6,
        unit="Stück",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
    )
    item_service.create_item(
        session=session,
        product_name="Bohnen",
        best_before_date=date(2025, 12, 1),
        quantity=4,
        unit="Dosen",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
    )

    items = item_service.get_all_items(session)

    assert len(items) == 2


def test_get_item(session: Session, test_admin: User) -> None:
    """Test getting an item by ID."""
    location = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    created = item_service.create_item(
        session=session,
        product_name="Marmelade",
        best_before_date=date(2025, 3, 1),
        quantity=3,
        unit="Gläser",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
    )

    item = item_service.get_item(session, created.id)

    assert item.id == created.id
    assert item.product_name == "Marmelade"


def test_get_item_not_found_fails(session: Session) -> None:
    """Test that getting non-existent item fails."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.get_item(session, 999)


def test_update_item(session: Session, test_admin: User) -> None:
    """Test updating an item."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    created = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2024, 1, 1),
        freeze_date=date(2024, 6, 1),
        quantity=1.0,
        unit="kg",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
    )

    updated = item_service.update_item(
        session=session,
        id=created.id,
        quantity=0.5,
        notes="Halbe Packung verwendet",
    )

    assert updated.quantity == 0.5
    assert updated.notes == "Halbe Packung verwendet"
    assert updated.product_name == "Erbsen"  # Unchanged


def test_mark_item_consumed(session: Session, test_admin: User) -> None:
    """Test marking an item as consumed."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    created = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1.0,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
    )

    updated = item_service.mark_item_consumed(session, created.id)

    assert updated.is_consumed is True


def test_delete_item(session: Session, test_admin: User) -> None:
    """Test deleting an item."""
    location = location_service.create_location(
        session=session,
        name="Vorratsraum",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    created = item_service.create_item(
        session=session,
        product_name="Alte Konserve",
        best_before_date=date(2020, 1, 1),
        quantity=1,
        unit="Dose",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
    )

    item_service.delete_item(session, created.id)

    with pytest.raises(ValueError, match="Item with id .* not found"):
        item_service.get_item(session, created.id)


def test_get_items_by_location(session: Session, test_admin: User) -> None:
    """Test getting items filtered by location."""
    location1 = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    location2 = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )

    item_service.create_item(
        session=session,
        product_name="Eis",
        best_before_date=date(2025, 1, 1),
        freeze_date=date(2024, 6, 1),
        quantity=1,
        unit="Packung",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location1.id,
        created_by=test_admin.id,
    )
    item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location2.id,
        created_by=test_admin.id,
    )

    items = item_service.get_items_by_location(session, location1.id)

    assert len(items) == 1
    assert items[0].product_name == "Eis"


def test_get_items_expiring_soon(session: Session, test_admin: User) -> None:
    """Test getting items expiring within X days."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )

    # Item expiring in 5 days
    item_service.create_item(
        session=session,
        product_name="Joghurt",
        best_before_date=date.today() + timedelta(days=5),
        quantity=1,
        unit="Becher",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
    )
    # Item expiring in 20 days
    item_service.create_item(
        session=session,
        product_name="Käse",
        best_before_date=date.today() + timedelta(days=20),
        quantity=1,
        unit="Packung",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
    )

    items = item_service.get_items_expiring_soon(session, days=7)

    assert len(items) == 1
    assert items[0].product_name == "Joghurt"
