"""Test pages for Item Card component testing.

These pages are used to test the item_card component in isolation.
Includes tests for both shelf-life items (two dates) and MHD items (single date).
"""

from ...database import get_session
from ...models.category import Category
from ...models.category_shelf_life import CategoryShelfLife
from ...models.category_shelf_life import StorageType
from ...models.freeze_time_config import ItemType
from ...models.item import Item
from ...models.location import Location
from ...models.location import LocationType
from ..components.item_card import create_item_card
from datetime import date
from datetime import timedelta
from nicegui import ui
from sqlmodel import Session


def _create_test_location(
    session: Session,
    location_type: LocationType = LocationType.FROZEN,
) -> Location:
    """Create a test location."""
    # Check for existing location with same type
    location_id = 1 if location_type == LocationType.FROZEN else 2
    location = session.get(Location, location_id)
    if location:
        return location

    name = "Tiefkühltruhe" if location_type == LocationType.FROZEN else "Kühlschrank"
    location = Location(
        id=location_id,
        name=name,
        location_type=location_type,
        created_by=1,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def _create_test_category(session: Session, with_shelf_life: bool = True) -> Category:
    """Create a test category with optional shelf life config."""
    category = session.get(Category, 1)
    if category:
        return category

    category = Category(
        id=1,
        name="Gemüse",
        color="#00FF00",
        created_by=1,
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    # Add shelf life config for frozen storage (6-12 months)
    if with_shelf_life and category.id is not None:
        shelf_life = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )
        session.add(shelf_life)
        session.commit()

    return category


def _create_shelf_life_item(
    session: Session,
    location: Location,
    category: Category,
    freeze_days_ago: int = 30,
) -> Item:
    """Create a shelf-life item (HOMEMADE_FROZEN) with freeze date."""
    freeze_date = date.today() - timedelta(days=freeze_days_ago)
    item = Item(
        product_name="Erbsen",
        best_before_date=freeze_date,
        freeze_date=freeze_date,
        expiry_date=freeze_date,  # Placeholder, calculated dynamically
        quantity=500,
        unit="g",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        category_id=category.id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _create_mhd_item(
    session: Session,
    location: Location,
    category: Category,
    mhd_days_from_now: int = 10,
) -> Item:
    """Create an MHD item (PURCHASED_FRESH) with best-before date."""
    best_before = date.today() + timedelta(days=mhd_days_from_now)
    item = Item(
        product_name="Joghurt",
        best_before_date=best_before,
        expiry_date=best_before,
        quantity=150,
        unit="g",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        category_id=category.id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# =============================================================================
# Test pages for shelf-life items (two dates: optimal + max)
# =============================================================================


@ui.page("/test-item-card")
def page_item_card() -> None:
    """Test page for basic item card rendering (shelf-life item)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        item = _create_shelf_life_item(session, location, category, freeze_days_ago=30)
        create_item_card(item, session)


@ui.page("/test-item-card-with-categories")
def page_item_card_with_categories() -> None:
    """Test page for item card with category displayed."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        item = _create_shelf_life_item(session, location, category, freeze_days_ago=30)
        create_item_card(item, session)


@ui.page("/test-item-card-critical")
def page_item_card_critical() -> None:
    """Test page for item card with critical expiry (close to max date)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        # Frozen 11.5 months ago = 2 days before max (12 months)
        item = _create_shelf_life_item(session, location, category, freeze_days_ago=350)
        create_item_card(item, session)


@ui.page("/test-item-card-warning")
def page_item_card_warning() -> None:
    """Test page for item card with warning expiry (past optimal, before max)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        # Frozen 7 months ago = past optimal (6 months), before max (12 months)
        item = _create_shelf_life_item(session, location, category, freeze_days_ago=210)
        create_item_card(item, session)


@ui.page("/test-item-card-ok")
def page_item_card_ok() -> None:
    """Test page for item card with ok expiry (before optimal date)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        # Frozen 30 days ago = well before optimal (6 months)
        item = _create_shelf_life_item(session, location, category, freeze_days_ago=30)
        create_item_card(item, session)


# =============================================================================
# Test pages for MHD items (single date)
# =============================================================================


@ui.page("/test-item-card-mhd")
def page_item_card_mhd() -> None:
    """Test page for MHD item card (single date display)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        category = _create_test_category(session, with_shelf_life=False)
        item = _create_mhd_item(session, location, category, mhd_days_from_now=10)
        create_item_card(item, session)


@ui.page("/test-item-card-mhd-critical")
def page_item_card_mhd_critical() -> None:
    """Test page for MHD item with critical status (< 3 days)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        category = _create_test_category(session, with_shelf_life=False)
        item = _create_mhd_item(session, location, category, mhd_days_from_now=2)
        create_item_card(item, session)


@ui.page("/test-item-card-mhd-warning")
def page_item_card_mhd_warning() -> None:
    """Test page for MHD item with warning status (3-7 days)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        category = _create_test_category(session, with_shelf_life=False)
        item = _create_mhd_item(session, location, category, mhd_days_from_now=5)
        create_item_card(item, session)
