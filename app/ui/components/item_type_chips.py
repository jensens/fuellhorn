"""Item Type Chip Group Component.

A chip-based selection component for choosing item types with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
"""

from ...models.item import ItemType
from collections.abc import Callable
from nicegui import ui


# German labels for item types
ITEM_TYPE_LABELS: dict[ItemType, str] = {
    ItemType.PURCHASED_FRESH: "Frisch eingekauft",
    ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
    ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft \u2192 eingefroren",
    ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
    ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
}

# CSS data-type attribute values for Solarpunk theme styling
ITEM_TYPE_DATA_TYPES: dict[ItemType, str] = {
    ItemType.PURCHASED_FRESH: "fresh",
    ItemType.PURCHASED_FROZEN: "frozen",
    ItemType.PURCHASED_THEN_FROZEN: "frozen",
    ItemType.HOMEMADE_FROZEN: "homemade",
    ItemType.HOMEMADE_PRESERVED: "homemade",
}


def create_item_type_chip_group(
    value: ItemType | None = None,
    on_change: Callable[[ItemType], None] | None = None,
) -> ui.element:
    """Create a chip group for selecting item types.

    Args:
        value: Initially selected item type (optional)
        on_change: Callback when selection changes

    Returns:
        The container element with all chips
    """
    # Store current selection and chip references
    current_value: list[ItemType | None] = [value]
    chip_refs: dict[ItemType, ui.element] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection."""
        for item_type, chip in chip_refs.items():
            is_selected = item_type == current_value[0]

            if is_selected:
                chip.classes(add="active")
            else:
                chip.classes(remove="active")

    def select_item_type(item_type: ItemType) -> None:
        """Handle chip selection."""
        if current_value[0] != item_type:
            current_value[0] = item_type
            update_chip_styles()
            if on_change:
                on_change(item_type)

    # Container with flex-wrap for responsive layout
    with ui.row().classes("flex-wrap gap-2") as container:
        for item_type in ItemType:
            is_selected = item_type == value
            label_text = ITEM_TYPE_LABELS.get(item_type, item_type.value)
            data_type = ITEM_TYPE_DATA_TYPES.get(item_type, "fresh")

            # Create chip as button with Solarpunk theme classes
            chip = (
                ui.button(
                    on_click=lambda _, it=item_type: select_item_type(it),
                )
                .classes("sp-chip sp-chip-type" + (" active" if is_selected else ""))
                .props(f'flat no-caps data-type="{data_type}"')
            )

            chip_refs[item_type] = chip

            # Add content to button with explicit flex container
            with chip:
                with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
                    # Ring-dot indicator with Solarpunk theme class
                    ui.element("div").classes("sp-ring-dot")

                    # Label
                    ui.label(label_text).classes("text-sm font-medium whitespace-nowrap")

    return container


def get_item_type_label(item_type: ItemType) -> str:
    """Get the German label for an item type.

    Args:
        item_type: The item type enum value

    Returns:
        German display label
    """
    return ITEM_TYPE_LABELS.get(item_type, item_type.value)
