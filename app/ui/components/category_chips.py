"""Category Chip Group Component.

A chip-based selection component for choosing categories with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
Categories are loaded dynamically from the database.
"""

from ...models.category import Category
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
    # Store current selection and chip references
    current_value: list[int | None] = [value]
    chip_refs: dict[int, ui.element] = {}
    dot_refs: dict[int, ui.element] = {}

    def update_chip_styles() -> None:
        """Update all chips to reflect current selection."""
        for category_id, chip in chip_refs.items():
            is_selected = category_id == current_value[0]
            dot = dot_refs[category_id]

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

            # Create chip as button for proper click handling
            chip = (
                ui.button(
                    on_click=lambda _, cid=cat_id: select_category(cid),
                )
                .classes(
                    "rounded-lg cursor-pointer "
                    "transition-all duration-150 ease-in-out select-none normal-case "
                    + ("bg-primary text-white" if is_selected else "bg-gray-100 text-gray-700 hover:bg-gray-200")
                )
                .style("min-height: 44px; padding: 0.5rem 0.75rem;")
                .props("flat no-caps")
            )

            chip_refs[cat_id] = chip

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
                    dot_refs[cat_id] = dot

                    # Label
                    ui.label(category.name).classes("text-sm font-medium whitespace-nowrap")

    return container
