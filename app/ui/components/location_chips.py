"""Location Chip Group Component.

A chip-based selection component for choosing storage locations with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
Locations are loaded dynamically from the database.
"""

from ...models.location import Location
from collections.abc import Callable
from collections.abc import Sequence
from nicegui import ui


def _get_contrast_text_color(hex_color: str) -> str:
    """Return 'white' or dark color based on background color contrast.

    Uses WCAG relative luminance formula to determine optimal text color.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#374151"

    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
    return "white" if luminance < 0.5 else "#1F2937"


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
            text_color = _get_contrast_text_color(color)
            # Dot border color: white for dark backgrounds, use location color for light
            dot_color = "white" if text_color == "white" else color

            if is_selected:
                # Selected state - full background in location color
                chip.style(
                    f"background-color: {color} !important; border: 2px solid {color}; color: {text_color} !important;"
                )
                dot.style(
                    "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                    f"background: radial-gradient(circle, {dot_color} 35%, transparent 35%); "
                    f"border: 2px solid {dot_color};"
                )
            else:
                # Default state - colored border, gray background
                chip.style(
                    f"background-color: #F3F4F6 !important; border: 2px solid {color}; color: #374151 !important;"
                )
                dot.style(
                    "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                    f"background-color: transparent; border: 2px solid {color};"
                )

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
            text_color = _get_contrast_text_color(color)

            # Store color for update_chip_styles
            location_colors[loc_id] = color

            # Create chip as button for proper click handling
            chip = (
                ui.button(
                    on_click=lambda _, lid=loc_id: select_location(lid),
                )
                .classes("rounded-lg cursor-pointer transition-all duration-150 ease-in-out select-none normal-case")
                .style(
                    "min-height: 44px; padding: 0.5rem 0.75rem; "
                    + (
                        f"background-color: {color} !important; border: 2px solid {color}; color: {text_color} !important;"
                        if is_selected
                        else f"background-color: #F3F4F6 !important; border: 2px solid {color}; color: #374151 !important;"
                    )
                )
                .props("flat no-caps")
            )

            chip_refs[loc_id] = chip

            # Add content to button with explicit flex container
            # Dot color: same as text for visibility
            dot_color = "white" if text_color == "white" else color
            with chip:
                with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
                    # Ring-dot indicator with location color
                    dot = ui.element("div").style(
                        "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                        + (
                            f"background: radial-gradient(circle, {dot_color} 35%, transparent 35%); border: 2px solid {dot_color};"
                            if is_selected
                            else f"background-color: transparent; border: 2px solid {color};"
                        )
                    )
                    dot_refs[loc_id] = dot

                    # Label
                    ui.label(location.name).classes("text-sm font-medium whitespace-nowrap")

    return container
