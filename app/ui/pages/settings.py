"""Settings Page - Übersicht und Navigation zu Admin-Bereichen.

Based on Issue #79: Settings Page aufteilen - Navigation zu Admin-Bereichen.
Issue #34: Smart Default Zeitfenster konfigurieren.
Issue #85: System-Defaults in DB speichern (Fallback für User ohne eigene Einstellungen).
"""

from ...auth import Permission
from ...auth import get_current_user
from ...auth import require_permissions
from ...database import get_engine
from ...services import preferences_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from nicegui import ui
from sqlmodel import Session


# Default time windows in minutes (hardcoded fallback)
DEFAULT_ITEM_TYPE_TIME_WINDOW = 30
DEFAULT_CATEGORY_TIME_WINDOW = 30
DEFAULT_LOCATION_TIME_WINDOW = 60


@ui.page("/admin/settings")
@require_permissions(Permission.CONFIG_MANAGE)
def settings() -> None:
    """Settings page with admin navigation and system defaults (Admin only)."""
    # Header (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/dashboard")).classes("sp-back-btn").props(
                "flat round"
            )
            ui.label("Einstellungen").classes("sp-page-title")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Admin Navigation section
        _render_admin_navigation()

        # Separator
        ui.separator().classes("my-4")

        # System Default Settings section (Issue #85)
        _render_system_defaults_section()

    # Bottom Navigation (no item active - accessed via user dropdown)
    create_bottom_nav(current_page="")


def _render_admin_navigation() -> None:
    """Render navigation links to admin areas (Solarpunk theme)."""
    ui.label("Verwaltung").classes("text-h6 font-semibold mb-3 text-fern")

    # Navigation cards (Solarpunk theme)
    nav_items = [
        {"icon": "category", "label": "Kategorien", "route": "/admin/categories"},
        {"icon": "place", "label": "Lagerorte", "route": "/admin/locations"},
        {"icon": "people", "label": "Benutzer", "route": "/admin/users"},
    ]

    for item in nav_items:
        with (
            ui.card()
            .classes("sp-dashboard-card w-full mb-2 cursor-pointer")
            .on("click", lambda r=item["route"]: ui.navigate.to(r))
        ):
            with ui.row().classes("w-full items-center justify-between p-2"):
                with ui.row().classes("items-center gap-3"):
                    ui.icon(item["icon"]).classes("text-fern")
                    ui.label(item["label"]).classes("font-medium text-charcoal")
                ui.icon("chevron_right").classes("text-stone")


def _get_system_defaults() -> dict:
    """Get system defaults from database."""
    with Session(get_engine()) as session:
        item_type_setting = preferences_service.get_system_setting(session, "item_type_time_window")
        category_setting = preferences_service.get_system_setting(session, "category_time_window")
        location_setting = preferences_service.get_system_setting(session, "location_time_window")

        return {
            "item_type_time_window": int(item_type_setting.value)
            if item_type_setting
            else DEFAULT_ITEM_TYPE_TIME_WINDOW,
            "category_time_window": int(category_setting.value) if category_setting else DEFAULT_CATEGORY_TIME_WINDOW,
            "location_time_window": int(location_setting.value) if location_setting else DEFAULT_LOCATION_TIME_WINDOW,
        }


def _render_system_defaults_section() -> None:
    """Render the System Default settings section (Issue #85) (Solarpunk theme).

    These are fallback values for users who haven't set their own preferences.
    """
    current_user = get_current_user(require_auth=True)
    defaults = _get_system_defaults()

    ui.label("System-Standardwerte").classes("text-h6 font-semibold mb-3 text-fern")

    with ui.card().classes("sp-dashboard-card w-full p-4"):
        ui.label("Zeitfenster für automatische Vorbelegung").classes("text-body2 text-charcoal mb-2")
        ui.label(
            "Diese Werte gelten als Fallback für Benutzer, die keine eigenen Einstellungen vorgenommen haben. "
            "Jeder Benutzer kann seine persönlichen Zeitfenster in seinem Profil anpassen."
        ).classes("text-caption text-stone mb-4")

        # Item type time window
        item_type_input = ui.number(
            label="Artikel-Typ Zeitfenster (Minuten)",
            value=defaults["item_type_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-2")

        # Category time window
        category_input = ui.number(
            label="Kategorie Zeitfenster (Minuten)",
            value=defaults["category_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-2")

        # Location time window
        location_input = ui.number(
            label="Lagerort Zeitfenster (Minuten)",
            value=defaults["location_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-4")

        # Save button
        def save_system_defaults() -> None:
            if current_user is None or current_user.id is None:
                ui.notify("Nicht authentifiziert", type="negative")
                return

            item_type_val = int(item_type_input.value) if item_type_input.value else DEFAULT_ITEM_TYPE_TIME_WINDOW
            category_val = int(category_input.value) if category_input.value else DEFAULT_CATEGORY_TIME_WINDOW
            location_val = int(location_input.value) if location_input.value else DEFAULT_LOCATION_TIME_WINDOW

            with Session(get_engine()) as session:
                preferences_service.set_system_setting(
                    session, "item_type_time_window", str(item_type_val), current_user.id
                )
                preferences_service.set_system_setting(
                    session, "category_time_window", str(category_val), current_user.id
                )
                preferences_service.set_system_setting(
                    session, "location_time_window", str(location_val), current_user.id
                )

            ui.notify("System-Standardwerte gespeichert", type="positive")

        ui.button("Speichern", icon="save", on_click=save_system_defaults).classes("sp-btn-primary")
