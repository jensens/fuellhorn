"""Category Chip Group Component.

A chip-based selection component for choosing categories with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
Categories are loaded dynamically from the database.
"""

from ...models.category import Category
from ..theme import get_contrast_text_color
from collections.abc import Callable
from collections.abc import Sequence
from nicegui import ui


def create_category_chip_group(
    categories: Sequence[Category],
    value: int | None = None,
    on_change: Callable[[int], None] | None = None,
) -> ui.element:
    """Create a chip group for selecting categories.

    Args:
        categories: List of Category objects from the database
        value: Initially selected category_id (optional)
        on_change: Callback when selection changes (receives category_id)

    Returns:
        The container element with all chips
    """
    # Store current selection, chip references, and category colors
    current_value: list[int | None] = [value]
    chip_refs: dict[int, ui.element] = {}
    dot_refs: dict[int, ui.element] = {}
    category_colors: dict[int, str] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection and category color."""
        for category_id, chip in chip_refs.items():
            is_selected = category_id == current_value[0]
            dot = dot_refs[category_id]
            color = category_colors.get(category_id, "#6B7280")
            text_color = get_contrast_text_color(color)
            # Dot border color: white for dark backgrounds, use category color for light
            dot_color = "white" if text_color == "white" else color

            if is_selected:
                # Selected state - full background in category color
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

    def select_category(category_id: int) -> None:
        """Handle chip selection."""
        if current_value[0] != category_id:
            current_value[0] = category_id
            update_chip_styles()
            if on_change:
                on_change(category_id)

    # Container with flex-wrap for responsive layout
    with ui.row().classes("flex-wrap gap-2") as container:
        for category in categories:
            # Skip categories without ID (shouldn't happen in practice)
            if category.id is None:
                continue
            cat_id: int = category.id
            is_selected = cat_id == value
            color = category.color or "#6B7280"  # Default gray if no color
            text_color = get_contrast_text_color(color)

            # Store color for update_chip_styles
            category_colors[cat_id] = color

            # Create chip as button for proper click handling
            chip = (
                ui.button(
                    on_click=lambda _, cid=cat_id: select_category(cid),
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

            chip_refs[cat_id] = chip

            # Add content to button with explicit flex container
            # Dot color: same as text for visibility
            dot_color = "white" if text_color == "white" else color
            with chip:
                with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
                    # Ring-dot indicator with category color
                    dot = ui.element("div").style(
                        "width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; "
                        + (
                            f"background: radial-gradient(circle, {dot_color} 35%, transparent 35%); border: 2px solid {dot_color};"
                            if is_selected
                            else f"background-color: transparent; border: 2px solid {color};"
                        )
                    )
                    dot_refs[cat_id] = dot

                    # Label
                    ui.label(category.name).classes("text-sm font-medium whitespace-nowrap")

    return container
