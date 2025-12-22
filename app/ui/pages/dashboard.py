"""Dashboard - Main Page after Login (Mobile-First).

Based on UI_KONZEPT.md Section 3.2: Übersicht / Dashboard (Mobile)
Uses unified ItemCard component from Issue #173.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_bottom_sheet
from ..components import create_item_card
from ..components import create_mobile_page_container
from ..components import create_user_dropdown
from ..components.location_overview import create_location_overview_chips
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

            # "Auf einen Blick" section - 2x2 tile grid (Issue #245)
            ui.label("Auf einen Blick").classes("sp-page-title text-base mb-3 mt-6")

            all_items = item_service.get_all_items(session)
            active_items = [i for i in all_items if not i.is_consumed]
            locations = location_service.get_all_locations(session)
            categories = category_service.get_all_categories(session)

            with ui.element("div").classes("grid grid-cols-2 gap-3"):
                # Tile 1: Artikel -> navigates to /items
                with (
                    ui.card()
                    .classes("sp-dashboard-card text-center cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on("click", lambda: ui.navigate.to("/items"))
                ):
                    ui.label(str(len(active_items))).classes("sp-stats-number primary")
                    ui.label("Artikel").classes("sp-stats-label")

                # Tile 2: Ablauf -> navigates to /items?filter=expiring
                with (
                    ui.card()
                    .classes("sp-dashboard-card text-center cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on("click", lambda: ui.navigate.to("/items?filter=expiring"))
                ):
                    ui.label(str(expiring_count)).classes("sp-stats-number warning")
                    ui.label("Ablauf").classes("sp-stats-label")

                # Tile 3: Lagerorte -> scrolls to Lagerorte section
                with (
                    ui.card()
                    .classes("sp-dashboard-card text-center cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on(
                        "click",
                        lambda: ui.run_javascript(
                            "document.getElementById('locations-section').scrollIntoView({behavior: 'smooth'})"
                        ),
                    )
                ):
                    ui.label(str(len(locations))).classes("sp-stats-number primary")
                    ui.label("Lagerorte").classes("sp-stats-label")

                # Tile 4: Kategorien -> scrolls to Kategorien section (future)
                with (
                    ui.card()
                    .classes("sp-dashboard-card text-center cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on(
                        "click",
                        lambda: ui.run_javascript(
                            "document.getElementById('categories-section')?.scrollIntoView({behavior: 'smooth'})"
                        ),
                    )
                ):
                    ui.label(str(len(categories))).classes("sp-stats-number primary")
                    ui.label("Kategorien").classes("sp-stats-label")

            # Location overview section (Issue #246)
            with ui.element("div").props('id="locations-section"'):
                ui.label("Lagerorte").classes("sp-page-title text-base mb-3 mt-6")

            # Get item counts for locations (locations already fetched above)
            item_counts = item_service.get_item_count_by_location(session)

            create_location_overview_chips(
                locations=locations,
                item_counts=item_counts,
            )

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
