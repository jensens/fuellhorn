"""UI-Tests: veraltete Smart-Defaults werden im Wizard verworfen (Issue #385).

Szenario aus dem Issue: TK-Ware in der Tiefkühltruhe erfassen ("Speichern &
Nächster"), danach frischen Salat → der Lagerort-Default zeigte auf die Truhe,
Schritt 3 bot sie nicht an, prüfte aber nur ``is None`` → Speichern war aktiv und
der Salat landete in der Truhe.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict:
    """IDs von Tiefkühltruhe, Kühlschrank, TK-Kategorie und einer Kategorie ohne Haltbarkeit."""
    with Session(isolated_test_database) as session:
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=1)
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        frozen_cat = Category(name="Fertiggerichte", created_by=1)
        fresh_cat = Category(name="Salat", created_by=1)
        session.add_all([freezer, fridge, frozen_cat, fresh_cat])
        session.commit()
        for obj in (freezer, fridge, frozen_cat, fresh_cat):
            session.refresh(obj)
        assert frozen_cat.id is not None
        session.add(
            CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=3, months_max=6)
        )
        session.commit()
        return {
            "freezer": freezer.id,
            "fridge": fridge.id,
            "frozen_cat": frozen_cat.id,
            "fresh_cat": fresh_cat.id,
        }


def _set_quantity(user: User, quantity: float) -> None:
    number_input = user.find(kind=ui.number).elements.pop()
    number_input.set_value(quantity)


def _is_disabled(user: User, marker: str) -> bool:
    element = user.find(marker=marker).elements.pop()
    return bool(element._props.get("disabled"))


async def _step1(user: User, product_name: str, item_type: str, unit: str) -> None:
    await user.should_see("Schritt 1 von 3")
    user.find("z.B. Tomaten aus Garten").type(product_name)
    user.find(marker=f"item-type-chip-{item_type}").click()
    _set_quantity(user, 1)
    user.find(marker=f"unit-chip-{unit}").click()
    user.find("Weiter").click()


async def test_stale_location_default_is_dropped_after_type_change(
    logged_in_user: User, isolated_test_database, world: dict
) -> None:
    """Nach TK-Ware in der Truhe: frischer Salat hat keinen Lagerort vorgewählt, Speichern ist deaktiviert."""
    # 1) TK-Ware in der Tiefkühltruhe mit "Speichern & Nächster" erfassen → Smart-Defaults gesetzt
    await logged_in_user.open("/items/add")
    await _step1(logged_in_user, "Pizza", "purchased_frozen", "Stück")
    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['frozen_cat']}").click()
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{world['freezer']}").click()
    logged_in_user.find(marker="wizard-save-next").click()
    await logged_in_user.should_see("gespeichert")

    # 2) Nächster Artikel: frisch gekauft → Truhe ist kein gültiger Lagerort mehr
    await logged_in_user.should_see("Schritt 1 von 3")
    await _step1(logged_in_user, "Salat", "purchased_fresh", "Stück")
    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['fresh_cat']}").click()
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")

    await logged_in_user.should_not_see(marker=f"location-chip-{world['freezer']}")
    assert _is_disabled(logged_in_user, "wizard-save"), "Speichern muss ohne gültigen Lagerort deaktiviert sein"

    # 3) Kühlschrank wählen → Speichern möglich, Salat liegt im Kühlschrank
    logged_in_user.find(marker=f"location-chip-{world['fridge']}").click()
    assert not _is_disabled(logged_in_user, "wizard-save")
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        salad = session.exec(select(Item).where(Item.product_name == "Salat")).one()
    assert salad.location_id == world["fridge"]


async def test_stale_category_default_is_dropped_after_type_change(logged_in_user: User, world: dict) -> None:
    """Die TK-Kategorie bleibt nach dem Wechsel auf 'selbst eingemacht' nicht als unsichtbare Vorauswahl hängen."""
    await logged_in_user.open("/items/add")
    await _step1(logged_in_user, "Pizza", "purchased_frozen", "Stück")
    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['frozen_cat']}").click()
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")
    logged_in_user.find(marker=f"location-chip-{world['freezer']}").click()
    logged_in_user.find(marker="wizard-save-next").click()
    await logged_in_user.should_see("gespeichert")

    await logged_in_user.should_see("Schritt 1 von 3")
    await _step1(logged_in_user, "Marmelade", "homemade_preserved", "Stück")
    await logged_in_user.should_see("Schritt 2 von 3")

    await logged_in_user.should_not_see(marker=f"category-chip-{world['frozen_cat']}")
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Bitte alle Pflichtfelder ausfüllen")
    await logged_in_user.should_see("Schritt 2 von 3")
