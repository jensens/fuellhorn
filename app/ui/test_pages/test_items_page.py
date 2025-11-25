"""Test pages for Items Page UI testing.

These pages set up test data and allow testing the items page components.
"""

from ...database import get_session
from ...models.category import Category
from ...models.freeze_time_config import ItemType
from ...models.item import Item
from ...models.item import ItemCategory
from ...models.location import Location
from ...models.location import LocationType
from ..components import create_bottom_nav
from ..components import create_item_card
from datetime import date
from datetime import timedelta
from nicegui import app
from nicegui import ui
from sqlmodel import Session
from sqlmodel import select


def _create_test_location(session: Session) -> Location:
    """Create a test location."""
    location = session.get(Location, 1)
    if location:
        return location

    new_location = Location(
        id=1,
        name="Tiefkühltruhe",
        location_type=LocationType.FROZEN,
        created_by=1,
    )
    session.add(new_location)
    session.commit()
    session.refresh(new_location)
    return new_location


def _create_test_category(session: Session, name: str = "Gemüse", id: int = 1) -> Category:
    """Create a test category."""
    category = session.get(Category, id)
    if category:
        return category

    new_category = Category(
        id=id,
        name=name,
        color="#00FF00",
        created_by=1,
    )
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category


def _create_test_item(
    session: Session,
    location: Location,
    product_name: str = "Tomaten",
    expiry_days_from_now: int = 30,
    quantity: float = 500,
    unit: str = "g",
    is_consumed: bool = False,
) -> Item:
    """Create a test item."""
    expiry_date = date.today() + timedelta(days=expiry_days_from_now)
    item = Item(
        product_name=product_name,
        best_before_date=date.today(),
        expiry_date=expiry_date,
        quantity=quantity,
        unit=unit,
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        created_by=1,
        is_consumed=is_consumed,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _set_test_session() -> None:
    """Set test user session."""
    app.storage.user["authenticated"] = True
    app.storage.user["user_id"] = 1
    app.storage.user["username"] = "admin"


@ui.page("/test-login-admin")
def page_test_login_admin(next: str = "") -> None:
    """Test page to simulate admin login.

    Args:
        next: Optional URL to redirect to after login.
              If not provided, shows a confirmation page.
    """
    _set_test_session()
    if next:
        ui.navigate.to(next)
    else:
        ui.label("Angemeldet als admin")
        ui.label("Willkommen")


@ui.page("/test-items-page-with-items")
def page_items_with_items() -> None:
    """Test page with items displayed as cards."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create multiple test items
        item1 = _create_test_item(
            session,
            location,
            product_name="Tomaten",
            expiry_days_from_now=30,
            quantity=500,
            unit="g",
        )
        _create_test_item(
            session,
            location,
            product_name="Hackfleisch",
            expiry_days_from_now=10,
            quantity=750,
            unit="g",
        )

        # Add category to first item
        category = _create_test_category(session)
        item_category = ItemCategory(item_id=item1.id, category_id=category.id)
        session.add(item_category)
        session.commit()

        # Create page layout
        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get non-consumed items
            items = list(
                session.exec(
                    select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                ).all()
            )

            if items:
                for item in items:
                    create_item_card(item, session)
            else:
                ui.label("Keine Artikel vorhanden")

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-consumed")
def page_items_with_consumed() -> None:
    """Test page to verify consumed items are excluded."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create active item
        _create_test_item(
            session,
            location,
            product_name="Aktiver Artikel",
            expiry_days_from_now=30,
            is_consumed=False,
        )

        # Create consumed item (should not be shown)
        _create_test_item(
            session,
            location,
            product_name="Entnommener Artikel",
            expiry_days_from_now=30,
            is_consumed=True,
        )

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get non-consumed items only
            items = list(
                session.exec(
                    select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                ).all()
            )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-empty")
def page_items_empty() -> None:
    """Test page with no items (empty state)."""
    _set_test_session()

    with ui.column().classes("w-full"):
        ui.label("Vorrat").classes("text-h5")
        ui.label("Keine Artikel vorhanden")

    create_bottom_nav(current_page="items")
