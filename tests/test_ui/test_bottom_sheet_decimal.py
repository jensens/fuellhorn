"""UI Tests: Teilentnahme mit Dezimalmengen im Bottom-Sheet (Issue #365).

Vorher: ``ui.number(min=1, step=1)`` plus ``int()``-Casts, 0,5 kg wurden als
'0 kg entnommen' gemeldet und 'Verfügbar: 2 kg' bei 2,5 kg angezeigt.
"""

from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from datetime import date
from datetime import timedelta
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="flour_item_id")
def flour_item_id_fixture(isolated_test_database) -> int:
    """2,5 kg Mehl im Vorratsraum."""
    with Session(isolated_test_database) as session:
        location = Location(name="Vorratsraum", location_type=LocationType.AMBIENT, created_by=1)
        session.add(location)
        session.commit()
        session.refresh(location)
        item = Item(
            product_name="Mehl",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=2.5,
            unit="kg",
            location_id=location.id,  # type: ignore[arg-type]
            best_before_date=date.today() + timedelta(days=90),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None
        return item.id


async def test_withdraw_dialog_shows_decimal_available_quantity(user: User, flour_item_id: int) -> None:
    """Der Dialog zeigt 'Verfügbar: 2.5 kg', nicht abgeschnitten '2 kg'."""
    await user.open(f"/test/bottom-sheet/{flour_item_id}")
    user.find("Teilentnahme").click()
    await user.should_see("Verfügbar: 2.5 kg")


async def test_withdraw_half_kilogram(logged_in_user: User, isolated_test_database, flour_item_id: int) -> None:
    """0,5 kg entnehmen → Toast '0.5 kg entnommen' und Rest 2,0 kg in der DB."""
    await logged_in_user.open(f"/test/bottom-sheet/{flour_item_id}")
    logged_in_user.find("Teilentnahme").click()
    number_input = logged_in_user.find(kind=ui.number).elements.pop()
    number_input.set_value(0.5)
    logged_in_user.find("Bestätigen").click()
    await logged_in_user.should_see("0.5 kg entnommen")

    with Session(isolated_test_database) as session:
        item = session.get(Item, flour_item_id)
    assert item is not None and item.quantity == 2.0


async def test_withdraw_input_allows_quantities_below_one(user: User, flour_item_id: int) -> None:
    """Das Mengenfeld hat keine Untergrenze von 1 mehr."""
    await user.open(f"/test/bottom-sheet/{flour_item_id}")
    user.find("Teilentnahme").click()
    number_input = user.find(kind=ui.number).elements.pop()
    assert (number_input.min or 0) < 1
