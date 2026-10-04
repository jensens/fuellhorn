"""UI-Tests: Lösch-Dialoge zeigen die Service-Meldung statt roher Exceptions (Issue #379)."""

from app.models import Item
from app.models import ItemType
from datetime import date
from nicegui.testing import User as TestUser
from sqlmodel import Session


def _add_item(engine, *, location_id: int, category_id: int | None = None, created_by: int = 1) -> None:
    with Session(engine) as session:
        session.add(
            Item(
                product_name="Blocker",
                best_before_date=date(2027, 1, 1),
                quantity=1,
                unit="Stück",
                item_type=ItemType.PURCHASED_FRESH,
                location_id=location_id,
                category_id=category_id,
                created_by=created_by,
            )
        )
        session.commit()


async def test_category_in_use_shows_message_and_keeps_category(
    logged_in_user: TestUser, standard_categories, standard_locations, isolated_test_database
) -> None:
    _add_item(isolated_test_database, location_id=100, category_id=101)  # Fleisch

    await logged_in_user.open("/admin/categories")
    logged_in_user.find(marker="delete-Fleisch").click()
    logged_in_user.find("Löschen").click()

    await logged_in_user.should_see("1 Artikel")
    await logged_in_user.should_see("Kategorie löschen")  # Dialog bleibt offen
    with Session(isolated_test_database) as session:
        from app.services import category_service

        assert category_service.get_category(session, 101) is not None


async def test_location_in_use_message_comes_from_service(
    logged_in_user: TestUser, standard_locations, isolated_test_database
) -> None:
    _add_item(isolated_test_database, location_id=100)  # Kühlschrank

    await logged_in_user.open("/admin/locations")
    logged_in_user.find(marker="delete-Kühlschrank").click()
    logged_in_user.find("Löschen").click()

    await logged_in_user.should_see("in Verwendung")
    await logged_in_user.should_see("eaktivier")


async def test_user_with_items_shows_message_and_keeps_user(
    logged_in_user: TestUser, standard_users, standard_locations, isolated_test_database
) -> None:
    with Session(isolated_test_database) as session:
        from app.services.auth_service import get_user_by_username

        user_id = get_user_by_username(session, "testuser2").id
    _add_item(isolated_test_database, location_id=100, created_by=user_id)

    await logged_in_user.open("/admin/users")
    logged_in_user.find(marker="delete-testuser2").click()
    logged_in_user.find("Löschen").click()

    await logged_in_user.should_see("1 Artikel")
    await logged_in_user.should_see("Benutzer löschen")  # Dialog bleibt offen
