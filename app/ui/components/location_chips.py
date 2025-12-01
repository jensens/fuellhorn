"""Location Chip Group Component.

A chip-based selection component for choosing storage locations with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
Locations are loaded dynamically from the database.
"""

from ...models.location import Location
from ..theme import get_contrast_text_color
from collections.abc import Callable
from collections.abc import Sequence
from nicegui import ui


def create_location_chip_group(
    locations: Sequence[Location],
    value: int | None = None,
    on_change: Callable[[int], None] | None = None,
) -> ui.element:
    """Create a chip group for selecting locations.

    Args:
        locations: List of Location objects from the database
        value: Initially selected location_id (optional)
        on_change: Callback when selection changes (receives location_id)

    Returns:
        The container element with all chips
    """
    # Store current selection, chip references, and location colors
    current_value: list[int | None] = [value]
    chip_refs: dict[int, ui.element] = {}
    dot_refs: dict[int, ui.element] = {}
    location_colors: dict[int, str] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection and location color."""
        for location_id, chip in chip_refs.items():
            is_selected = location_id == current_value[0]
            dot = dot_refs[location_id]
            color = location_colors.get(location_id, "#6B7280")
            text_color = get_contrast_text_color(color)
            # Dot border color: white for dark backgrounds, use location color for light
            dot_color = "white" if text_color == "white" else color

            if is_selected:
                # Selected state - full background in location color
                chip.classes(add="active")
                chip.style(
                    f"--chip-color: {color}; "
                    f"background-color: {color} !important; border-color: {color}; color: {text_color} !important;"
                )
                dot.style(
                    f"border-color: {dot_color}; background: radial-gradient(circle, {dot_color} 35%, transparent 35%);"
                )
            else:
                # Default state - colored border, theme background
                chip.classes(remove="active")
                chip.style(f"--chip-color: {color}; border-color: {color};")
                dot.style(f"border-color: {color}; background: white;")

    def select_location(location_id: int) -> None:
        """Handle chip selection."""
        if current_value[0] != location_id:
            current_value[0] = location_id
            update_chip_styles()
            if on_change:
                on_change(location_id)

    # Container with flex-wrap for responsive layout
    with ui.row().classes("flex-wrap gap-2") as container:
        for location in locations:
            # Skip locations without ID (shouldn't happen in practice)
            if location.id is None:
                continue
            loc_id: int = location.id
            is_selected = loc_id == value
            color = location.color or "#6B7280"  # Default gray if no color
            text_color = get_contrast_text_color(color)

            # Store color for update_chip_styles
            location_colors[loc_id] = color

            # Create chip as button with Solarpunk theme classes
            # Dynamic colors via CSS custom properties and inline style overrides
            chip = (
                ui.button(
                    on_click=lambda _, lid=loc_id: select_location(lid),
                )
                .classes("sp-chip sp-chip-category" + (" active" if is_selected else ""))
                .style(
                    f"--chip-color: {color}; "
                    + (
                        f"background-color: {color} !important; border-color: {color}; color: {text_color} !important;"
                        if is_selected
                        else f"border-color: {color};"
                    )
                )
                .props("flat no-caps")
            )

            chip_refs[loc_id] = chip

            # Add content to button with explicit flex container
            # Dot color: same as text for visibility on dark backgrounds
            dot_color = "white" if text_color == "white" else color
            with chip:
                with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
                    # Ring-dot indicator with Solarpunk theme class and dynamic color
                    dot = (
                        ui.element("div")
                        .classes("sp-ring-dot")
                        .style(
                            f"border-color: {dot_color if is_selected else color}; "
                            + (
                                f"background: radial-gradient(circle, {dot_color} 35%, transparent 35%);"
                                if is_selected
                                else ""
                            )
                        )
                    )
                    dot_refs[loc_id] = dot

                    # Label
                    ui.label(location.name).classes("text-sm font-medium whitespace-nowrap")

    return container
