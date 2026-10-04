"""Dashboard - Main Page after Login (Mobile-First).

Based on UI_KONZEPT.md Section 3.2: Übersicht / Dashboard (Mobile)
Uses unified ItemCard component from Issue #173.
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...services import category_service
from ...services import expiry_service
from ...services import item_service
from ...services import location_service
from ...services.item_rows import get_item_rows
from ...services.preferences_service import get_expiry_thresholds
from ..components import create_bottom_nav
from ..components import create_bottom_sheet
from ..components import create_item_card
from ..components import create_mobile_page_container
from ..components import create_user_dropdown
from ..components.consume_all import confirm_consume_all
from ..components.flash import show_flash
from ..components.location_overview import create_location_overview_chips
from ..components.recently_added import create_recently_added_section
from ..theme.icons import create_icon
from nicegui import ui


@ui.page("/dashboard")
@require_auth
def dashboard() -> None:
    """Dashboard mit Ablaufübersicht und Statistiken (Mobile-First)."""
    # Theme-CSS und swipe-card.js kommen aus dem gemeinsamen Seitenkopf (app/startup.py, #375)
    # Nachricht eines vorangegangenen Redirects (z.B. "Keine Berechtigung") anzeigen (#381)
    show_flash()
    # Header with user dropdown (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        ui.label("Füllhorn").classes("sp-page-title")
        create_user_dropdown()

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        with next(get_session()) as session:
            # Items with status warning/critical (Issue #363: status-based, not best_before_date)
            expiring_items = expiry_service.get_items_expiring_soon(session)
            expiring_count = len(expiring_items)
            _, warning_days = get_expiry_thresholds(session)

            # Schnellerfassung für den Keller: nur Name, Menge, Einheit, Typ (Issue #463)
            with (
                ui.card()
                .classes("sp-dashboard-card w-full mb-4 cursor-pointer hover:shadow-sp-md transition-shadow")
                .on("click", lambda: ui.navigate.to("/items/quick"))
                .mark("dashboard-quick")
            ):
                with ui.row().classes("w-full items-center justify-between gap-2 no-wrap"):
                    with ui.column().classes("gap-1 flex-1 min-w-0"):
                        ui.label("Schnell erfassen").classes("text-base font-medium text-charcoal")
                        ui.label("Nur Name, Menge und Ort - den Rest später").classes("text-sm text-stone")
                    create_icon("navigation/add", size="24px")

            # Schnell erfasste Artikel warten auf die fehlenden Angaben (Issue #463). Der
            # Einstieg steht oben, weil das Nachpflegen im Warmen die Fortsetzung des
            # Erfassens im Keller ist; ohne Lücken bleibt die Zeile weg.
            incomplete_count = len(expiry_service.get_items_needing_completion(session))
            if incomplete_count:
                with (
                    ui.card()
                    .classes("sp-dashboard-card w-full mb-4 cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on("click", lambda: ui.navigate.to("/items/incomplete"))
                    .mark("dashboard-incomplete")
                ):
                    with ui.row().classes("w-full items-center justify-between gap-2 no-wrap"):
                        with ui.column().classes("gap-1 flex-1 min-w-0"):
                            ui.label(f"Nachpflegen ({incomplete_count})").classes("text-base font-medium text-charcoal")
                            ui.label("Fehlende Angaben ergänzen").classes("text-sm text-stone")
                        create_icon("actions/edit", size="24px")

            # Expiring items section with count badge (Issue #244)
            ui.label(f"Bald ablaufend ({expiring_count})").classes("sp-page-title text-base mb-3")

            if expiring_items:
                # Display expiring items using unified card component
                shown_items = expiring_items[:5]  # Show max 5 items
                for row in get_item_rows(session, shown_items):
                    create_item_card(
                        row,
                        on_consume=lambda i=row.item: handle_consume(i),
                        on_partial_consume=lambda i=row.item: handle_consume(i),
                        on_consume_all=lambda i=row.item: handle_consume_all(i),
                        on_edit=lambda i=row.item: ui.navigate.to(f"/items/{i.id}/edit"),
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
                    ui.label(f"Keine Artikel laufen in den nächsten {warning_days} Tagen ab.").classes(
                        "text-sm text-stone"
                    )

            # "Kürzlich hinzugefügt" section - recently added items (Issue #248)
            create_recently_added_section(session)

            # "Auf einen Blick" section - 2x2 tile grid (Issue #245)
            ui.label("Auf einen Blick").classes("sp-page-title text-base mb-3 mt-6")

            # Zählen statt alle Artikel laden (#393)
            active_item_count = item_service.count_active_items(session)
            locations = location_service.get_all_locations(session)
            categories = category_service.get_all_categories(session)

            with ui.element("div").classes("grid grid-cols-2 min-[480px]:grid-cols-4 gap-3 w-full"):
                # Tile 1: Artikel -> navigates to /items
                with (
                    ui.card()
                    .classes("sp-dashboard-card text-center cursor-pointer hover:shadow-sp-md transition-shadow")
                    .on("click", lambda: ui.navigate.to("/items"))
                ):
                    ui.label(str(active_item_count)).classes("sp-stats-number primary")
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
        # Buchungen rufen nur ihren Callback; on_close lädt nach Schließen ohne Buchung bzw. nach
        # veraltetem Bestand neu (#393, #394)
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
    """Handle consuming all of an item via swipe action (Issue #226, #367: with confirmation + user)."""
    confirm_consume_all(item, lambda: ui.navigate.to("/dashboard"))
