"""UI: Kompakter Kategorie-Filter im Vorrat – eine Zeile, Auswahl im Panel von unten (Issue #471)."""

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


@pytest.fixture(name="pantry")
def pantry_fixture(isolated_test_database) -> dict[str, int]:
    """Gruppe 'Fleisch' mit 'Rindfleisch' und 'Wurst', eigenständig 'Gemüse'; je ein Artikel."""
    with Session(isolated_test_database) as session:
        meat = Category(name="Fleisch", color="#F44336", created_by=1)
        session.add(meat)
        session.commit()
        session.refresh(meat)
        beef = Category(name="Rindfleisch", color="#D32F2F", created_by=1, parent_id=meat.id)
        sausage = Category(name="Wurst", color="#795548", created_by=1, parent_id=meat.id)
        veg = Category(name="Gemüse", color="#4CAF50", created_by=1)
        shelf = Location(name="Regal", location_type=LocationType.AMBIENT, created_by=1)
        session.add_all([beef, sausage, veg, shelf])
        session.commit()
        for obj in (beef, sausage, veg, shelf):
            session.refresh(obj)
        assert meat.id and beef.id and sausage.id and veg.id and shelf.id
        for name, category_id in (("Steak", beef.id), ("Bratwurst", sausage.id), ("Erbsen", veg.id)):
            item_service.create_item(
                session,
                product_name=name,
                best_before_date=date(2027, 3, 1),
                quantity=1,
                unit="Stück",
                item_type=ItemType.PURCHASED_FRESH,
                location_id=shelf.id,
                created_by=1,
                category_id=category_id,
            )
        return {"meat": meat.id, "beef": beef.id, "sausage": sausage.id, "veg": veg.id}


def _card_names(user: User) -> list[str]:
    assert user.client is not None
    return sorted(
        element.text
        for element in user.client.layout.descendants()
        if isinstance(element, ui.label) and any(m.startswith("item-name-") for m in element._markers)
    )


def _sheet(user: User) -> ui.dialog:
    (dialog,) = user.find(kind=ui.dialog, marker="category-filter-sheet").elements
    return dialog


def _open_button(user: User) -> ui.button:
    (button,) = user.find(kind=ui.button, marker="category-filter-open").elements
    return button


async def _open_items(user: User) -> None:
    await user.open("/items")
    await user.should_see("Erbsen")


async def test_filter_is_one_row_until_opened(logged_in_user: User, pantry: dict[str, int]) -> None:
    """Zugeklappt: nur die Schaltfläche; die Kategorie-Chips liegen im geschlossenen Panel."""
    await _open_items(logged_in_user)

    assert _open_button(logged_in_user).text == "Kategorien"
    assert _sheet(logged_in_user).value is False
    chips = logged_in_user.find(marker=f"filter-category-{pantry['beef']}").elements
    assert chips and all(_sheet(logged_in_user) in chip.ancestors() for chip in chips)


async def test_selecting_in_sheet_filters_and_shows_chip(logged_in_user: User, pantry: dict[str, int]) -> None:
    """Kategorie wählen: Liste gefiltert, Chip unter der Schaltfläche, Zähler in der Schaltfläche."""
    await _open_items(logged_in_user)

    logged_in_user.find(marker="category-filter-open").click()
    assert _sheet(logged_in_user).value is True
    logged_in_user.find(marker=f"filter-category-{pantry['veg']}").click()

    await logged_in_user.should_see(marker=f"filter-selected-{pantry['veg']}")
    assert _card_names(logged_in_user) == ["Erbsen"]
    assert _open_button(logged_in_user).text == "Kategorien (1)"

    logged_in_user.find(marker="category-filter-done").click()
    assert _sheet(logged_in_user).value is False


