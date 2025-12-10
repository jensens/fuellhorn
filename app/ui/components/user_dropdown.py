"""User Dropdown Component - Dropdown menu in header for user actions.

Based on Issue #83: User-Dropdown im Header statt 'Mehr' in Bottom Nav
- Username is clickable
- Opens dropdown with: Profil, Einstellungen (admin only), Abmelden
"""

from ...auth import Permission
from ...auth import get_current_user
from ...auth import get_permissions_for_user
from ..auth import logout
from ..theme.icons import create_icon
from nicegui import app
from nicegui import ui


def create_user_dropdown() -> None:
    """Create a clickable username with dropdown menu.

    The dropdown contains:
    - Profil (all users) → /profile
    - Einstellungen (only for admin users) → /admin/settings
    - Abmelden → logout
    """
    username = app.storage.user.get("username", "User")

    # Get current user to check permissions
    current_user = get_current_user(require_auth=False)
    is_admin = False
    if current_user:
        permissions = get_permissions_for_user(current_user)
        is_admin = Permission.CONFIG_MANAGE in permissions

    # Clickable username with dropdown
    with ui.button(on_click=lambda: None).props("flat no-caps color=gray-7").classes("text-sm"):
        with ui.row().classes("items-center gap-2"):
            create_icon("misc/user", size="20px")
            ui.label(username)
        with ui.menu().classes("min-w-40"):
            # Profile link (all users)
            with ui.menu_item(on_click=lambda: ui.navigate.to("/profile")):
                with ui.row().classes("items-center gap-2"):
                    create_icon("misc/user", size="20px")
                    ui.label("Profil")

            # Settings link (admin only)
            if is_admin:
                with ui.menu_item(on_click=lambda: ui.navigate.to("/admin/settings")):
                    with ui.row().classes("items-center gap-2"):
                        create_icon("misc/settings", size="20px")
                        ui.label("Einstellungen")

            # Logout option
            with ui.menu_item(on_click=logout):
                with ui.row().classes("items-center gap-2"):
                    create_icon("misc/logout", size="20px")
                    ui.label("Abmelden")
