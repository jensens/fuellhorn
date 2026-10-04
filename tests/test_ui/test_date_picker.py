"""UI: gestufte Datumsauswahl Jahr, Monat, Tag mit optionalem Tag (Issue #346).

Der alte Kalender zwang zum Durchklicken der Monate; für Herstellungsdaten, die Jahre
zurückliegen, war das mühsam. Die Auswahl zeigt Jahre, Monate und Tage direkt.
"""

from app.models import Category
from app.models import Item
from app.models import Location
from app.models import LocationType
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


PICKER = "wizard-date-input-picker"


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    with Session(isolated_test_database) as session:
        pantry = Location(name="Speis", location_type=LocationType.AMBIENT, created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([pantry, dairy])
        session.commit()
        session.refresh(pantry)
        session.refresh(dairy)
        assert pantry.id is not None and dairy.id is not None
        return {"pantry": pantry.id, "dairy": dairy.id}


async def _open_step2(user: User, world: dict[str, int], name: str = "Apfelmus") -> None:
    await user.open("/items/add")
    await user.should_see("Schritt 1 von 3")
    user.find("z.B. Tomaten aus Garten").type(name)
    user.find(marker="item-type-chip-purchased_fresh").click()
    user.find(kind=ui.number).elements.pop().set_value(1)
    user.find(marker="unit-chip-Stück").click()
    user.find("Weiter").click()
    await user.should_see("Schritt 2 von 3")
    user.find(marker=f"category-chip-{world['dairy']}").click()


def _input_value(user: User) -> str:
    (field,) = user.find(kind=ui.input, marker="wizard-date-input").elements
    return str(field.value)


def _markers(user: User, prefix: str) -> set[str]:
    assert user.client is not None
    return {
        marker
        for element in user.client.layout.descendants()
        for marker in getattr(element, "_markers", [])
        if marker.startswith(prefix)
    }


async def test_picking_year_month_and_day_fills_the_field(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    await _open_step2(logged_in_user, world)

    logged_in_user.find(marker=f"{PICKER}-year-2027").click()
    logged_in_user.find(marker=f"{PICKER}-month-3").click()
    logged_in_user.find(marker=f"{PICKER}-day-15").click()

    assert _input_value(logged_in_user) == "15.03.2027"

    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{world['pantry']}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item).where(Item.product_name == "Apfelmus")).one()
    assert (item.best_before_date, item.best_before_month_only) == (date(2027, 3, 15), False)


async def test_taking_a_month_without_a_day(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Akzeptanzkriterium #347: ohne Tag wird der 1. gespeichert und als Monat angezeigt."""
    await _open_step2(logged_in_user, world, name="Marmelade")

    logged_in_user.find(marker=f"{PICKER}-year-2027").click()
    logged_in_user.find(marker=f"{PICKER}-month-3").click()
    logged_in_user.find(marker=f"{PICKER}-month-only").click()

    assert _input_value(logged_in_user) == "03/2027"

    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{world['pantry']}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item).where(Item.product_name == "Marmelade")).one()
    assert (item.best_before_date, item.best_before_month_only) == (date(2027, 3, 1), True)


async def test_earlier_years_are_one_click_away(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Vergangene Herstellungsdaten brauchen kein Durchklicken der Monate (Issue #346)."""
    await _open_step2(logged_in_user, world)
    this_year = date.today().year
    assert f"{PICKER}-year-{this_year - 7}" not in _markers(logged_in_user, f"{PICKER}-year-")

    logged_in_user.find(marker=f"{PICKER}-year-earlier").click()

    assert f"{PICKER}-year-{this_year - 7}" in _markers(logged_in_user, f"{PICKER}-year-")


async def test_day_count_follows_the_month(logged_in_user: User, isolated_test_database, world: dict[str, int]) -> None:
    await _open_step2(logged_in_user, world)

    logged_in_user.find(marker=f"{PICKER}-year-2028").click()
    logged_in_user.find(marker=f"{PICKER}-month-2").click()
    assert f"{PICKER}-day-29" in _markers(logged_in_user, f"{PICKER}-day-")
    assert f"{PICKER}-day-30" not in _markers(logged_in_user, f"{PICKER}-day-")

    logged_in_user.find(marker=f"{PICKER}-year-2027").click()
    logged_in_user.find(marker=f"{PICKER}-month-2").click()
    assert f"{PICKER}-day-28" in _markers(logged_in_user, f"{PICKER}-day-")
    assert f"{PICKER}-day-29" not in _markers(logged_in_user, f"{PICKER}-day-")


async def test_both_date_fields_have_their_own_picker(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Bei „Selbst eingefroren“ stehen zwei Datumsfelder auf der Seite; die Marker dürfen sich nicht mischen."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")
    logged_in_user.find("z.B. Tomaten aus Garten").type("Bohnen")
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    logged_in_user.find(kind=ui.number).elements.pop().set_value(1)
    logged_in_user.find(marker="unit-chip-Stück").click()
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 2 von 3")

    assert f"{PICKER}-month-3" in _markers(logged_in_user, PICKER)
    assert "wizard-freeze-date-input-picker-month-3" in _markers(logged_in_user, "wizard-freeze-date-input-picker")
