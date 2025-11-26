"""Item Type Chip Group Component.

A chip-based selection component for choosing item types with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
"""

from ...models.freeze_time_config import ItemType
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
    dot_refs: dict[ItemType, ui.element] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection."""
        for item_type, chip in chip_refs.items():
            is_selected = item_type == current_value[0]
            dot = dot_refs[item_type]

            if is_selected:
                # Selected state - white outer ring with colored inner dot
                chip.classes(
                    remove="bg-gray-100 text-gray-700 hover:bg-gray-200",
                    add="bg-primary text-white",
                )
                dot.style(
                    "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                    "background: radial-gradient(circle, var(--q-primary, #1976d2) 35%, white 35%);"
                )
            else:
                # Default state - empty ring
                chip.classes(
                    remove="bg-primary text-white",
                    add="bg-gray-100 text-gray-700 hover:bg-gray-200",
                )
                dot.style(
                    "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                    "background: transparent; border: 2px solid #9ca3af;"
                )

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

            # Create chip as button for proper click handling
            chip = (
                ui.button(
                    on_click=lambda _, it=item_type: select_item_type(it),
                )
                .classes(
                    "rounded-lg cursor-pointer "
                    "transition-all duration-150 ease-in-out select-none normal-case "
                    + ("bg-primary text-white" if is_selected else "bg-gray-100 text-gray-700 hover:bg-gray-200")
                )
                .style("min-height: 44px; padding: 0.5rem 0.75rem;")
                .props("flat no-caps")
            )

            chip_refs[item_type] = chip

            # Add content to button with explicit flex container
            with chip:
                with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
                    # Ring-dot indicator
                    dot = ui.element("div").style(
                        "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                        + (
                            "background: radial-gradient(circle, var(--q-primary, #1976d2) 35%, white 35%);"
                            if is_selected
                            else "background-color: transparent; border: 2px solid #9ca3af;"
                        )
                    )
                    dot_refs[item_type] = dot

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
