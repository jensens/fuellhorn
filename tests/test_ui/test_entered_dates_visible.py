"""UI Tests: Erfasste Daten sind nach dem Speichern sichtbar (Issue #342).

Dashboard-Liste "Kürzlich hinzugefügt" und Bottom-Sheet zeigen das eingegebene
Herstellungs-/Einfrierdatum zusätzlich zum errechneten Haltbarkeitsdatum.
"""

from app.models import ItemType
from app.models import LocationType
from app.models import StorageType
from app.services import category_service
from app.services import item_service
from app.services import location_service
from app.services import shelf_life_service
from datetime import date
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="soup_id")
def soup_id_fixture(isolated_test_database) -> int:
    """Kürbissuppe, hergestellt 01.09.2026, eingefroren 02.09.2026, Haltbarkeit 2–3 Monate."""
    with Session(isolated_test_database) as session:
        freezer = location_service.create_location(session, "Truhe", LocationType.FROZEN, created_by=1)
        soups = category_service.create_category(session, "Suppen", created_by=1)
        assert soups.id is not None
        shelf_life_service.create_shelf_life(session, soups.id, StorageType.FROZEN, months_min=2, months_max=3)
        item = item_service.create_item(
            session,
            product_name="Kürbissuppe",
            best_before_date=date(2026, 9, 1),
            quantity=1,
            unit="l",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=freezer.id,  # type: ignore[arg-type]
            created_by=1,
            category_id=soups.id,
            freeze_date=date(2026, 9, 2),
        )
        assert item.id is not None
        return item.id


async def test_recently_added_row_shows_entered_dates(logged_in_user: User, soup_id: int) -> None:
    """Die Zeile in 'Kürzlich hinzugefügt' nennt Herstellungs- und Einfrierdatum."""
    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Kürzlich hinzugefügt")
    await logged_in_user.should_see("Hergestellt am 01.09.2026")
    await logged_in_user.should_see("Eingefroren am 02.09.2026")


async def test_bottom_sheet_shows_entered_dates_next_to_expiry(user: User, soup_id: int) -> None:
    """Das Bottom-Sheet zeigt die Eingabedaten und weiterhin das errechnete Idealdatum."""
    await user.open(f"/test/bottom-sheet/{soup_id}")
    await user.should_see("Hergestellt am")
    await user.should_see("01.09.2026")
    await user.should_see("Eingefroren am")
    await user.should_see("02.09.2026")
    await user.should_see("Ideal bis")
    await user.should_see("02.11.2026")  # Einfrierdatum + 2 Monate
