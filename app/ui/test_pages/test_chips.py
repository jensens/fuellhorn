"""Test pages for Chip component testing.

These pages are used to test the chip components in isolation.
Only loaded when TESTING=true environment variable is set.
"""

from ...database import get_session
from ...models.category import Category
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_grouped_category_chip_group
from ..components import create_location_chip_group
from ..components.location_overview import create_location_overview_chips
from nicegui import ui


# Store last selected values for test verification
_last_location: list[int | None] = [None]
_last_category: list[int | None] = [None]


def _reset_test_state() -> None:
    """Reset test state between tests."""
    _last_location[0] = None
    _last_category[0] = None


@ui.page("/test/location-chips")
def test_location_chips_page() -> None:
    """Test page for Location chips without initial selection."""
    _reset_test_state()

    # Label reference for updating
    selection_label: list[ui.label | None] = [None]

    def on_change(value: int) -> None:
        _last_location[0] = value
        if selection_label[0]:
            selection_label[0].set_text(f"Selected: {value}")

    # Load locations from database
    with next(get_session()) as session:
        locations = location_service.get_all_locations(session)

    with ui.column().classes("p-4"):
        ui.label("Location Chips Test").classes("text-h6")
        create_location_chip_group(
            locations=locations,
            on_change=on_change,
        )
        # Display current selection for test verification
        selection_label[0] = ui.label("Selected: None")


@ui.page("/test/location-chips-preselected")
def test_location_chips_preselected_page() -> None:
    """Test page for Location chips with initial selection."""
    _reset_test_state()

    # Load locations from database
    with next(get_session()) as session:
        locations = location_service.get_all_locations(session)

    # Use first location as preselected if available
    preselected_id = locations[0].id if locations else None
    _last_location[0] = preselected_id

    def on_change(value: int) -> None:
        _last_location[0] = value

    with ui.column().classes("p-4"):
        ui.label("Location Chips Test (Preselected)").classes("text-h6")
        create_location_chip_group(
            locations=locations,
            value=preselected_id,
            on_change=on_change,
        )


@ui.page("/test/category-chips")
def test_category_chips_page() -> None:
    """Test page for Category chips without initial selection."""
    _reset_test_state()

    # Label reference for updating
    selection_label: list[ui.label | None] = [None]

    def on_change(value: int) -> None:
        _last_category[0] = value
        if selection_label[0]:
            selection_label[0].set_text(f"Selected: {value}")

    # Load categories from database
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)

    with ui.column().classes("p-4"):
        ui.label("Category Chips Test").classes("text-h6")
        create_grouped_category_chip_group(
            grouped_categories=[(None, categories)],
            on_change=on_change,
        )
        # Display current selection for test verification
        selection_label[0] = ui.label("Selected: None")


@ui.page("/test/category-chips-preselected")
def test_category_chips_preselected_page() -> None:
    """Test page for Category chips with initial selection."""
    _reset_test_state()

    # Load categories from database
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)

    # Use first category as preselected if available
    preselected_id = categories[0].id if categories else None
    _last_category[0] = preselected_id

    def on_change(value: int) -> None:
        _last_category[0] = value

    with ui.column().classes("p-4"):
        ui.label("Category Chips Test (Preselected)").classes("text-h6")
        create_grouped_category_chip_group(
            grouped_categories=[(None, categories)],
            value=preselected_id,
            on_change=on_change,
        )


@ui.page("/test/category-chips-grouped")
def test_category_chips_grouped_page() -> None:
    """Test page for Category chips with groups and ungrouped categories (#457)."""
    _reset_test_state()

    grouped: list[tuple[str | None, list[Category]]] = [
        ("Fleisch", [Category(id=2, name="Rindfleisch", parent_id=1, created_by=1)]),
        (None, [Category(id=3, name="Gemüse", created_by=1)]),
    ]

    with ui.column().classes("p-4"):
        ui.label("Category Chips Test (Grouped)").classes("text-h6")
        create_grouped_category_chip_group(grouped_categories=grouped)


@ui.page("/test/location-overview")
def test_location_overview_page() -> None:
    """Test page for Location Overview chips (Issue #246).

    Displays horizontal scrollable location chips with icons and item counts.
    """
    with next(get_session()) as session:
        locations = location_service.get_all_locations(session)
        item_counts = item_service.get_item_count_by_location(session)

    with ui.column().classes("p-4 w-full"):
        ui.label("Location Overview Test").classes("text-h6")
        create_location_overview_chips(
            locations=locations,
            item_counts=item_counts,
        )
