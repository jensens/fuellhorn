"""Dashboard - Main Page after Login (Mobile-First).

Based on UI_KONZEPT.md Section 3.2: Übersicht / Dashboard (Mobile)
"""

from ...auth import require_auth
from ...database import get_session
from ...models.item import Item
from ...services import item_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..components import create_user_dropdown
from datetime import date
from nicegui import ui


@ui.page("/dashboard")
@require_auth
def dashboard() -> None:
    """Dashboard mit Ablaufübersicht und Statistiken (Mobile-First)."""

    # Header with user dropdown
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Füllhorn").classes("text-h5 font-bold text-primary")
        create_user_dropdown()

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Expiring items section
        ui.label("🔴 Bald abgelaufen").classes("text-h6 font-semibold mb-3")

        with next(get_session()) as session:
            # Get items expiring in next 7 days
            expiring_items = item_service.get_items_expiring_soon(session, days=7)

            if expiring_items:
                # Display expiring items as cards
                for item in expiring_items[:5]:  # Show max 5 items
                    # Get proper expiry info via service (fixes #149)
                    # For MHD items: returns (None, None, best_before_date)
                    # For shelf-life items: returns (optimal_date, max_date, None)
                    optimal_date, max_date, mhd_date = item_service.get_item_expiry_info(
                        session,
                        item.id,  # type: ignore[arg-type]
                    )

                    # Determine effective expiry date for status calculation
                    if mhd_date is not None:
                        # MHD items: use best_before_date directly
                        effective_expiry = mhd_date
                    elif optimal_date is not None:
                        # Shelf-life items: use optimal date for status
                        effective_expiry = optimal_date
                    else:
                        # Fallback to item's best_before_date
                        effective_expiry = item.best_before_date

                    days_until_expiry = (effective_expiry - date.today()).days

                    # Status color
                    if days_until_expiry <= 0:
                        status_color = "red-500"
                        status_icon = "🔴"
                        status_text = "Heute abgelaufen" if days_until_expiry == 0 else "Abgelaufen"
                    elif days_until_expiry <= 3:
                        status_color = "red-500"
                        status_icon = "🔴"
                        status_text = (
                            f"Läuft ab: {'Morgen' if days_until_expiry == 1 else f'in {days_until_expiry} Tagen'}"
                        )
                    else:
                        status_color = "orange-500"
                        status_icon = "🟡"
                        status_text = f"Läuft ab: in {days_until_expiry} Tagen"

                    # Item card
                    with ui.card().classes(f"w-full mb-2 border-l-4 border-{status_color}"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column().classes("flex-1"):
                                ui.label(f"{status_icon} {item.product_name}").classes("font-medium")
                                ui.label(status_text).classes(f"text-sm text-{status_color}")
                                ui.label(f"📍 {item.location_id}").classes("text-xs text-gray-600")
                            ui.button("Entn.", on_click=lambda i=item: handle_consume(i)).props(
                                f"color={status_color} size=sm"
                            )
            else:
                ui.label("✅ Keine Artikel laufen in den nächsten 7 Tagen ab!").classes(
                    "text-green-600 p-4 bg-green-50 rounded"
                )

            # Statistics section
            ui.label("📊 Vorrats-Statistik").classes("text-h6 font-semibold mb-3 mt-6")

            all_items = item_service.get_all_items(session)
            consumed_items = [i for i in all_items if i.is_consumed]
            active_items = [i for i in all_items if not i.is_consumed]

            with ui.card().classes("w-full"):
                with ui.row().classes("w-full justify-around text-center"):
                    with ui.column():
                        ui.label(str(len(active_items))).classes("text-2xl font-bold text-primary")
                        ui.label("Artikel").classes("text-sm text-gray-600")
                    with ui.column():
                        ui.label(str(len(expiring_items))).classes("text-2xl font-bold text-orange-500")
                        ui.label("Ablauf").classes("text-sm text-gray-600")
                    with ui.column():
                        ui.label(str(len(consumed_items))).classes("text-2xl font-bold text-green-500")
                        ui.label("Entn.").classes("text-sm text-gray-600")

            # Quick filters section
            ui.label("🏷️ Schnellfilter").classes("text-h6 font-semibold mb-3 mt-6")

            # Get unique locations
            locations = set(item.location_id for item in active_items)

            with ui.row().classes("w-full gap-2 flex-wrap"):
                for loc_id in list(locations)[:4]:  # Show max 4 quick filters
                    ui.button(
                        f"Lagerort {loc_id}",
                        on_click=lambda loc=loc_id: ui.navigate.to(f"/items?location={loc}"),
                    ).props("outline color=primary size=sm")

    # Bottom Navigation (always visible)
    create_bottom_nav(current_page="dashboard")


def handle_consume(item: Item) -> None:
    """Handle consuming an item (opens dialog)."""
    # TODO: Implement consume dialog (Bottom Sheet)
    ui.notify(f"Entnehmen-Funktion für {item.product_name} wird implementiert", type="info")
