"""Users Page - Admin page for managing users (Mobile-First).

Based on Issue #28: Users Page - Liste aller Benutzer
"""

from ...auth import Permission
from ...auth import require_permissions
from ...database import get_session
from ...services import auth_service
from ..components import create_mobile_page_container
from nicegui import ui


@ui.page("/admin/users")
@require_permissions(Permission.USER_MANAGE)
def users_page() -> None:
    """Users management page (Mobile-First)."""
    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/settings")).props("flat round color=gray-7")
            ui.label("Benutzer").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Section header
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Benutzer verwalten").classes("text-h6 font-semibold")

        _render_users_list()


def _render_users_list() -> None:
    """Render the list of users."""
    with next(get_session()) as session:
        users = auth_service.list_users(session)

        if users:
            # Display users as cards
            for user in users:
                with ui.card().classes("w-full mb-2"):
                    with ui.row().classes("w-full items-center justify-between"):
                        # Left side: username and role
                        with ui.column().classes("gap-0"):
                            ui.label(user.username).classes("font-medium text-lg")
                            # Role badge
                            role_display = "Admin" if user.role == "admin" else "Benutzer"
                            role_color = "primary" if user.role == "admin" else "grey"
                            ui.badge(role_display, color=role_color).classes("mt-1")

                        # Right side: status and last login
                        with ui.column().classes("gap-0 items-end"):
                            # Status indicator
                            status_text = "Aktiv" if user.is_active else "Inaktiv"
                            status_color = "text-green-600" if user.is_active else "text-red-600"
                            ui.label(status_text).classes(f"text-sm font-medium {status_color}")

                            # Last login
                            if user.last_login:
                                login_date = user.last_login.strftime("%d.%m.%Y")
                                login_time = user.last_login.strftime("%H:%M")
                                ui.label(f"{login_date} {login_time}").classes("text-xs text-gray-500")
                            else:
                                ui.label("Nie angemeldet").classes("text-xs text-gray-400")
        else:
            # Empty state (shouldn't happen since there's always at least one admin)
            with ui.card().classes("w-full"):
                with ui.column().classes("w-full items-center py-8"):
                    ui.icon("person_off", size="48px").classes("text-gray-400 mb-2")
                    ui.label("Keine Benutzer vorhanden").classes("text-gray-600 text-center")
