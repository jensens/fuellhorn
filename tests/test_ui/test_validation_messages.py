"""UI: Validierungsmeldungen pro Feld im Wizard und in der Edit-View, Mengenformat in der Zusammenfassung (Issue #396).

Vorher sah der Nutzer nur einen deaktivierten Button; die Texte aus ``validate_*`` wurden
ausschließlich auf Wahrheitswert geprüft, die Freigabe reagierte erst auf ``blur`` und die
Zusammenfassung zeigte "500.0 g".
"""

from app.models import Category
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


QUANTITY_MESSAGE = "Menge muss größer als 0 sein"
NAME_MESSAGE = "Mindestens 2 Zeichen erforderlich"
NAME_PLACEHOLDER = "z.B. Tomaten aus Garten"


@pytest.fixture(name="milk_id")
def milk_id_fixture(isolated_test_database) -> int:
    """Ein frischer Artikel im Kühlschrank für die Edit-View."""
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, dairy])
        session.commit()
        session.refresh(fridge)
        session.refresh(dairy)
        assert fridge.id is not None and dairy.id is not None
        milk = item_service.create_item(
            session,
            product_name="Milch",
            best_before_date=date(2027, 1, 15),
            quantity=1,
            unit="l",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,
            created_by=1,
            category_id=dairy.id,
        )
        assert milk.id is not None
        return milk.id


def _set_quantity(user: User, quantity: float) -> None:
    """Setzt die Menge wie der Browser: ``ui.number`` liefert Floats."""
    user.find(kind=ui.number).elements.pop().set_value(quantity)


def _error_visible(user: User, field: str) -> bool:
    """Die Fehlerzeile existiert immer; ``find`` übergeht unsichtbare Elemente, also den Layout-Baum durchgehen."""
    assert user.client is not None
    labels = [
        element
        for element in user.client.layout.descendants()
        if isinstance(element, ui.label) and f"error-{field}" in element._markers
    ]
    assert len(labels) == 1, f"Fehlerzeile für {field!r} fehlt"
    return labels[0].visible and bool(labels[0].text)


def _click_as_if_still_enabled(user: User, marker: str) -> None:
    """Der Klick erreicht den Server, bevor der deaktivierte Button im Browser angekommen ist (#386)."""
    button = user.find(marker=marker).elements.pop()
    button.enable()  # type: ignore[attr-defined]
    user.find(marker=marker).click()


async def test_wizard_shows_no_messages_before_input(logged_in_user: User) -> None:
    """Leere Pflichtfelder sind beim Öffnen kein Fehler; die Meldung erscheint erst nach einer Eingabe."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")

    assert not _error_visible(logged_in_user, "product_name")
    assert not _error_visible(logged_in_user, "quantity")


async def test_wizard_quantity_zero_shows_message_and_clears_when_fixed(logged_in_user: User) -> None:
    """Akzeptanzkriterium: Menge 0 → Text sichtbar, ohne dass das Feld den Fokus verlieren muss."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")

    _set_quantity(logged_in_user, 0)
    await logged_in_user.should_see(QUANTITY_MESSAGE)
    assert _error_visible(logged_in_user, "quantity")

    _set_quantity(logged_in_user, 5)
    await logged_in_user.should_not_see(QUANTITY_MESSAGE)
    assert not _error_visible(logged_in_user, "quantity")


async def test_wizard_short_name_shows_message(logged_in_user: User) -> None:
    """Akzeptanzkriterium: Name mit 1 Zeichen → entsprechende Meldung."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")

    logged_in_user.find(NAME_PLACEHOLDER).type("T")
    await logged_in_user.should_see(NAME_MESSAGE)

    logged_in_user.find(NAME_PLACEHOLDER).type("omaten")
    await logged_in_user.should_not_see(NAME_MESSAGE)


async def test_wizard_next_with_errors_reveals_all_messages(logged_in_user: User) -> None:
    """Weiter trotz Fehlern zeigt jede Feldmeldung statt nur „Bitte alle Pflichtfelder ausfüllen“."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")

    _click_as_if_still_enabled(logged_in_user, "wizard-next")

    await logged_in_user.should_see(NAME_MESSAGE)
    await logged_in_user.should_see(QUANTITY_MESSAGE)
    await logged_in_user.should_see("Schritt 1 von 3")


async def test_wizard_summary_formats_quantity_without_decimals(logged_in_user: User) -> None:
    """Akzeptanzkriterium: Zusammenfassung zeigt "500 g" statt "500.0 g"."""
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")
    logged_in_user.find(NAME_PLACEHOLDER).type("Käse")
    logged_in_user.find(marker="item-type-chip-purchased_fresh").click()
    _set_quantity(logged_in_user, 500.0)
    logged_in_user.find(marker="unit-chip-g").click()
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 2 von 3")
    await logged_in_user.should_see("500 g")
    await logged_in_user.should_not_see("500.0")


async def test_edit_quantity_zero_shows_message(logged_in_user: User, milk_id: int) -> None:
    await logged_in_user.open(f"/items/{milk_id}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")

    _set_quantity(logged_in_user, 0)

    await logged_in_user.should_see(QUANTITY_MESSAGE)
    assert _error_visible(logged_in_user, "quantity")


async def test_edit_short_name_shows_message(logged_in_user: User, milk_id: int) -> None:
    await logged_in_user.open(f"/items/{milk_id}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")

    logged_in_user.find(NAME_PLACEHOLDER, kind=ui.input).elements.pop().set_value("M")

    await logged_in_user.should_see(NAME_MESSAGE)
    assert _error_visible(logged_in_user, "product_name")
