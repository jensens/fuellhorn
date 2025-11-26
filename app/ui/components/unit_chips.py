"""Unit Chip Group Component.

A compact chip-based selection component for choosing units.
Uses color change only (no indicator) for a clean, minimal design.
"""

from collections.abc import Callable
from nicegui import ui


# Available units
UNITS: list[str] = ["g", "kg", "ml", "l", "Stück", "Packung"]


def create_unit_chip_group(
    value: str | None = None,
    on_change: Callable[[str], None] | None = None,
) -> ui.element:
    """Create a chip group for selecting units.

    Args:
        value: Initially selected unit (optional)
        on_change: Callback when selection changes

    Returns:
        The container element with all chips
    """
    # Store current selection and chip references
    current_value: list[str | None] = [value]
    chip_refs: dict[str, ui.element] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection."""
        for unit, chip in chip_refs.items():
            is_selected = unit == current_value[0]

            if is_selected:
                # Selected state
                chip.classes(
                    remove="bg-gray-200 text-gray-800 hover:bg-gray-300",
                    add="bg-primary text-white",
                )
            else:
                # Default state
                chip.classes(
                    remove="bg-primary text-white",
                    add="bg-gray-200 text-gray-800 hover:bg-gray-300",
                )

    def select_unit(unit: str) -> None:
        """Handle chip selection."""
        if current_value[0] != unit:
            current_value[0] = unit
            update_chip_styles()
            if on_change:
                on_change(unit)

    # Container with horizontal layout
    with ui.row().classes("flex-wrap gap-1") as container:
        for unit in UNITS:
            is_selected = unit == value

            # Chip as button for proper click handling
            chip = ui.button(
                unit,
                on_click=lambda _, u=unit: select_unit(u),
            ).classes(
                "flex items-center justify-center px-3 rounded-lg cursor-pointer "
                "transition-all duration-150 ease-in-out select-none font-semibold text-sm "
                + ("bg-primary text-white" if is_selected else "bg-gray-200 text-gray-800 hover:bg-gray-300")
            ).style(
                "min-width: 48px; height: 44px;"
            ).props("flat no-caps")

            chip_refs[unit] = chip

    return container


def get_available_units() -> list[str]:
    """Get the list of available units.

    Returns:
        List of unit strings
    """
    return UNITS.copy()
