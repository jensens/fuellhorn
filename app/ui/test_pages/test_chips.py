"""Test pages for Chip component testing.

These pages are used to test the chip components in isolation.
Only loaded when TESTING=true environment variable is set.
"""

from ...database import get_session
from ...models.item import ItemType
from ...services import category_service
from ...services import location_service
from ..components import create_category_chip_group
from ..components import create_item_type_chip_group
from ..components import create_location_chip_group
from ..components import create_unit_chip_group
from nicegui import ui


# Store last selected values for test verification
_last_item_type: list[ItemType | None] = [None]
_last_unit: list[str | None] = [None]
_last_location: list[int | None] = [None]
_last_category: list[int | None] = [None]


def _reset_test_state() -> None:
    """Reset test state between tests."""
    _last_item_type[0] = None
    _last_unit[0] = None
    _last_location[0] = None
    _last_category[0] = None


@ui.page("/test/item-type-chips")
def test_item_type_chips_page() -> None:
    """Test page for ItemType chips without initial selection."""
    _reset_test_state()

    # Label reference for updating
    selection_label: list[ui.label | None] = [None]

    def on_change(value: ItemType) -> None:
        _last_item_type[0] = value
        if selection_label[0]:
            selection_label[0].set_text(f"Selected: {value.value}")

    with ui.column().classes("p-4"):
        ui.label("ItemType Chips Test").classes("text-h6")
        create_item_type_chip_group(on_change=on_change)
        # Display current selection for test verification
        selection_label[0] = ui.label("Selected: None")


@ui.page("/test/item-type-chips-preselected")
def test_item_type_chips_preselected_page() -> None:
    """Test page for ItemType chips with initial selection."""
    _reset_test_state()
    _last_item_type[0] = ItemType.HOMEMADE_FROZEN

    def on_change(value: ItemType) -> None:
        _last_item_type[0] = value

    with ui.column().classes("p-4"):
        ui.label("ItemType Chips Test (Preselected)").classes("text-h6")
        create_item_type_chip_group(
            value=ItemType.HOMEMADE_FROZEN,
            on_change=on_change,
        )


@ui.page("/test/unit-chips")
def test_unit_chips_page() -> None:
    """Test page for Unit chips without initial selection."""
    _reset_test_state()

    def on_change(value: str) -> None:
        _last_unit[0] = value

    with ui.column().classes("p-4"):
        ui.label("Unit Chips Test").classes("text-h6")
        create_unit_chip_group(on_change=on_change)


@ui.page("/test/unit-chips-preselected")
def test_unit_chips_preselected_page() -> None:
    """Test page for Unit chips with initial selection."""
    _reset_test_state()
    _last_unit[0] = "kg"

    def on_change(value: str) -> None:
        _last_unit[0] = value

    with ui.column().classes("p-4"):
        ui.label("Unit Chips Test (Preselected)").classes("text-h6")
        create_unit_chip_group(
            value="kg",
            on_change=on_change,
        )


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
        create_category_chip_group(
            categories=categories,
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
        create_category_chip_group(
            categories=categories,
            value=preselected_id,
            on_change=on_change,
        )
