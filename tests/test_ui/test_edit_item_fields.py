"""UI-Tests Edit-View: Felder leeren, Re-Validierung vor dem Speichern, Typwechsel (Issue #386)."""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import item_service
from datetime import date
from nicegui.testing import User
import pytest
from sqlmodel import Session


NOTES_PLACEHOLDER = "z.B. je 12 Stück, 300g pro Packung"


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict:
    """Kühlschrank + Truhe, Kategorie mit FROZEN-Haltbarkeit und eine ohne; Milch (frisch) und Pizza (TK)."""
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=1)
        frozen_cat = Category(name="Fertiggerichte", created_by=1)
        bare_cat = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, freezer, frozen_cat, bare_cat])
        session.commit()
        for obj in (fridge, freezer, frozen_cat, bare_cat):
            session.refresh(obj)
        assert frozen_cat.id is not None and fridge.id is not None and freezer.id is not None
        session.add(
            CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=2, months_max=6)
        )
        session.commit()
        milk = item_service.create_item(
            session=session,
            product_name="Milch",
            best_before_date=date(2027, 1, 15),
            quantity=1.0,
            unit="l",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,
            created_by=1,
            category_id=bare_cat.id,
            notes="noch 2 Packungen",
        )
        pizza = item_service.create_item(
            session=session,
            product_name="Pizza",
            best_before_date=date(2026, 9, 1),
            quantity=2,
            unit="Stück",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=freezer.id,
            created_by=1,
            category_id=frozen_cat.id,
        )
        assert milk.id is not None and pizza.id is not None
        return {"milk": milk.id, "pizza": pizza.id, "fridge": fridge.id, "freezer": freezer.id}


def _is_disabled(user: User, marker: str) -> bool:
    element = user.find(marker=marker).elements.pop()
    return bool(element._props.get("disabled") or element._props.get("disable")) or not getattr(
        element, "enabled", True
    )


def _click_as_if_still_enabled(user: User, marker: str) -> None:
    """Simuliert den Race aus dem Issue: Der Browser zeigte den Button noch aktiv, der Klick erreicht den Server.

    Die User-Fixture ignoriert Klicks auf deaktivierte Elemente (wie NiceGUI serverseitig), deshalb wird
    der Button für den Klick kurz wieder aktiviert; der Handler muss selbst re-validieren.
    """
    button = user.find(marker=marker).elements.pop()
    button.enable()  # type: ignore[attr-defined]
    user.find(marker=marker).click()


async def test_clearing_notes_persists_empty_notes(logged_in_user: User, isolated_test_database, world: dict) -> None:
    """Akzeptanzkriterium: Notiz löschen und speichern → DB leer."""
    await logged_in_user.open(f"/items/{world['milk']}/edit")
    await logged_in_user.should_see("noch 2 Packungen")

    logged_in_user.find(NOTES_PLACEHOLDER).clear()
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        assert item_service.get_item(session, world["milk"]).notes is None


async def test_switch_to_homemade_frozen_without_freeze_date_is_refused_with_message(
    logged_in_user: User, isolated_test_database, world: dict
) -> None:
    """Akzeptanzkriterium: Typwechsel auf HOMEMADE_FROZEN, Einfrierdatum geleert → kein Speichern, Meldung."""
    await logged_in_user.open(f"/items/{world['pizza']}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")

    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    await logged_in_user.should_see("Eingefroren am *")
    logged_in_user.find(marker="edit-freeze-date-input").clear()

    assert _is_disabled(logged_in_user, "edit-save")
    # Ein bereits abgeschickter Klick (Race) darf trotzdem nichts speichern
    _click_as_if_still_enabled(logged_in_user, "edit-save")
    await logged_in_user.should_see("Einfrierdatum erforderlich")
    await logged_in_user.should_not_see("gespeichert")

    with Session(isolated_test_database) as session:
        assert item_service.get_item(session, world["pizza"]).item_type == ItemType.PURCHASED_FROZEN


async def test_switch_to_frozen_type_prefills_freeze_date_and_saves_it(
    logged_in_user: User, isolated_test_database, world: dict
) -> None:
    """Typwechsel auf HOMEMADE_FROZEN setzt ein Einfrierdatum (heute) in form_data, nicht nur im Feld."""
    await logged_in_user.open(f"/items/{world['pizza']}/edit")
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    await logged_in_user.should_see("Hergestellt am *")

    assert not _is_disabled(logged_in_user, "edit-save")
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        pizza = item_service.get_item(session, world["pizza"])
    assert pizza.item_type == ItemType.HOMEMADE_FROZEN
    assert pizza.freeze_date == date.today()


async def test_switch_away_from_frozen_type_clears_freeze_date(
    logged_in_user: User, isolated_test_database, world: dict
) -> None:
    """Gefroren → TK-Ware gekauft: das Einfrierdatum wird geleert statt still weitergeschleppt."""
    with Session(isolated_test_database) as session:
        item_service.update_item(
            session, world["pizza"], item_type=ItemType.PURCHASED_THEN_FROZEN, freeze_date=date(2026, 9, 1)
        )

    await logged_in_user.open(f"/items/{world['pizza']}/edit")
    await logged_in_user.should_see("Eingefroren am *")
    logged_in_user.find(marker="item-type-chip-purchased_frozen").click()
    await logged_in_user.should_see("Mindesthaltbarkeitsdatum (MHD) *")
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        pizza = item_service.get_item(session, world["pizza"])
    assert pizza.item_type == ItemType.PURCHASED_FROZEN
    assert pizza.freeze_date is None


async def test_blank_product_name_is_refused_even_if_click_gets_through(
    logged_in_user: User, isolated_test_database, world: dict
) -> None:
    """Edit re-validiert vor dem Speichern wie der Wizard (2-Zeichen-Minimum, getrimmt)."""
    await logged_in_user.open(f"/items/{world['milk']}/edit")
    name_input = logged_in_user.find("z.B. Tomaten aus Garten")
    name_input.clear()
    name_input.type(" ")

    assert _is_disabled(logged_in_user, "edit-save")
    _click_as_if_still_enabled(logged_in_user, "edit-save")
    await logged_in_user.should_see("Mindestens 2 Zeichen")

    with Session(isolated_test_database) as session:
        assert item_service.get_item(session, world["milk"]).product_name == "Milch"
