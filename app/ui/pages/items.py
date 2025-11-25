"""Items Page - List view of all inventory items (Mobile-First).

Displays all non-consumed items as cards with expiry status.
Based on requirements from Issue #9.
"""

from ...auth import require_auth
from ...database import get_session
from ...services import item_service
from ..components import create_bottom_nav
from ..components import create_item_card
from ..components import create_mobile_page_container
from nicegui import ui


@ui.page("/items")
@require_auth
def items_page() -> None:
    """Items list page with card layout (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Vorrat").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        with next(get_session()) as session:
            # Get all active (non-consumed) items
            items = item_service.get_active_items(session)

            if items:
                # Display items as cards
                for item in items:
                    create_item_card(item, session)
            else:
                # Empty state
                with ui.card().classes("w-full p-6 text-center"):
                    ui.icon("inventory_2").classes("text-6xl text-gray-300 mb-4")
                    ui.label("Keine Artikel vorhanden").classes("text-lg text-gray-600 mb-2")
                    ui.label("Erfasse deinen ersten Artikel!").classes("text-sm text-gray-500")
                    ui.button(
                        "Artikel erfassen",
                        on_click=lambda: ui.navigate.to("/add-item"),
                    ).classes("mt-4")

    # Bottom Navigation
    create_bottom_nav(current_page="items")