async def test_group_selects_all_its_categories(logged_in_user: User, pantry: dict[str, int]) -> None:
    """Gruppen-Chip filtert auf alle Kategorien der Gruppe (#395)."""
    await _open_items(logged_in_user)

    logged_in_user.find(marker="category-filter-open").click()
    (group_chip,) = logged_in_user.find(marker=f"filter-category-{pantry['meat']}").elements
    assert "Alle" in group_chip.text  # Gruppe = Überschrift, „Alle“ wählt die ganze Gruppe
    headings = [e.text for e in _sheet(logged_in_user).descendants() if isinstance(e, ui.label)]
    assert "Fleisch" in headings
    logged_in_user.find(marker=f"filter-category-{pantry['meat']}").click()

    await logged_in_user.should_see(marker=f"filter-selected-{pantry['meat']}")
    assert _card_names(logged_in_user) == ["Bratwurst", "Steak"]
    (selected,) = logged_in_user.find(marker=f"filter-selected-{pantry['meat']}").elements
    assert selected.text == "Fleisch"


async def test_chip_removes_category(logged_in_user: User, pantry: dict[str, int]) -> None:
    """Tipp auf den Chip unter der Schaltfläche entfernt die Kategorie."""
    await _open_items(logged_in_user)
    logged_in_user.find(marker="category-filter-open").click()
    logged_in_user.find(marker=f"filter-category-{pantry['veg']}").click()
    logged_in_user.find(marker=f"filter-category-{pantry['beef']}").click()
    logged_in_user.find(marker="category-filter-done").click()
    assert _card_names(logged_in_user) == ["Erbsen", "Steak"]

    logged_in_user.find(marker=f"filter-selected-{pantry['veg']}").click()

    assert _card_names(logged_in_user) == ["Steak"]
    await logged_in_user.should_not_see(marker=f"filter-selected-{pantry['veg']}")
    assert _open_button(logged_in_user).text == "Kategorien (1)"


async def test_clear_all_in_sheet(logged_in_user: User, pantry: dict[str, int]) -> None:
    """„Alle abwählen“ leert die Auswahl, die Liste zeigt wieder alles."""
    await _open_items(logged_in_user)
    logged_in_user.find(marker="category-filter-open").click()
    logged_in_user.find(marker=f"filter-category-{pantry['veg']}").click()
    assert _card_names(logged_in_user) == ["Erbsen"]

    logged_in_user.find(marker="category-filter-clear").click()

    assert _card_names(logged_in_user) == ["Bratwurst", "Erbsen", "Steak"]
    assert _open_button(logged_in_user).text == "Kategorien"


async def test_ungrouped_categories_under_sonstiges(logged_in_user: User, pantry: dict[str, int]) -> None:
    """Kategorien ohne Gruppe stehen im Panel unter „Sonstiges“ (#457)."""
    await _open_items(logged_in_user)

    labels = [
        element.text
        for element in _sheet(logged_in_user).descendants()
        if isinstance(element, ui.label) and element.text == "Sonstiges"
    ]

    assert labels == ["Sonstiges"]


async def test_selected_chip_is_44px_touch_target(logged_in_user: User, pantry: dict[str, int]) -> None:
    await _open_items(logged_in_user)
    logged_in_user.find(marker="category-filter-open").click()
    logged_in_user.find(marker=f"filter-category-{pantry['veg']}").click()

    (chip,) = logged_in_user.find(marker=f"filter-selected-{pantry['veg']}").elements

    assert "min-h-[44px]" in chip._classes


async def test_reset_filters_clears_categories(logged_in_user: User, pantry: dict[str, int]) -> None:
    """„Filter zurücksetzen“ leert auch die Kategorie-Auswahl."""
    await _open_items(logged_in_user)
    logged_in_user.find(marker="category-filter-open").click()
    logged_in_user.find(marker=f"filter-category-{pantry['veg']}").click()
    logged_in_user.find(marker="category-filter-done").click()
    assert _card_names(logged_in_user) == ["Erbsen"]

    logged_in_user.find("Filter zurücksetzen").click()

    await logged_in_user.should_see("Steak", retries=50)
    assert _card_names(logged_in_user) == ["Bratwurst", "Erbsen", "Steak"]
    assert _open_button(logged_in_user).text == "Kategorien"
    await logged_in_user.should_not_see(marker=f"filter-selected-{pantry['veg']}")
