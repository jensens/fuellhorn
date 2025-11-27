"""Test pages for Item Card component testing.

These pages are used to test the item_card component in isolation.
"""

from ...database import get_session
from ...models.category import Category
from ...models.freeze_time_config import ItemType
from ...models.item import Item
from ...models.location import Location
from ...models.location import LocationType
from ..components.item_card import create_item_card
from datetime import date
from datetime import timedelta
from nicegui import ui
from sqlmodel import Session


def _create_test_location(session: Session) -> Location:
    """Create a test location."""
    location = session.get(Location, 1)
    if location:
        return location

    location = Location(
        id=1,
        name="Tiefkühltruhe",
        location_type=LocationType.FROZEN,
        created_by=1,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def _create_test_category(session: Session) -> Category:
    """Create a test category."""
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
    return category


def _create_test_item(
    session: Session,
    location: Location,
    expiry_days_from_now: int = 30,
    category_id: int | None = None,
) -> Item:
    """Create a test item with specified expiry."""
    expiry_date = date.today() + timedelta(days=expiry_days_from_now)
    item = Item(
        product_name="Tomaten",
        best_before_date=date.today(),
        expiry_date=expiry_date,
        quantity=500,
        unit="g",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        category_id=category_id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@ui.page("/test-item-card")
def page_item_card() -> None:
    """Test page for basic item card rendering."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        item = _create_test_item(session, location, expiry_days_from_now=30)
        create_item_card(item, session)


@ui.page("/test-item-card-with-categories")
def page_item_card_with_categories() -> None:
    """Test page for item card with category."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session)
        item = _create_test_item(session, location, expiry_days_from_now=30, category_id=category.id)
        create_item_card(item, session)


@ui.page("/test-item-card-critical")
def page_item_card_critical() -> None:
    """Test page for item card with critical expiry (< 3 days)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        item = _create_test_item(session, location, expiry_days_from_now=2)
        create_item_card(item, session)


@ui.page("/test-item-card-warning")
def page_item_card_warning() -> None:
    """Test page for item card with warning expiry (< 7 days)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        item = _create_test_item(session, location, expiry_days_from_now=5)
        create_item_card(item, session)


@ui.page("/test-item-card-ok")
def page_item_card_ok() -> None:
    """Test page for item card with ok expiry (> 7 days)."""
    with next(get_session()) as session:
        location = _create_test_location(session)
        item = _create_test_item(session, location, expiry_days_from_now=10)
        create_item_card(item, session)
