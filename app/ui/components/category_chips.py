"""Category Chip Group Component.

A chip-based selection component for choosing categories with a radio-button-like
ring-dot indicator. Designed for mobile-first touch interaction.
Supports grouped display via parent categories.
"""

from ...models.category import Category
from ..theme import Colors
from ..theme import get_contrast_text_color
from collections.abc import Callable
from collections.abc import Sequence
from nicegui import ui


def create_grouped_category_chip_group(
    grouped_categories: Sequence[tuple[str | None, Sequence[Category]]],
    value: int | None = None,
    on_change: Callable[[int], None] | None = None,
) -> ui.element:
    """Create a chip group from pre-grouped categories.

    Args:
        grouped_categories: List of (group_name, categories) tuples
            from get_grouped_categories_for_item_type()
        value: Initially selected category_id (optional)
        on_change: Callback when selection changes (receives category_id)

    Returns:
        The container element with all chips
    """
    current_value: list[int | None] = [value]
    chip_refs: dict[int, ui.element] = {}
    dot_refs: dict[int, ui.element] = {}
    category_colors: dict[int, str] = {}

    def update_chip_styles() -> None:
        for category_id, chip in chip_refs.items():
            is_selected = category_id == current_value[0]
            dot = dot_refs[category_id]
            color = category_colors.get(category_id, Colors.DEFAULT_GRAY)
            text_color = get_contrast_text_color(color)
            dot_color = "white" if text_color == "white" else color

            if is_selected:
                chip.classes(add="active")
                chip.style(
                    f"--chip-color: {color}; "
                    f"background-color: {color} !important; border-color: {color}; color: {text_color} !important;"
                )
                dot.style(
                    f"border-color: {dot_color}; background: radial-gradient(circle, {dot_color} 35%, transparent 35%);"
                )
            else:
                # replace= drops the background-color/color set on selection (#341)
                chip.classes(remove="active")
                chip.style(replace=f"--chip-color: {color}; border-color: {color};")
                dot.style(f"border-color: {color}; background: white;")

    def select_category(category_id: int) -> None:
        if current_value[0] != category_id:
            current_value[0] = category_id
            update_chip_styles()
            if on_change:
                on_change(category_id)

    def _render_chip(category: Category, is_selected: bool) -> None:
        if category.id is None:
            return
        cat_id: int = category.id
        color = category.color or Colors.DEFAULT_GRAY
        text_color = get_contrast_text_color(color)
        category_colors[cat_id] = color

        chip = (
            ui.button(
                on_click=lambda _, cid=cat_id: select_category(cid),
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
            .mark(f"category-chip-{cat_id}")
        )
        chip_refs[cat_id] = chip

        dot_color = "white" if text_color == "white" else color
        with chip:
            with ui.row().classes("items-center gap-2").style("flex-wrap: nowrap;"):
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
                dot_refs[cat_id] = dot
                ui.label(category.name).classes("text-sm font-medium whitespace-nowrap")

    with ui.column().classes("gap-3 w-full") as container:
        for group_name, cats in grouped_categories:
            if group_name:
                ui.label(group_name).classes("text-xs font-bold uppercase tracking-wide text-stone-500 mt-1")
            with ui.row().classes("flex-wrap gap-2"):
                for cat in cats:
                    _render_chip(cat, cat.id == value)

    return container
