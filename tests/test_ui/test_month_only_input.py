"""UI: Datum ohne Tag erfassen, anzeigen und bearbeiten (Issues #346, #347)."""

from app.models import Category
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    """Kühlschrank und eine Kategorie ohne Haltbarkeitsdaten, passend für frisch Gekauftes."""
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, dairy])
        session.commit()
        session.refresh(fridge)
        session.refresh(dairy)
        assert fridge.id is not None and dairy.id is not None
        return {"fridge": fridge.id, "dairy": dairy.id}


def _type_date(user: User, marker: str, value: str) -> None:
    field = user.find(marker=marker)
    field.clear()
    field.type(value)


async def _fill_step1(user: User, name: str) -> None:
    await user.should_see("Schritt 1 von 3")
    user.find("z.B. Tomaten aus Garten").type(name)
    user.find(marker="item-type-chip-purchased_fresh").click()
    user.find(kind=ui.number).elements.pop().set_value(1)
    user.find(marker="unit-chip-l").click()
    user.find("Weiter").click()


async def test_wizard_saves_a_month_without_a_day(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Akzeptanzkriterium: „03/2026“ wird als 01.03.2026 mit Kennzeichen gespeichert."""
    await logged_in_user.open("/items/add")
    await _fill_step1(logged_in_user, "Milch")

    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['dairy']}").click()
    _type_date(logged_in_user, "wizard-date-input", "03/2026")
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{world['fridge']}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item).where(Item.product_name == "Milch")).one()
    assert (item.best_before_date, item.best_before_month_only) == (date(2026, 3, 1), True)


async def test_wizard_summary_shows_month_and_year(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    await logged_in_user.open("/items/add")
    await _fill_step1(logged_in_user, "Sahne")

    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['dairy']}").click()
    _type_date(logged_in_user, "wizard-date-input", "03/2026")
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    await logged_in_user.should_see("MHD: 03/2026")


async def test_dashboard_shows_the_entered_month(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """„Zuletzt erfasst“ zeigt die Eingabe, nicht den 1. des Monats."""
    with Session(isolated_test_database) as session:
        item_service.create_item(
            session,
            product_name="Butter",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=1,
            category_id=world["dairy"],
        )

    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Butter")

    await logged_in_user.should_see("MHD 03/2026")
    await logged_in_user.should_not_see("01.03.2026")


async def test_edit_keeps_and_changes_the_precision(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    with Session(isolated_test_database) as session:
        item = item_service.create_item(
            session,
            product_name="Käse",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=1,
            category_id=world["dairy"],
        )
        item_id = item.id
    assert item_id is not None

    await logged_in_user.open(f"/items/{item_id}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")
    (date_input,) = logged_in_user.find(kind=ui.input, marker="edit-date-input").elements
    assert date_input.value == "03/2026", "die Bearbeiten-Ansicht zeigt die Monatsangabe"

    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")
    with Session(isolated_test_database) as session:
        kept = session.get(Item, item_id)
    assert kept is not None and (kept.best_before_date, kept.best_before_month_only) == (date(2026, 3, 1), True)

    await logged_in_user.open(f"/items/{item_id}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")
    _type_date(logged_in_user, "edit-date-input", "17.05.2026")
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        changed = session.get(Item, item_id)
    assert changed is not None
    assert (changed.best_before_date, changed.best_before_month_only) == (date(2026, 5, 17), False)
