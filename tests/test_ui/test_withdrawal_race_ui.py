"""UI: Bottom-Sheet mit veraltetem Bestand zeigt die Service-Meldung und lädt neu (Issue #394)."""

from app.models import Category
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import Withdrawal
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="joghurt")
def joghurt_fixture(isolated_test_database) -> int:
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, dairy])
        session.commit()
        session.refresh(fridge)
        session.refresh(dairy)
        assert fridge.id is not None
        item = item_service.create_item(
            session,
            product_name="Joghurt",
            best_before_date=date(2027, 1, 1),
            quantity=5,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,
            created_by=1,
            category_id=dairy.id,
        )
        assert item.id is not None
        return item.id


async def test_stale_sheet_withdrawal_shows_message_and_reloads(
    logged_in_user: User, isolated_test_database, joghurt: int
) -> None:
    await logged_in_user.open("/items")
    logged_in_user.find(marker=f"item-consume-{joghurt}").click()
    await logged_in_user.should_see("Teilentnahme")

    # Ein anderer Nutzer entnimmt inzwischen 3 Stück
    with Session(isolated_test_database) as session:
        item_service.withdraw_partial(session, joghurt, 3, 1)

    logged_in_user.find("Teilentnahme").click()
    await logged_in_user.should_see("Menge entnehmen")
    logged_in_user.find(kind=ui.number).elements.pop().set_value(3)
    logged_in_user.find("Bestätigen").click()

    await logged_in_user.should_see("Bestand hat sich geändert")
    await logged_in_user.should_see("2/5 Stück")  # Liste neu geladen, aktueller Bestand sichtbar

    with Session(isolated_test_database) as session:
        assert item_service.get_item(session, joghurt).quantity == 2
        assert [w.quantity for w in session.exec(select(Withdrawal)).all()] == [3]


async def test_consume_all_twice_shows_service_message(
    logged_in_user: User, isolated_test_database, joghurt: int
) -> None:
    await logged_in_user.open("/items")
    with Session(isolated_test_database) as session:
        item_service.mark_item_consumed(session, joghurt, 1)

    logged_in_user.find(marker=f"item-consume-{joghurt}").click()
    await logged_in_user.should_see("Teilentnahme")
    logged_in_user.find(marker="consume-button").click()

    await logged_in_user.should_see("bereits vollständig entnommen")
    with Session(isolated_test_database) as session:
        assert len(session.exec(select(Withdrawal)).all()) == 1
