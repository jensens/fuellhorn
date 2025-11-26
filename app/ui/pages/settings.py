"""Settings Page - Übersicht und Navigation zu Admin-Bereichen.

Based on Issue #79: Settings Page aufteilen - Navigation zu Admin-Bereichen.
Issue #34: Smart Default Zeitfenster konfigurieren.
"""

from ...auth import Permission
from ...auth import require_permissions
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from nicegui import app
from nicegui import ui


# Default time windows in minutes
DEFAULT_ITEM_TYPE_TIME_WINDOW = 30
DEFAULT_CATEGORY_TIME_WINDOW = 30
DEFAULT_LOCATION_TIME_WINDOW = 60


@ui.page("/admin/settings")
@require_permissions(Permission.CONFIG_MANAGE)
def settings() -> None:
    """Settings page with admin navigation and smart defaults (Admin only)."""
    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/dashboard")).props("flat round color=gray-7")
            ui.label("Einstellungen").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Admin Navigation section
        _render_admin_navigation()

        # Separator
        ui.separator().classes("my-4")

        # Smart Default Settings section (Issue #34)
        _render_smart_defaults_section()

    # Bottom Navigation
    create_bottom_nav(current_page="settings")


def _render_admin_navigation() -> None:
    """Render navigation links to admin areas."""
    ui.label("Verwaltung").classes("text-h6 font-semibold mb-3")

    # Navigation cards
    nav_items = [
        {"icon": "category", "label": "Kategorien", "route": "/admin/categories"},
        {"icon": "place", "label": "Lagerorte", "route": "/admin/locations"},
        {"icon": "people", "label": "Benutzer", "route": "/admin/users"},
        {"icon": "ac_unit", "label": "Gefrierzeiten", "route": "/admin/freeze-times"},
    ]

    for item in nav_items:
        with (
            ui.card()
            .classes("w-full mb-2 cursor-pointer hover:bg-gray-50")
            .on("click", lambda r=item["route"]: ui.navigate.to(r))
        ):
            with ui.row().classes("w-full items-center justify-between p-2"):
                with ui.row().classes("items-center gap-3"):
                    ui.icon(item["icon"]).classes("text-primary")
                    ui.label(item["label"]).classes("font-medium")
                ui.icon("chevron_right").classes("text-gray-400")


def _get_preferences() -> dict:
    """Get preferences from browser storage with defaults."""
    preferences = app.storage.browser.get("preferences", {})
    return {
        "item_type_time_window": preferences.get("item_type_time_window", DEFAULT_ITEM_TYPE_TIME_WINDOW),
        "category_time_window": preferences.get("category_time_window", DEFAULT_CATEGORY_TIME_WINDOW),
        "location_time_window": preferences.get("location_time_window", DEFAULT_LOCATION_TIME_WINDOW),
    }


def _save_preferences(item_type_window: int, category_window: int, location_window: int) -> None:
    """Save preferences to browser storage."""
    preferences = app.storage.browser.get("preferences", {})
    preferences["item_type_time_window"] = item_type_window
    preferences["category_time_window"] = category_window
    preferences["location_time_window"] = location_window
    app.storage.browser["preferences"] = preferences
    ui.notify("Einstellungen gespeichert", type="positive")


def _render_smart_defaults_section() -> None:
    """Render the Smart Default settings section (Issue #34)."""
    preferences = _get_preferences()

    ui.label("Smart Default Einstellungen").classes("text-h6 font-semibold mb-3")

    with ui.card().classes("w-full p-4"):
        ui.label("Zeitfenster für automatische Vorbelegung").classes("text-body2 text-gray-600 mb-3")

        # Item type time window
        item_type_input = ui.number(
            label="Artikel-Typ Zeitfenster (Minuten)",
            value=preferences["item_type_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-2")

        # Category time window
        category_input = ui.number(
            label="Kategorie Zeitfenster (Minuten)",
            value=preferences["category_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-2")

        # Location time window
        location_input = ui.number(
            label="Lagerort Zeitfenster (Minuten)",
            value=preferences["location_time_window"],
            min=1,
            max=120,
        ).classes("w-full mb-4")

        # Save button
        def save_settings() -> None:
            item_type_val = int(item_type_input.value) if item_type_input.value else DEFAULT_ITEM_TYPE_TIME_WINDOW
            category_val = int(category_input.value) if category_input.value else DEFAULT_CATEGORY_TIME_WINDOW
            location_val = int(location_input.value) if location_input.value else DEFAULT_LOCATION_TIME_WINDOW
            _save_preferences(item_type_val, category_val, location_val)

        ui.button("Speichern", icon="save", on_click=save_settings).props("color=primary")
