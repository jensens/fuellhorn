"""Dashboard - Main Page after Login (Mobile-First).

Based on UI_KONZEPT.md Section 3.2: Übersicht / Dashboard (Mobile)
Uses unified ItemCard component from Issue #173.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_bottom_sheet
from ..components import create_item_card
from ..components import create_mobile_page_container
from ..components import create_user_dropdown
from nicegui import ui


@ui.page("/dashboard")
@require_auth
def dashboard() -> None:
    """Dashboard mit Ablaufübersicht und Statistiken (Mobile-First)."""
    # Load swipe card CSS and JS (required for item card swipe actions)
    ui.add_head_html('<link rel="stylesheet" href="/static/css/solarpunk-theme.css">')
    ui.add_head_html('<script src="/static/js/swipe-card.js"></script>')

    # Header with user dropdown (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        ui.label("Füllhorn").classes("sp-page-title")
        create_user_dropdown()

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        with next(get_session()) as session:
            # Get items expiring in next 7 days
            expiring_items = item_service.get_items_expiring_soon(session, days=7)
            expiring_count = len(expiring_items)

            # Expiring items section with count badge (Issue #244)
            ui.label(f"Bald ablaufend ({expiring_count})").classes("sp-page-title text-base mb-3")

            if expiring_items:
                # Display expiring items using unified card component
                for item in expiring_items[:5]:  # Show max 5 items
                    create_item_card(
                        item,
                        session,
                        on_consume=lambda i=item: handle_consume(i),  # type: ignore[misc]
                        on_partial_consume=lambda i=item: handle_consume(i),  # type: ignore[misc]
                        on_consume_all=lambda i=item: handle_consume_all(i),  # type: ignore[misc]
                        on_edit=lambda i=item: ui.navigate.to(f"/items/{i.id}/edit"),  # type: ignore[misc]
                    )

                # "Alle anzeigen" link (Issue #244)
                ui.link("Alle anzeigen", "/items?filter=expiring").classes(
                    "text-sm text-leaf hover:text-leaf-dark mt-2 block"
                )
            else:
                # Improved empty state with leaf icon (Issue #244)
                with ui.card().classes("sp-dashboard-card w-full p-6 text-center"):
                    ui.icon("eco").classes("text-4xl text-leaf mb-2")
                    ui.label("Alles frisch!").classes("text-lg text-charcoal font-medium")
                    ui.label("Keine Artikel laufen in den nächsten 7 Tagen ab.").classes("text-sm text-stone")

            # Statistics section
            ui.label("Vorrats-Statistik").classes("sp-page-title text-base mb-3 mt-6")

            all_items = item_service.get_all_items(session)
            consumed_items = [i for i in all_items if i.is_consumed]
            active_items = [i for i in all_items if not i.is_consumed]

            with ui.card().classes("sp-dashboard-card w-full"):
                with ui.row().classes("sp-stats-row w-full"):
                    with ui.column():
                        ui.label(str(len(active_items))).classes("sp-stats-number primary")
                        ui.label("Artikel").classes("sp-stats-label")
                    with ui.column():
                        ui.label(str(len(expiring_items))).classes("sp-stats-number warning")
                        ui.label("Ablauf").classes("sp-stats-label")
                    with ui.column():
                        ui.label(str(len(consumed_items))).classes("sp-stats-number success")
                        ui.label("Entn.").classes("sp-stats-label")

            # Quick filters section
            ui.label("Schnellfilter").classes("sp-page-title text-base mb-3 mt-6")

            # Get unique locations with names
            location_items: dict[int, str] = {}
            for item in active_items:
                if item.location_id not in location_items:
                    try:
                        loc = location_service.get_location(session, item.location_id)
                        location_items[item.location_id] = loc.name
                    except ValueError:
                        location_items[item.location_id] = f"Lagerort {item.location_id}"

            with ui.row().classes("w-full gap-2 flex-wrap"):
                for loc_id, loc_name in list(location_items.items())[:4]:  # Show max 4 quick filters
                    ui.button(
                        loc_name,
                        on_click=lambda loc=loc_id: ui.navigate.to(f"/items?location={loc}"),
                    ).classes("sp-quick-filter").props("flat no-caps")

    # Bottom Navigation (always visible)
    create_bottom_nav(current_page="dashboard")


def handle_consume(item: Item) -> None:
    """Handle consuming an item - opens bottom sheet with details."""

    def refresh_dashboard() -> None:
        """Refresh dashboard after action."""
        ui.navigate.to("/dashboard")

    with next(get_session()) as session:
        location = location_service.get_location(session, item.location_id)
        sheet = create_bottom_sheet(
            item=item,
            location=location,
            on_close=refresh_dashboard,
            on_withdraw=lambda _: refresh_dashboard(),
            on_edit=lambda i: ui.navigate.to(f"/items/{i.id}/edit"),
            on_consume=lambda _: refresh_dashboard(),
        )
        sheet.open()


def handle_consume_all(item: Item) -> None:
    """Handle consuming all of an item via swipe action (Issue #226)."""
    with next(get_session()) as session:
        item_service.mark_item_consumed(session, item.id)  # type: ignore[arg-type]
        ui.notify(f"{item.product_name} komplett entnommen", type="positive")
    ui.navigate.to("/dashboard")
