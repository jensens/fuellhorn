"""Category Bar Chart Component for Dashboard.

Issue #247: Vertical list of categories with colored bars and item counts.
"""

from ...models.category import Category
from collections.abc import Sequence
from nicegui import ui


def create_category_bar_chart(
    categories: Sequence[Category],
    item_counts: dict[int, int],
    max_visible: int = 5,
) -> ui.element | None:
    """Create vertical category bar chart with item counts.

    Displays categories as horizontal bars with:
    - Bar width proportional to item count (relative to max)
    - Bar color from category.color (hex)
    - Sorted by count descending
    - Max-height with scrollbar when > max_visible categories
    - Tap navigates to /items?category={id}

    Args:
        categories: List of Category objects from the database
        item_counts: Dictionary mapping category_id to item count
        max_visible: Number of categories before scrollbar appears (default 5)

    Returns:
        The container element with the bar chart, or None if no categories with items
    """
    # Build list of (category, count) pairs, filtering out categories without items
    category_data: list[tuple[Category, int]] = []
    for category in categories:
        if category.id is None:
            continue
        count = item_counts.get(category.id, 0)
        if count > 0:
            category_data.append((category, count))

    # If no categories with items, don't render anything
    if not category_data:
        return None

    # Sort by count descending
    category_data.sort(key=lambda x: x[1], reverse=True)

    # Find max count for proportional bar widths
    max_count = max(count for _, count in category_data)

    # Calculate max height (each row ~44px, add padding)
    row_height = 44
    max_height = max_visible * row_height

    # Section title
    with ui.element("div").props('id="categories-section"'):
        ui.label("Kategorien").classes("sp-page-title text-base mb-3 mt-6")

    # Container with max-height and scroll
    with ui.element("div").classes("w-full overflow-y-auto").style(f"max-height: {max_height}px;") as container:
        for category, count in category_data:
            if category.id is None:
                continue

            cat_id: int = category.id
            color = category.color or "#6B7280"  # Fallback gray

            # Calculate bar width percentage (min 10% for visibility)
            bar_width_percent = max(10, int((count / max_count) * 100))

            # Category row - clickable
            with (
                ui.element("div")
                .classes(
                    "flex items-center gap-3 py-2 px-1 cursor-pointer hover:bg-cream-light rounded transition-colors"
                )
                .on("click", lambda _, cid=cat_id: ui.navigate.to(f"/items?category={cid}"))
            ):
                # Bar container (flex-1 to take remaining space)
                with ui.element("div").classes("flex-1 h-6 bg-cream rounded overflow-hidden"):
                    # Colored bar with proportional width
                    (
                        ui.element("div")
                        .classes("h-full rounded transition-all")
                        .style(f"width: {bar_width_percent}%; background-color: {color};")
                    )

                # Category name
                ui.label(category.name).classes("text-sm text-charcoal font-medium min-w-[100px] truncate")

                # Item count
                ui.label(str(count)).classes("text-sm font-bold text-leaf min-w-[30px] text-right")

    return container
