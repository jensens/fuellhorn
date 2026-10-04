"""UI Tests: Umwahl bei Kategorie- und Lagerort-Chips (Issue #341).

Beim Deselektieren wurde der Stil additiv gesetzt; ``background-color`` und
``color`` aus dem Selektions-Stil blieben stehen, der alte Chip wirkte weiter
ausgefüllt. Die Tests prüfen den Stil der Chip-Elemente nach einem Wechsel.
"""

from app.models import Category
from app.models import Location
from nicegui import ui
from nicegui.testing import User


def _chip(user: User, marker: str) -> ui.button:
    return user.find(kind=ui.button, marker=marker).elements.pop()


async def test_category_chip_loses_fill_when_another_is_selected(
    user: User, standard_categories: list[Category]
) -> None:
    """Kategorie A, dann B wählen: A hat weder 'active' noch eine Hintergrundfarbe mehr."""
    first, second = standard_categories[0].id, standard_categories[1].id
    await user.open("/test/category-chips")
    user.find(marker=f"category-chip-{first}").click()
    user.find(marker=f"category-chip-{second}").click()

    deselected = _chip(user, f"category-chip-{first}")
    selected = _chip(user, f"category-chip-{second}")
    assert "active" not in deselected.classes and "background-color" not in deselected.style
    assert "active" in selected.classes and "background-color" in selected.style


async def test_location_chip_loses_fill_when_another_is_selected(
    user: User, standard_locations: list[Location]
) -> None:
    """Lagerort A, dann B wählen: A hat weder 'active' noch eine Hintergrundfarbe mehr."""
    first, second = standard_locations[0].id, standard_locations[1].id
    await user.open("/test/location-chips")
    user.find(marker=f"location-chip-{first}").click()
    user.find(marker=f"location-chip-{second}").click()

    deselected = _chip(user, f"location-chip-{first}")
    selected = _chip(user, f"location-chip-{second}")
    assert "active" not in deselected.classes and "background-color" not in deselected.style
    assert "active" in selected.classes and "background-color" in selected.style


async def test_category_reselect_keeps_border_color(user: User, standard_categories: list[Category]) -> None:
    """Der deselektierte Chip behält seinen farbigen Rahmen (nur die Füllung verschwindet)."""
    first, second = standard_categories[0].id, standard_categories[1].id
    await user.open("/test/category-chips")
    user.find(marker=f"category-chip-{first}").click()
    user.find(marker=f"category-chip-{second}").click()

    deselected = _chip(user, f"category-chip-{first}")
    assert deselected.style.get("border-color") == standard_categories[0].color
