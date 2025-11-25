"""Categories Page - Admin page for managing categories (Mobile-First).

Based on Issue #20: Categories Page - Liste aller Kategorien
"""

from ...auth import Permission
from ...auth import require_permissions
from ...database import get_session
from ...services import category_service
from ..components import create_mobile_page_container
from nicegui import ui


@ui.page("/admin/categories")
@require_permissions(Permission.CONFIG_MANAGE)
def categories_page() -> None:
    """Categories management page (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/settings")).props("flat round color=gray-7")
            ui.label("Kategorien").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        ui.label("Kategorien verwalten").classes("text-h6 font-semibold mb-3")

        with next(get_session()) as session:
            categories = category_service.get_all_categories(session)

            if categories:
                # Display categories as cards
                for category in categories:
                    with ui.card().classes("w-full mb-2"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                # Color indicator
                                if category.color:
                                    ui.element("div").classes("w-6 h-6 rounded-full").style(
                                        f"background-color: {category.color}"
                                    )
                                else:
                                    ui.element("div").classes("w-6 h-6 rounded-full bg-gray-300")
                                # Category name
                                ui.label(category.name).classes("font-medium text-lg")
                            # Freeze time info (if set)
                            if category.freeze_time_months:
                                ui.label(f"{category.freeze_time_months} Mon.").classes("text-sm text-gray-600")
            else:
                # Empty state
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full items-center py-8"):
                        ui.icon("category", size="48px").classes("text-gray-400 mb-2")
                        ui.label("Keine Kategorien vorhanden").classes("text-gray-600 text-center")
                        ui.label("Kategorien helfen beim Organisieren des Vorrats.").classes(
                            "text-sm text-gray-500 text-center"
                        )
