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
from ...models.item import ItemType
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_bottom_sheet
from ..components import create_item_card
from ..components import create_mobile_page_container
from ..theme import get_contrast_text_color
from ..theme.icons import create_icon
from nicegui import app
from nicegui import ui
from typing import Any


# User storage key for consumed items filter (persisted across page reloads)
SHOW_CONSUMED_KEY = "show_consumed_items"


# Sorting options
SORT_OPTIONS: dict[str, str] = {
    "best_before_date": "Haltbarkeitsdatum",
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
    with ui.card().classes("sp-dashboard-card w-full p-6 text-center"):
        with ui.element("div").classes("mb-4"):
            create_icon("navigation/inventory", size="64px", classes="text-stone")
        ui.label("Keine Artikel vorhanden").classes("text-lg text-charcoal mb-2")
        ui.label("Erfasse deinen ersten Artikel!").classes("text-sm text-stone")
        ui.button(
            "Artikel erfassen",
            on_click=lambda: ui.navigate.to("/add-item"),
        ).classes("mt-4 sp-btn-primary")


def _render_no_filter_results() -> None:
    """Render message when filters yield no results."""
    with ui.card().classes("sp-dashboard-card w-full p-6 text-center"):
        ui.icon("search_off").classes("text-6xl text-stone mb-4")
        ui.label("Keine Artikel gefunden").classes("text-lg text-charcoal mb-2")
        ui.label("Versuche andere Filter oder Suchbegriffe").classes("text-sm text-stone")


def _render_no_consumed_items() -> None:
    """Render message when no items have been withdrawn yet."""
    with ui.card().classes("sp-dashboard-card w-full p-6 text-center"):
        with ui.element("div").classes("mb-4"):
            create_icon("status/ok", size="64px", classes="text-stone")
        ui.label("Keine Entnahmen").classes("text-lg text-charcoal mb-2")
        ui.label("Es wurden noch keine Artikel entnommen.").classes("text-sm text-stone")


def _build_item_category_map(items: list[Item]) -> dict[int, int | None]:
    """Build a mapping from item IDs to their category ID.

    Args:
        items: List of items

    Returns:
        Dictionary mapping item ID to category ID (or None)
    """
    return {item.id: item.category_id for item in items if item.id is not None}


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
    item_category_map: dict[int, int | None],
) -> list[Item]:
    """Filter items by selected categories (OR logic).

    Args:
        items: List of items to filter
        selected_categories: Set of selected category IDs
        item_category_map: Mapping of item IDs to category ID

    Returns:
        Filtered list of items that have one of the selected categories
    """
    if not selected_categories:
        return items

    return [item for item in items if item.id is not None and item_category_map.get(item.id) in selected_categories]


def _sort_items(items: list[Item], sort_field: str, ascending: bool) -> list[Item]:
    """Sort items by the specified field.

    Args:
        items: List of items to sort
        sort_field: Field to sort by (best_before_date, product_name, created_at)
        ascending: True for ascending, False for descending

    Returns:
        Sorted list of items
    """
    if sort_field == "best_before_date":
        return sorted(items, key=lambda x: x.best_before_date, reverse=not ascending)
    elif sort_field == "product_name":
        return sorted(items, key=lambda x: x.product_name.lower(), reverse=not ascending)
    elif sort_field == "created_at":
        return sorted(items, key=lambda x: x.created_at, reverse=not ascending)
    return items


