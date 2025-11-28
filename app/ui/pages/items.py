"""Items Page - List view of all inventory items (Mobile-First).

Displays all non-consumed items as cards with expiry status.
Based on requirements from Issue #9.
Search functionality added in Issue #10.
Category filter added in Issue #11.
Filter by location and item type added in Issue #12.
Sorting added in Issue #13.
Extended in Issue #17 to allow showing consumed items via toggle.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...models.item import ItemCategory
from ...models.item import ItemType
from ...services import category_service
from ...services import item_service
from ...services import location_service
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

# Sorting options
SORT_OPTIONS: dict[str, str] = {
    "expiry_date": "Ablaufdatum",
    "product_name": "Produktname",
    "created_at": "Erfassungsdatum",
}

# Human-readable labels for item types
ITEM_TYPE_LABELS: dict[str, str] = {
    "": "Alle Typen",
    ItemType.PURCHASED_FRESH.value: "Frisch gekauft",
    ItemType.PURCHASED_FROZEN.value: "TK-Ware gekauft",
    ItemType.PURCHASED_THEN_FROZEN.value: "Gekauft → eingefroren",
    ItemType.HOMEMADE_FROZEN.value: "Selbst eingefroren",
    ItemType.HOMEMADE_PRESERVED.value: "Eingemacht",
}


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


def _filter_items(
    items: list[Item],
    search_term: str,
    location_id: int | None = None,
    item_type: str | None = None,
) -> list[Item]:
    """Filter items by product name, location, and item type.

    Args:
        items: List of items to filter
        search_term: Search term to filter by (case-insensitive)
        location_id: Location ID to filter by (None or 0 = all locations)
        item_type: Item type value to filter by (None or "" = all types)

    Returns:
        Filtered list of items
    """
    result = items

    # Filter by search term
    if search_term:
        term_lower = search_term.lower()
        result = [item for item in result if term_lower in item.product_name.lower()]

    # Filter by location
    if location_id and location_id > 0:
        result = [item for item in result if item.location_id == location_id]

    # Filter by item type
    if item_type:
        result = [item for item in result if item.item_type.value == item_type]

    return result


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


def _sort_items(items: list[Item], sort_field: str, ascending: bool) -> list[Item]:
    """Sort items by the specified field.

    Args:
        items: List of items to sort
        sort_field: Field to sort by (expiry_date, product_name, created_at)
        ascending: True for ascending, False for descending

    Returns:
        Sorted list of items
    """
    if sort_field == "expiry_date":
        return sorted(items, key=lambda x: x.expiry_date, reverse=not ascending)
    elif sort_field == "product_name":
        return sorted(items, key=lambda x: x.product_name.lower(), reverse=not ascending)
    elif sort_field == "created_at":
        return sorted(items, key=lambda x: x.created_at, reverse=not ascending)
    return items


@ui.page("/items")
@require_auth
def items_page() -> None:
    """Items list page with card layout, search, and all filters (Mobile-First)."""

    # Read filter setting from browser storage (default: False = hide consumed)
    show_consumed = app.storage.browser.get(SHOW_CONSUMED_KEY, False)

    # State for filters and sorting
    filter_state: dict[str, Any] = {
        "search_term": "",
        "location_id": 0,  # 0 = all locations
        "item_type": "",  # "" = all types
        "sort_field": "expiry_date",  # Default: sort by expiry date
        "sort_ascending": True,  # Default: ascending (soonest first)
    }
    selected_categories: set[int] = set()
    chip_elements: dict[int, ui.button] = {}
    sort_direction_btn: ui.button | None = None

    # Container reference (for refreshing)
    items_container: Any = None

    # Load locations for filter dropdown
    with next(get_session()) as session:
        locations = location_service.get_all_locations(session)
        location_options: dict[int, str] = {0: "Alle Lagerorte"}
        location_options.update({loc.id: loc.name for loc in locations if loc.id is not None})

    def refresh_items() -> None:
        """Refresh items list based on current filter settings."""
        nonlocal items_container
        if items_container is None:
            return

        items_container.clear()
        current_show_consumed = app.storage.browser.get(SHOW_CONSUMED_KEY, False)

        with items_container:
            with next(get_session()) as session:
                # Get items based on consumed filter
                if current_show_consumed:
                    all_items = item_service.get_all_items(session)
                else:
                    all_items = item_service.get_active_items(session)

                # Build item-to-categories mapping
                item_category_map = _build_item_category_map(session, all_items)

                # Apply all filters (search, location, item type)
                filtered_items = _filter_items(
                    all_items,
                    filter_state["search_term"],
                    filter_state["location_id"],
                    filter_state["item_type"],
                )

                # Apply category filter
                filtered_items = _filter_items_by_categories(filtered_items, selected_categories, item_category_map)

                # Apply sorting
                filtered_items = _sort_items(
                    filtered_items,
                    filter_state["sort_field"],
                    filter_state["sort_ascending"],
                )

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
        filter_state["search_term"] = e.value or ""
        refresh_items()

    def on_location_change(e: Any) -> None:
        """Handle location filter change."""
        filter_state["location_id"] = e.value if e.value else 0
        refresh_items()

    def on_item_type_change(e: Any) -> None:
        """Handle item type filter change."""
        filter_state["item_type"] = e.value if e.value else ""
        refresh_items()

    def on_sort_field_change(e: Any) -> None:
        """Handle sort field change."""
        filter_state["sort_field"] = e.value if e.value else "expiry_date"
        refresh_items()

    def toggle_sort_direction() -> None:
        """Toggle between ascending and descending sort."""
        nonlocal sort_direction_btn
        filter_state["sort_ascending"] = not filter_state["sort_ascending"]
        # Update button icon
        if sort_direction_btn:
            new_icon = "arrow_upward" if filter_state["sort_ascending"] else "arrow_downward"
            sort_direction_btn.props(f"icon={new_icon}")
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
        with ui.row().classes("w-full mb-2"):
            ui.input(
                label="Suchen",
                placeholder="Produktname...",
                on_change=on_search_change,
            ).props("clearable dense outlined").classes("w-full")

        # Filter dropdowns row
        with ui.row().classes("w-full gap-2 mb-2"):
            # Location filter
            ui.select(
                label="Lagerort",
                options=location_options,
                value=0,
                on_change=on_location_change,
            ).props("dense outlined").classes("flex-1")

            # Item type filter
            ui.select(
                label="Artikel-Typ",
                options=ITEM_TYPE_LABELS,
                value="",
                on_change=on_item_type_change,
            ).props("dense outlined").classes("flex-1")

        # Sorting row
        with ui.row().classes("w-full gap-2 items-center mb-2"):
            ui.select(
                label="Sortierung",
                options=SORT_OPTIONS,
                value="expiry_date",
                on_change=on_sort_field_change,
            ).props("dense outlined").classes("flex-1")

            # Direction toggle button
            sort_direction_btn = ui.button(
                icon="arrow_upward",
                on_click=toggle_sort_direction,
            ).props("flat dense")

        # Category filter chips (load categories once)
        with next(get_session()) as session:
            all_categories = category_service.get_all_categories(session)

        if all_categories:
            with ui.row().classes("w-full gap-2 flex-wrap mb-4"):
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
