"""UI-Tests Schnellerfassung im Keller (Issue #463).

Unten im Keller steht man vor der Truhe und will nur Name, Menge, Einheit und Typ
eintippen. Der Lagerort wird einmal gewählt und bleibt, die Seite bleibt offen, und
was fehlt, wird oben im Warmen über die Nachpflege-Liste ergänzt.
"""

from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import User as UserModel
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="places")
def places_fixture(isolated_test_database) -> dict[str, int]:
    """Truhe im Keller (gefroren) und Vorratsregal (Raumtemperatur)."""
    with Session(isolated_test_database) as session:
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=1)
        pantry = Location(name="Vorratsregal", location_type=LocationType.AMBIENT, created_by=1)
        session.add_all([freezer, pantry])
        session.commit()
        session.refresh(freezer)
        session.refresh(pantry)
        assert freezer.id is not None and pantry.id is not None
        return {"freezer": freezer.id, "pantry": pantry.id}


async def _choose_location(user: User, location_id: int) -> None:
    """Ort antippen und warten, bis das Formular neu aufgebaut ist (``refresh`` läuft im nächsten Tick)."""
    user.find(marker=f"location-chip-{location_id}").click()
    await user.should_see(marker="quick-name")


async def _save_and_wait(user: User, count: int) -> None:
    """Erfassen und warten, bis die Liste den Artikel zeigt und das Formular frei ist."""
    user.find(marker="quick-save").click()
    await user.should_see(f"Gerade erfasst ({count})")


def _set_quantity(user: User, quantity: float) -> None:
    """Menge setzen (``ui.number`` versteht ``type()`` der User-Fixture nicht)."""
    user.find(kind=ui.number).elements.pop().set_value(quantity)


def _set_admin_active(database, *, active: bool) -> None:
    with Session(database) as session:
        admin = session.exec(select(UserModel).where(UserModel.username == "admin")).one()
        admin.is_active = active
        session.add(admin)
        session.commit()


def _items(database) -> list[Item]:
    with Session(database) as session:
        return sorted(session.exec(select(Item)).all(), key=lambda item: item.id or 0)


async def test_capturing_two_items_without_leaving_the_page(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Akzeptanzkriterium: Nach dem Erfassen geht es sofort mit dem nächsten Artikel weiter."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])

    logged_in_user.find(marker="quick-name").type("Erbsen")
    _set_quantity(logged_in_user, 3)
    logged_in_user.find(marker="unit-chip-Packung").click()
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    await _save_and_wait(logged_in_user, 1)
    await logged_in_user.should_see("3 Packung Erbsen")

    logged_in_user.find(marker="quick-name").type("Kirschen")
    await _save_and_wait(logged_in_user, 2)
    await logged_in_user.should_see("3 Packung Kirschen")

    captured = _items(isolated_test_database)
    assert [item.product_name for item in captured] == ["Erbsen", "Kirschen"]
    for item in captured:
        assert item.location_id == places["freezer"]
        assert item.item_type == ItemType.HOMEMADE_FROZEN
        assert item.unit == "Packung"
        assert item.quantity == 3
        assert (item.best_before_date, item.freeze_date, item.category_id) == (None, None, None)


async def test_the_name_field_is_empty_again_after_capturing(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Ort, Einheit und Typ bleiben stehen, nur der Name wird frei."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["pantry"])
    logged_in_user.find(marker="quick-name").type("Marmelade")
    _set_quantity(logged_in_user, 2)
    logged_in_user.find(marker="unit-chip-Stück").click()
    logged_in_user.find(marker="item-type-chip-homemade_preserved").click()
    await _save_and_wait(logged_in_user, 1)
    await logged_in_user.should_see("Marmelade")

    assert logged_in_user.find(marker="quick-name", kind=ui.input).elements.pop().value == ""
    assert logged_in_user.find(kind=ui.number).elements.pop().value == 2


async def test_type_chips_are_limited_to_the_chosen_location(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """In der Truhe gibt es nichts Frisches; im Regal nichts Gefrorenes."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])
    await logged_in_user.should_see(marker="item-type-chip-homemade_frozen")
    await logged_in_user.should_not_see(marker="item-type-chip-purchased_fresh")

    await _choose_location(logged_in_user, places["pantry"])
    await logged_in_user.should_see(marker="item-type-chip-purchased_fresh")
    await logged_in_user.should_not_see(marker="item-type-chip-homemade_frozen")


async def test_name_stays_required(logged_in_user: User, isolated_test_database, places: dict[str, int]) -> None:
    """Ohne Name entsteht kein Artikel; die Meldung sagt, was fehlt."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    logged_in_user.find(marker="quick-save").click()

    await logged_in_user.should_see("Mindestens 2 Zeichen erforderlich")
    assert _items(isolated_test_database) == []


async def test_finishing_leads_to_the_completion_list(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Oben im Warmen geht es mit der Nachpflege weiter."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])
    logged_in_user.find(marker="quick-name").type("Zwetschken")
    _set_quantity(logged_in_user, 1)
    logged_in_user.find(marker="unit-chip-Packung").click()
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()
    await _save_and_wait(logged_in_user, 1)
    await logged_in_user.should_see("Zwetschken")

    logged_in_user.find(marker="quick-finish").click()
    await logged_in_user.should_see("Nachpflegen (1)", retries=50)


async def test_dashboard_offers_the_quick_capture(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Der Weg in den Keller beginnt auf dem Dashboard."""
    await logged_in_user.open("/dashboard")

    logged_in_user.find(marker="dashboard-quick").click()
    await logged_in_user.should_see("Schnellerfassung", retries=50)


async def test_quick_capture_requires_auth(user: User, isolated_test_database) -> None:
    """Ohne Anmeldung landet man auf dem Login."""
    await user.open("/items/quick")
    await user.should_see("Benutzername")


async def test_captured_items_show_up_as_unknown_in_stock(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Die Ware steht physisch da, also ist sie sofort im Bestand - ohne Haltbarkeitsdaten."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])
    logged_in_user.find(marker="quick-name").type("Rhabarber")
    _set_quantity(logged_in_user, 1)
    logged_in_user.find(marker="unit-chip-kg").click()
    logged_in_user.find(marker="item-type-chip-purchased_then_frozen").click()
    await _save_and_wait(logged_in_user, 1)
    await logged_in_user.should_see("Rhabarber")

    await logged_in_user.open("/items")
    await logged_in_user.should_see("Rhabarber", retries=50)
    await logged_in_user.should_see("Keine Haltbarkeitsdaten")
    assert _items(isolated_test_database)[0].created_at.date() == date.today()


async def test_deactivated_user_cannot_capture_anymore(
    logged_in_user: User, isolated_test_database, places: dict[str, int]
) -> None:
    """Berechtigung wird beim Klick geprüft, nicht nur beim Seitenaufbau (wie im Wizard, Issue #381)."""
    await logged_in_user.open("/items/quick")
    await _choose_location(logged_in_user, places["freezer"])
    logged_in_user.find(marker="quick-name").type("Erbsen")
    logged_in_user.find(marker="item-type-chip-homemade_frozen").click()

    _set_admin_active(isolated_test_database, active=False)
    try:
        logged_in_user.find(marker="quick-save").click()
        await logged_in_user.should_see("Bitte neu anmelden")
    finally:
        _set_admin_active(isolated_test_database, active=True)

    assert _items(isolated_test_database) == []