@ui.page("/items")
@require_auth
def items_page() -> None:
    """Items list page with card layout, search, and all filters (Mobile-First)."""
    # Load swipe card CSS and JS (required for item card swipe actions)
    ui.add_head_html('<link rel="stylesheet" href="/static/css/solarpunk-theme.css">')
    ui.add_head_html('<script src="/static/js/swipe-card.js"></script>')

    # Read filter setting from user storage (persisted server-side per user session)
    initial_show_consumed = app.storage.user.get(SHOW_CONSUMED_KEY, False)

    # State for filters and sorting (includes show_consumed for immediate updates)
    filter_state: dict[str, Any] = {
        "search_term": "",
        "location_id": 0,  # 0 = all locations
        "item_type": "",  # "" = all types
        "sort_field": "best_before_date",  # Default: sort by best_before_date
        "sort_ascending": True,  # Default: ascending (soonest first)
        "show_consumed": initial_show_consumed,  # Track toggle state locally
    }
    selected_categories: set[int] = set()
    chip_elements: dict[int, ui.button] = {}
    category_colors: dict[int, str] = {}  # Store category colors for styling
    sort_direction_btn: ui.button | None = None
    sort_row: ui.row | None = None  # Reference for hiding when consumed toggle is on

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

        with items_container:
            with next(get_session()) as session:
                # Get items based on consumed filter (use local state for immediate updates)
                if filter_state["show_consumed"]:
                    # Show only consumed/partially withdrawn items, sorted by last withdrawal
                    all_items = item_service.get_consumed_items(session)
                else:
                    all_items = item_service.get_active_items(session)

                # Build item-to-category mapping
                item_category_map = _build_item_category_map(all_items)

                # Apply all filters (search, location, item type)
                filtered_items = _filter_items(
                    all_items,
                    filter_state["search_term"],
                    filter_state["location_id"],
                    filter_state["item_type"],
                )

                # Apply category filter
                filtered_items = _filter_items_by_categories(filtered_items, selected_categories, item_category_map)

                # Apply sorting (skip when showing consumed - already sorted by withdrawal date)
                if not filter_state["show_consumed"]:
                    filtered_items = _sort_items(
                        filtered_items,
                        filter_state["sort_field"],
                        filter_state["sort_ascending"],
                    )

                if not all_items:
                    # No items - show appropriate empty state
                    if filter_state["show_consumed"]:
                        _render_no_consumed_items()
                    else:
                        _render_empty_state()
                elif filtered_items:
                    # Display filtered items as cards with consume button and swipe actions
                    for item in filtered_items:
                        create_item_card(
                            item,
                            session,
                            on_consume=handle_consume,
                            on_partial_consume=handle_consume,  # Swipe "Teil" -> opens dialog
                            on_consume_all=handle_consume_all,  # Swipe "Alles" -> consume all
                            on_edit=lambda i=item: ui.navigate.to(f"/items/{i.id}/edit"),  # type: ignore[misc]
                        )
                else:
                    # Filters yielded no results
                    _render_no_filter_results()

    def on_toggle_change(e: Any) -> None:
        """Handle toggle change - update local state and persist to user storage."""
        filter_state["show_consumed"] = e.value
        app.storage.user[SHOW_CONSUMED_KEY] = e.value
        # Hide sort controls when showing consumed (sorted by withdrawal date)
        if sort_row:
            sort_row.set_visibility(not e.value)
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
        filter_state["sort_field"] = e.value if e.value else "best_before_date"
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
        """Update chip appearance based on selection state and category color."""
        chip = chip_elements.get(cat_id)
        color = category_colors.get(cat_id, "#6B7280")  # Default gray if no color
        text_color = get_contrast_text_color(color)
        if chip:
            if cat_id in selected_categories:
                # Selected: Full background in category color, contrast text
                chip.style(
                    f"background-color: {color} !important; border: 2px solid {color}; color: {text_color} !important;"
                )
            else:
                # Not selected: Gray background, colored border
                chip.style(
                    "background-color: #E5E7EB !important; border: 2px solid " + color + "; color: #374151 !important;"
                )

    def toggle_category(cat_id: int) -> None:
        """Toggle category selection."""
        if cat_id in selected_categories:
            selected_categories.remove(cat_id)
        else:
            selected_categories.add(cat_id)
        update_chip_style(cat_id)
        refresh_items()

    def handle_consume(item: Item) -> None:
        """Handle consume button click - opens bottom sheet with item details."""
        with next(get_session()) as session:
            location = location_service.get_location(session, item.location_id)
            sheet = create_bottom_sheet(
                item=item,
                location=location,
                on_close=refresh_items,
                on_withdraw=lambda _: refresh_items(),
                on_edit=lambda i: ui.navigate.to(f"/items/{i.id}/edit"),
                on_consume=lambda _: refresh_items(),
            )
            sheet.open()

    def handle_consume_all(item: Item) -> None:
        """Handle consuming all of an item via swipe action (Issue #226)."""
        with next(get_session()) as session:
            item_service.mark_item_consumed(session, item.id)  # type: ignore[arg-type]
            ui.notify(f"{item.product_name} komplett entnommen", type="positive")
        refresh_items()

    # Header with toggle (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        ui.label("Vorrat").classes("sp-page-title")
        # Toggle for showing consumed items
        ui.switch("Entnommene anzeigen", value=initial_show_consumed, on_change=on_toggle_change).classes("text-sm")

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

        # Sorting row (hidden when showing consumed items - they're sorted by withdrawal date)
        sort_row = ui.row().classes("w-full gap-2 items-center mb-2")
        sort_row.set_visibility(not initial_show_consumed)
        with sort_row:
            ui.select(
                label="Sortierung",
                options=SORT_OPTIONS,
                value="best_before_date",
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
                        # Store category color for styling
                        color = cat.color or "#6B7280"  # Default gray
                        category_colors[cat.id] = color

                        # Create chip with colored dot prefix
                        chip = (
                            ui.button(
                                f"● {cat.name}",
                                on_click=lambda _, cid=cat.id: toggle_category(cid),
                            )
                            .classes("rounded-full px-4 py-1 text-sm")
                            .props("flat no-caps")
                        )
                        # Apply initial unselected style with category color (!important to override defaults)
                        chip.style(
                            f"background-color: #E5E7EB !important; border: 2px solid {color}; color: #374151 !important;"
                        )
                        chip_elements[cat.id] = chip

        items_container = ui.column().classes("w-full gap-2")
        refresh_items()

    # Bottom Navigation
    create_bottom_nav(current_page="items")
