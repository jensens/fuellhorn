"""More Page - 'Mehr' Page with Logout (Mobile-First).

Based on Issue #18: Logout-Button im Header/Navigation
Im 'Mehr'-Bereich der Bottom Navigation.
"""

from ...auth import require_auth
from ..auth import logout
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from nicegui import app
from nicegui import ui


@ui.page("/settings")
@require_auth
def more_page() -> None:
    """More page with logout button (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Mehr").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # User info section
        username = app.storage.user.get("username", "User")

        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.icon("account_circle", size="48px").classes("text-primary")
                with ui.column().classes("flex-1"):
                    ui.label(username).classes("text-lg font-medium")
                    ui.label("Angemeldet").classes("text-sm text-gray-600")

        # Settings options
        ui.label("Einstellungen").classes("text-h6 font-semibold mb-3")

        with ui.card().classes("w-full mb-4"):
            with ui.column().classes("w-full gap-2"):
                with (
                    ui.row()
                    .classes("w-full items-center justify-between p-2 cursor-pointer hover:bg-gray-100 rounded")
                    .on("click", lambda: ui.navigate.to("/admin/settings"))
                ):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("settings", size="24px").classes("text-gray-600")
                        ui.label("Gefrierzeit-Konfiguration").classes("text-base")
                    ui.icon("chevron_right", size="24px").classes("text-gray-400")

                with ui.row().classes(
                    "w-full items-center justify-between p-2 cursor-pointer hover:bg-gray-100 rounded"
                ):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("info", size="24px").classes("text-gray-600")
                        ui.label("Über Füllhorn").classes("text-base")
                    ui.icon("chevron_right", size="24px").classes("text-gray-400")

        # Logout section
        ui.label("Konto").classes("text-h6 font-semibold mb-3 mt-6")

        # Logout button - prominent, touch-friendly
        ui.button(
            "Abmelden",
            icon="logout",
            on_click=logout,
        ).props("color=negative size=lg outline").classes("w-full").style("min-height: 48px")

    # Bottom Navigation
    create_bottom_nav(current_page="more")
