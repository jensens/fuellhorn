"""UI Tests for Item Edit Page (/items/{id}/edit)."""

from app.models import ItemType
from app.models import LocationType
from app.services import category_service
from app.services import item_service
from app.services import location_service
from datetime import date
from nicegui.testing import User
from sqlmodel import Session


async def test_edit_item_route_requires_auth(user: User) -> None:
    """Test that /items/1/edit requires authentication."""
    await user.open("/items/1/edit")
    # Should redirect to login
    await user.should_see("Benutzername")


async def test_edit_item_page_shows_form(logged_in_user: User, isolated_test_database) -> None:
    """Test that edit page shows a form with item fields."""
    # Create test data in the isolated database
    with Session(isolated_test_database) as session:
        location = location_service.create_location(
            session=session,
            name="Kuehlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,  # admin user
        )
        category = category_service.create_category(
            session=session,
            name="Milchprodukte",
            created_by=1,
        )
        item = item_service.create_item(
            session=session,
            product_name="Testmilch",
            best_before_date=date(2025, 12, 31),
            quantity=1.0,
            unit="L",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=1,
            category_id=category.id,
        )
        item_id = item.id

    await logged_in_user.open(f"/items/{item_id}/edit")
    # Should show edit form title
    await logged_in_user.should_see("Artikel bearbeiten")
    # Should show product name
    await logged_in_user.should_see("Testmilch")


async def test_edit_item_page_shows_404_for_nonexistent_item(logged_in_user: User) -> None:
    """Test that edit page shows error for non-existent item."""
    await logged_in_user.open("/items/99999/edit")
    await logged_in_user.should_see("nicht gefunden")


async def test_edit_item_shows_category_optional_for_purchased_fresh(
    logged_in_user: User, isolated_test_database
) -> None:
    """Kategorie-Feld wird als optional fuer PURCHASED_FRESH Items angezeigt."""
    with Session(isolated_test_database) as session:
        location = location_service.create_location(
            session=session,
            name="Kuehlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        category_service.create_category(
            session=session,
            name="Milchprodukte",
            created_by=1,
        )
        item = item_service.create_item(
            session=session,
            product_name="Frischmilch",
            best_before_date=date(2025, 12, 31),
            quantity=1.0,
            unit="L",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=1,
        )
        item_id = item.id

    await logged_in_user.open(f"/items/{item_id}/edit")
    await logged_in_user.should_see("Kategorie (optional)")


async def test_edit_item_shows_category_required_for_homemade_frozen(
    logged_in_user: User, isolated_test_database
) -> None:
    """Kategorie-Feld wird als Pflichtfeld fuer HOMEMADE_FROZEN Items angezeigt."""
    with Session(isolated_test_database) as session:
        location = location_service.create_location(
            session=session,
            name="Tiefkuehler",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        category_service.create_category(
            session=session,
            name="Gemuese",
            created_by=1,
        )
        item = item_service.create_item(
            session=session,
            product_name="Erbsen",
            best_before_date=date(2025, 6, 15),
            quantity=500,
            unit="g",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=location.id,
            created_by=1,
            freeze_date=date(2025, 6, 15),
        )
        item_id = item.id

    await logged_in_user.open(f"/items/{item_id}/edit")
    await logged_in_user.should_see("Kategorie *")
