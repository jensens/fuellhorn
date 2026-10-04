"""UI Tests: Navigationsziele auf echten Seiten (Issue #366).

Vorher: der CTA im leeren Vorrat führte nach ``/add-item`` (404) und jede Zeile in
"Kürzlich hinzugefügt" nach ``/items/{id}`` (404, es gibt keine Detailseite).
"""

from app.models import ItemType
from app.models import LocationType
from app.services import item_service
from app.services import location_service
from datetime import date
from datetime import timedelta
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="recent_item_id")
def recent_item_id_fixture(isolated_test_database) -> int:
    """Ein frisch erfasster Artikel im Kühlschrank."""
    with Session(isolated_test_database) as session:
        fridge = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, created_by=1)
        item = item_service.create_item(
            session,
            product_name="Joghurt",
            best_before_date=date.today() + timedelta(days=10),
            quantity=4,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,  # type: ignore[arg-type]
            created_by=1,
        )
        assert item.id is not None
        return item.id


async def test_empty_inventory_cta_opens_wizard(logged_in_user: User) -> None:
    """'Artikel erfassen' im leeren Vorrat öffnet Schritt 1 des Wizards."""
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Keine Artikel vorhanden")
    logged_in_user.find("Artikel erfassen").click()
    await logged_in_user.should_see("Schritt 1 von 3")


async def test_recently_added_row_opens_edit_page(logged_in_user: User, recent_item_id: int) -> None:
    """Ein Tap auf eine Zeile in 'Kürzlich hinzugefügt' öffnet den Edit-View des Artikels."""
    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Kürzlich hinzugefügt")
    logged_in_user.find(marker=f"recent-item-{recent_item_id}").click()
    await logged_in_user.should_see("Artikel bearbeiten")
    await logged_in_user.should_see("Joghurt")
