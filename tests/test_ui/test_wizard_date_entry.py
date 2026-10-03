"""UI Tests: Eingegebene Daten im Wizard werden persistiert (Issue #362).

Treibt den echten 3-Schritt-Wizard über die NiceGUI-``User``-Fixture und
prüft das in der Datenbank gespeicherte Datum. Vor dem Fix erhielt jeder
Artikel ``date.today()``, weil das Datumsfeld nie an ``form_data`` gebunden war.
"""

from app.models import Item
from app.models import Location
from app.models import LocationType
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="chilled_location")
def chilled_location_fixture(isolated_test_database) -> Location:
    """Kühlschrank-Lagerort (gültig für PURCHASED_FRESH)."""
    with Session(isolated_test_database) as session:
        location = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        session.add(location)
        session.commit()
        session.refresh(location)
        return location


def _set_quantity(user: User, quantity: float) -> None:
    """Setzt die Menge (``ui.number`` unterstützt ``type()`` der User-Fixture nicht)."""
    number_input = user.find(kind=ui.number).elements.pop()
    number_input.set_value(quantity)


async def _fill_step1(user: User, product_name: str, item_type: str, quantity: float, unit: str) -> None:
    """Füllt Schritt 1 aus und klickt Weiter."""
    await user.should_see("Schritt 1 von 3")
    user.find("z.B. Tomaten aus Garten").type(product_name)
    user.find(marker=f"item-type-chip-{item_type}").click()
    _set_quantity(user, quantity)
    user.find(marker=f"unit-chip-{unit}").click()
    user.find("Weiter").click()


def _type_date(user: User, marker: str, value: str) -> None:
    """Leert ein Datumsfeld und tippt ein neues Datum (DD.MM.YYYY)."""
    field = user.find(marker=marker)
    field.clear()
    field.type(value)


async def test_wizard_persists_typed_best_before_date(
    logged_in_user: User, isolated_test_database, chilled_location: Location
) -> None:
    """Ein getipptes MHD landet als best_before_date in der Datenbank."""
    await logged_in_user.open("/items/add")
    await _fill_step1(logged_in_user, "Milch", "purchased_fresh", 1, "l")

    await logged_in_user.should_see("Schritt 2 von 3")
    _type_date(logged_in_user, "wizard-date-input", "15.01.2027")
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{chilled_location.id}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item)).one()
    assert item.best_before_date == date(2027, 1, 15)
