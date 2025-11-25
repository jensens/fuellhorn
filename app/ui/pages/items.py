"""Items Page - List view of all inventory items (Mobile-First).

Displays all non-consumed items as cards with expiry status.
Based on requirements from Issue #9.
Search functionality added in Issue #10.
Category filter added in Issue #11.
Extended in Issue #17 to allow showing consumed items via toggle.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...models.item import ItemCategory
from ...services import category_service
from ...services import item_service
from ..components import create_bottom_nav
from ..components import create_item_card
from ..components import create_mobile_page_container
from nicegui import app
from nicegui import ui
from sqlmodel import Session
from sqlmodel import select
from typing import Any


# Browser storage key for consumed items filter
SHOW_CONSUMED_KEY = "show_consumed_items"


def _render_empty_state() -> None:
    """Render empty state when no items exist or no search results."""
    with ui.card().classes("w-full p-6 text-center"):
        ui.icon("inventory_2").classes("text-6xl text-gray-300 mb-4")
        ui.label("Keine Artikel vorhanden").classes("text-lg text-gray-600 mb-2")
        ui.label("Erfasse deinen ersten Artikel!").classes("text-sm text-gray-500")
        ui.button(
            "Artikel erfassen",
            on_click=lambda: ui.navigate.to("/add-item"),
        ).classes("mt-4")


def _render_no_filter_results() -> None:
    """Render message when filters yield no results."""
    with ui.card().classes("w-full p-6 text-center"):
        ui.icon("search_off").classes("text-6xl text-gray-300 mb-4")
        ui.label("Keine Artikel gefunden").classes("text-lg text-gray-600 mb-2")
        ui.label("Versuche andere Filter oder Suchbegriffe").classes("text-sm text-gray-500")


def _build_item_category_map(session: Session, items: list[Item]) -> dict[int, set[int]]:
    """Build a mapping from item IDs to their category IDs.

    Args:
        session: Database session
        items: List of items

    Returns:
        Dictionary mapping item ID to set of category IDs
    """
    item_category_map: dict[int, set[int]] = {}
    for item in items:
        if item.id is not None:
            item_cats = session.exec(select(ItemCategory).where(ItemCategory.item_id == item.id)).all()
            item_category_map[item.id] = {ic.category_id for ic in item_cats}
    return item_category_map


def _filter_items_by_search(items: list[Item], search_term: str) -> list[Item]:
    """Filter items by product name (case-insensitive).

    Args:
        items: List of items to filter
        search_term: Search term to filter by

    Returns:
        Filtered list of items
    """
    if not search_term:
        return items

    term_lower = search_term.lower()
    return [item for item in items if term_lower in item.product_name.lower()]


def _filter_items_by_categories(
    items: list[Item],
    selected_categories: set[int],
    item_category_map: dict[int, set[int]],
) -> list[Item]:
    """Filter items by selected categories (OR logic).

    Args:
        items: List of items to filter
        selected_categories: Set of selected category IDs
        item_category_map: Mapping of item IDs to category IDs

    Returns:
        Filtered list of items that have at least one of the selected categories
    """
    if not selected_categories:
        return items

    return [
        item for item in items if item.id is not None and item_category_map.get(item.id, set()) & selected_categories
    ]


@ui.page("/items")
@require_auth
def items_page() -> None:
    """Items list page with card layout, search, category filter and consumed toggle (Mobile-First)."""

    # Read filter setting from browser storage (default: False = hide consumed)
    show_consumed = app.storage.browser.get(SHOW_CONSUMED_KEY, False)

    # State for filters
    selected_categories: set[int] = set()
    chip_elements: dict[int, ui.button] = {}
    search_state: dict[str, str] = {"term": ""}

    # Container reference (for refreshing)
    items_container: Any = None

    def refresh_items() -> None:
        """Refresh items list based on current filter settings."""
        nonlocal items_container
        if items_container is None:
            return

        items_container.clear()
        current_show_consumed = app.storage.browser.get(SHOW_CONSUMED_KEY, False)
        search_term = search_state["term"]

        with items_container:
            with next(get_session()) as session:
                # Get items based on consumed filter
                if current_show_consumed:
                    all_items = item_service.get_all_items(session)
                else:
                    all_items = item_service.get_active_items(session)

                # Build item-to-categories mapping
                item_category_map = _build_item_category_map(session, all_items)

                # Apply filters
                filtered_items = list(all_items)
                filtered_items = _filter_items_by_search(filtered_items, search_term)
                filtered_items = _filter_items_by_categories(filtered_items, selected_categories, item_category_map)

                if not all_items:
                    # No items at all - show empty state with CTA
                    _render_empty_state()
                elif filtered_items:
                    # Display filtered items as cards
                    for item in filtered_items:
                        create_item_card(item, session)
                else:
                    # Filters yielded no results
                    _render_no_filter_results()

    def on_toggle_change(e: Any) -> None:
        """Handle toggle change - store setting and refresh list."""
        app.storage.browser[SHOW_CONSUMED_KEY] = e.value
        refresh_items()

    def on_search_change(e: Any) -> None:
        """Handle search input change."""
        search_state["term"] = e.value or ""
        refresh_items()

    def update_chip_style(cat_id: int) -> None:
        """Update chip appearance based on selection state."""
        chip = chip_elements.get(cat_id)
        if chip:
            if cat_id in selected_categories:
                chip.classes(
                    remove="bg-gray-200 text-gray-800",
                    add="bg-primary text-white",
                )
            else:
                chip.classes(
                    remove="bg-primary text-white",
                    add="bg-gray-200 text-gray-800",
                )

    def toggle_category(cat_id: int) -> None:
        """Toggle category selection."""
        if cat_id in selected_categories:
            selected_categories.remove(cat_id)
        else:
            selected_categories.add(cat_id)
        update_chip_style(cat_id)
        refresh_items()

    # Header with toggle
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Vorrat").classes("text-h5 font-bold text-primary")
        # Toggle for showing consumed items
        ui.switch("Entnommene anzeigen", value=show_consumed, on_change=on_toggle_change).classes("text-sm")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Search input field at top
        with ui.row().classes("w-full mb-4"):
            ui.input(
                label="Suchen",
                placeholder="Produktname...",
                on_change=on_search_change,
            ).props("clearable").classes("w-full").props("dense outlined")

        # Category filter chips (load categories once)
        with next(get_session()) as session:
            all_categories = category_service.get_all_categories(session)

        if all_categories:
            with ui.row().classes("w-full gap-2 flex-wrap my-2"):
                for cat in all_categories:
                    if cat.id is not None:
                        chip = ui.button(
                            cat.name,
                            on_click=lambda _, cid=cat.id: toggle_category(cid),
                        ).classes("bg-gray-200 text-gray-800 rounded-full px-4 py-1 text-sm")
                        chip_elements[cat.id] = chip

        items_container = ui.column().classes("w-full gap-2")
        refresh_items()

    # Bottom Navigation
    create_bottom_nav(current_page="items")
