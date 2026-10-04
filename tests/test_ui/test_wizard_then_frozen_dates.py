"""UI-Tests: Datums-Semantik und -Beschriftung für PURCHASED_THEN_FROZEN (Issue #387)."""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import item_service
from datetime import date
from datetime import timedelta
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="freezer_world")
def freezer_world_fixture(isolated_test_database) -> dict:
    with Session(isolated_test_database) as session:
        freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=1)
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        category = Category(name="Fleisch", created_by=1)
        session.add_all([freezer, fridge, category])
        session.commit()
        for obj in (freezer, fridge, category):
            session.refresh(obj)
        assert category.id is not None
        session.add(
            CategoryShelfLife(category_id=category.id, storage_type=StorageType.FROZEN, months_min=3, months_max=6)
        )
        session.commit()
        return {"freezer": freezer.id, "fridge": fridge.id, "category": category.id}


def _set_quantity(user: User, quantity: float) -> None:
    number_input = user.find(kind=ui.number).elements.pop()
    number_input.set_value(quantity)


def _type_date(user: User, marker: str, value: date) -> None:
    field = user.find(marker=marker)
    field.clear()
    field.type(value.strftime("%d.%m.%Y"))


async def test_wizard_then_frozen_with_freeze_date_yesterday_is_saved(
    logged_in_user: User, isolated_test_database, freezer_world: dict
) -> None:
    """Akzeptanzkriterium: PURCHASED_THEN_FROZEN mit Einfrierdatum gestern → speicherbar; best_before spiegelt es."""
    yesterday = date.today() - timedelta(days=1)
    await logged_in_user.open("/items/add")
    logged_in_user.find("z.B. Tomaten aus Garten").type("Hackfleisch")
    logged_in_user.find(marker="item-type-chip-purchased_then_frozen").click()
    _set_quantity(logged_in_user, 500)
    logged_in_user.find(marker="unit-chip-g").click()
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 2 von 3")
    await logged_in_user.should_see("Eingefroren am *")
    logged_in_user.find(marker=f"category-chip-{freezer_world['category']}").click()
    _type_date(logged_in_user, "wizard-date-input", yesterday)
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    await logged_in_user.should_see(f"Eingefroren: {yesterday.strftime('%d.%m.%Y')}")
    await logged_in_user.should_not_see("Datum:")
    logged_in_user.find(marker=f"location-chip-{freezer_world['freezer']}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item)).one()
    assert item.freeze_date == yesterday
    assert item.best_before_date == yesterday


async def test_wizard_summary_labels_follow_item_type(logged_in_user: User, freezer_world: dict) -> None:
    """Selbst eingefroren: Zusammenfassung sagt 'Hergestellt' und 'Eingefroren', nicht 'Datum'."""
    await logged_in_user.open("/items/add")
    logged_in_user.find("z.B. Tomaten aus Garten").type("Kürbissuppe")
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    _set_quantity(logged_in_user, 1)
    logged_in_user.find(marker="unit-chip-l").click()
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Hergestellt am *")
    await logged_in_user.should_see("Eingefroren am *")
    logged_in_user.find(marker=f"category-chip-{freezer_world['category']}").click()
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    await logged_in_user.should_see("Hergestellt:")
    await logged_in_user.should_see("Eingefroren:")
    await logged_in_user.should_not_see("Datum:")


async def test_edit_view_hides_derived_date_for_then_frozen(
    logged_in_user: User, isolated_test_database, freezer_world: dict
) -> None:
    """Edit-View zeigt für PURCHASED_THEN_FROZEN nur 'Eingefroren am' (kein 'Einkaufsdatum')."""
    with Session(isolated_test_database) as session:
        item = item_service.create_item(
            session=session,
            product_name="Hackfleisch",
            best_before_date=date(2026, 9, 30),
            quantity=500,
            unit="g",
            item_type=ItemType.PURCHASED_THEN_FROZEN,
            location_id=freezer_world["freezer"],
            created_by=1,
            category_id=freezer_world["category"],
            freeze_date=date(2026, 9, 30),
        )
        item_id = item.id

    await logged_in_user.open(f"/items/{item_id}/edit")
    await logged_in_user.should_see("Eingefroren am *")
    await logged_in_user.should_not_see("Einkaufsdatum")
    await logged_in_user.should_not_see(marker="edit-best-before-section")

    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    await logged_in_user.should_see("Hergestellt am *")
    await logged_in_user.should_see(marker="edit-best-before-section")
