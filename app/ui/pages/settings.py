"""Settings Page - Übersicht und Navigation zu Admin-Bereichen.

Based on Issue #79: Settings Page aufteilen - Navigation zu Admin-Bereichen.
Issue #34: Smart Default Zeitfenster konfigurieren.
Issue #85: System-Defaults in DB speichern (Fallback für User ohne eigene Einstellungen).
"""

from ...auth import Permission
from ...auth import get_current_user
from ...auth import require_permissions
from ...auth import with_permission_check
from ...database import get_engine
from ...services import preferences_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..components.errors import show_service_error
from ..theme.icons import create_icon
from nicegui import ui
from sqlmodel import Session


# Eine Quelle für Fallback-Werte: preferences_service.HARDCODED_DEFAULTS (Issue #397)
DEFAULTS = preferences_service.HARDCODED_DEFAULTS


@ui.page("/admin/settings")
@require_permissions(Permission.CONFIG_MANAGE)
def settings() -> None:
    """Settings page with admin navigation and system defaults (Admin only)."""
    # Header (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with ui.button(on_click=lambda: ui.navigate.to("/dashboard")).classes("sp-back-btn").props("flat round"):
                create_icon("actions/back", size="24px")
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
    """System-Defaults aus der DB; Fallback sind die Hardcoded-Defaults des Services (#397)."""
    with Session(get_engine()) as session:
        return preferences_service.get_system_defaults(session)


def _render_system_defaults_section() -> None:
    """Render the System Default settings section (Issue #85) (Solarpunk theme).

    These are fallback values for users who haven't set their own preferences.
    """
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

        # Save button for time windows
        @with_permission_check(Permission.CONFIG_MANAGE)  # Nutzer zur Laufzeit, nicht aus der Build-Closure (#381)
        def save_system_defaults() -> None:
            acting_user = get_current_user(require_auth=True)
            if acting_user is None or acting_user.id is None:
                ui.notify("Nicht authentifiziert", type="negative")
                return

            item_type_val = int(item_type_input.value) if item_type_input.value else DEFAULTS["item_type_time_window"]
            category_val = int(category_input.value) if category_input.value else DEFAULTS["category_time_window"]
            location_val = int(location_input.value) if location_input.value else DEFAULTS["location_time_window"]

            try:
                with Session(get_engine()) as session:
                    # Ein Commit für alle Werte, Validierung im Service (#382)
                    preferences_service.set_system_settings(
                        session,
                        {
                            "item_type_time_window": str(item_type_val),
                            "category_time_window": str(category_val),
                            "location_time_window": str(location_val),
                        },
                        acting_user.id,
                    )
            except Exception as e:
                show_service_error(e)
                return

            ui.notify("System-Standardwerte gespeichert", type="positive")

        with ui.button(on_click=save_system_defaults).classes("sp-btn-primary"):
            with ui.row().classes("items-center gap-2"):
                create_icon("actions/save", size="20px")
                ui.label("Speichern")

    # Expiry thresholds section (Issue #135)
    ui.label("Ablauf-Schwellwerte").classes("text-h6 font-semibold mb-3 mt-6 text-fern")

    with ui.card().classes("sp-dashboard-card w-full p-4"):
        ui.label("Schwellwerte für Ablaufstatus").classes("text-body2 text-charcoal mb-2")
        ui.label(
            "Diese Werte bestimmen, ab wann Artikel als 'kritisch' (rot) oder 'Warnung' (gelb) "
            "angezeigt werden, basierend auf dem Ablaufdatum."
        ).classes("text-caption text-stone mb-4")

        # Critical days threshold
        critical_days_input = (
            ui.number(
                label="Kritisch (Tage vor Ablauf)",
                value=defaults["expiry_critical_days"],
                min=0,
                max=30,
            )
            .classes("w-full mb-2")
            .mark("expiry-critical-days")
        )

        # Warning days threshold
        warning_days_input = (
            ui.number(
                label="Warnung (Tage vor Ablauf)",
                value=defaults["expiry_warning_days"],
                min=0,
                max=90,
            )
            .classes("w-full mb-4")
            .mark("expiry-warning-days")
        )

        # Save button for expiry thresholds
        @with_permission_check(Permission.CONFIG_MANAGE)
        def save_expiry_thresholds() -> None:
            acting_user = get_current_user(require_auth=True)
            if acting_user is None or acting_user.id is None:
                ui.notify("Nicht authentifiziert", type="negative")
                return

            critical_val = (
                int(critical_days_input.value) if critical_days_input.value else DEFAULTS["expiry_critical_days"]
            )
            warning_val = int(warning_days_input.value) if warning_days_input.value else DEFAULTS["expiry_warning_days"]

            try:
                with Session(get_engine()) as session:
                    # Der Service verweigert Kritisch >= Warnung und schreibt beide Werte in einem Commit (#382)
                    preferences_service.set_system_settings(
                        session,
                        {"expiry_critical_days": str(critical_val), "expiry_warning_days": str(warning_val)},
                        acting_user.id,
                    )
            except Exception as e:
                show_service_error(e)
                return

            ui.notify("Ablauf-Schwellwerte gespeichert", type="positive")

        with ui.button(on_click=save_expiry_thresholds).classes("sp-btn-primary").mark("save-expiry-thresholds"):
            with ui.row().classes("items-center gap-2"):
                create_icon("actions/save", size="20px")
                ui.label("Speichern")
