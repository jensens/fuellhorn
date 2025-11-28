"""Test pages for Chip component testing.

These pages are used to test the chip components in isolation.
Only loaded when TESTING=true environment variable is set.
"""

from ...models.item import ItemType
from ..components import create_item_type_chip_group
from ..components import create_unit_chip_group
from nicegui import ui


# Store last selected values for test verification
_last_item_type: list[ItemType | None] = [None]
_last_unit: list[str | None] = [None]


def _reset_test_state() -> None:
    """Reset test state between tests."""
    _last_item_type[0] = None
    _last_unit[0] = None


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
