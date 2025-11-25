"""Items Page - List view of all inventory items (Mobile-First).

Displays all non-consumed items as cards with expiry status.
Based on requirements from Issue #9.
Search functionality added in Issue #10.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...services import item_service
from ..components import create_bottom_nav
from ..components import create_item_card
from ..components import create_mobile_page_container
from nicegui import ui


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


def _render_no_search_results() -> None:
    """Render message when search yields no results."""
    with ui.card().classes("w-full p-6 text-center"):
        ui.icon("search_off").classes("text-6xl text-gray-300 mb-4")
        ui.label("Keine Artikel gefunden").classes("text-lg text-gray-600 mb-2")
        ui.label("Versuche einen anderen Suchbegriff").classes("text-sm text-gray-500")


def _filter_items(items: list[Item], search_term: str) -> list[Item]:
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


@ui.page("/items")
@require_auth
def items_page() -> None:
    """Items list page with card layout and search (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Vorrat").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        with next(get_session()) as session:
            # Get all active (non-consumed) items
            all_items = item_service.get_active_items(session)

            # Container for items that will be updated on search
            items_container = ui.column().classes("w-full gap-2")

            def update_items_display(search_term: str) -> None:
                """Update the displayed items based on search term."""
                items_container.clear()

                filtered_items = _filter_items(all_items, search_term)

                with items_container:
                    if not all_items:
                        # No items at all - show empty state with CTA
                        _render_empty_state()
                    elif filtered_items:
                        # Display filtered items as cards
                        for item in filtered_items:
                            create_item_card(item, session)
                    else:
                        # Search yielded no results
                        _render_no_search_results()

            # Search input field at top
            with ui.row().classes("w-full mb-4"):
                ui.input(
                    label="Suchen",
                    placeholder="Produktname...",
                    on_change=lambda e: update_items_display(e.value),
                ).props("clearable").classes("w-full").props("dense outlined")

            # Initial render with empty search
            update_items_display("")

    # Bottom Navigation
    create_bottom_nav(current_page="items")
