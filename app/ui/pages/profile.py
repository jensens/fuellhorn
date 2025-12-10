"""Profile Page - User profile settings.

Based on Issue #85: Profil-Seite für User (Passwort ändern, Smart Defaults)
- Password change (with current password verification)
- Email change (username stays fixed)
- Smart default time window settings (stored per user in DB)
"""

from ...auth import get_current_user
from ...auth import require_auth
from ...database import get_engine
from ...models.user import User
from ...services import preferences_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..theme.icons import create_icon
from nicegui import ui
from sqlmodel import Session
from typing import Any


# Default time windows in minutes
DEFAULT_ITEM_TYPE_TIME_WINDOW = 30
DEFAULT_CATEGORY_TIME_WINDOW = 30
DEFAULT_LOCATION_TIME_WINDOW = 60


@ui.page("/profile")
@require_auth
def profile() -> None:
    """Profile page for all authenticated users."""
    current_user = get_current_user(require_auth=True)

    # This should not happen due to @require_auth decorator, but needed for type safety
    if current_user is None:
        ui.navigate.to("/login")
        return

    # Header (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with ui.button(on_click=lambda: ui.navigate.to("/dashboard")).classes("sp-back-btn").props("flat round"):
                create_icon("actions/back", size="24px")
            ui.label("Profil").classes("sp-page-title")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Account Info section
        _render_account_info_section(current_user)

        # Separator
        ui.separator().classes("my-4")

        # Password change section
        _render_password_change_section(current_user)

        # Separator
        ui.separator().classes("my-4")

        # Smart Defaults section
        _render_smart_defaults_section(current_user)

    # Bottom Navigation (no item active - accessed via user dropdown)
    create_bottom_nav(current_page="")


def _render_account_info_section(current_user: User) -> None:
    """Render account info section with email and username (Solarpunk theme)."""
    ui.label("Konto-Informationen").classes("text-h6 font-semibold mb-3 text-fern")

    with ui.card().classes("sp-dashboard-card w-full p-4"):
        # Username (readonly)
        ui.input(
            label="Benutzername",
            value=current_user.username,
        ).props("readonly outlined").classes("w-full mb-3")

        # Email (editable)
        email_input = (
            ui.input(
                label="E-Mail",
                value=current_user.email,
            )
            .props("outlined")
            .classes("w-full mb-4")
        )

        def save_email() -> None:
            new_email = email_input.value
            if not new_email:
                ui.notify("E-Mail-Adresse darf nicht leer sein", type="negative")
                return

            try:
                with Session(get_engine()) as session:
                    # Re-fetch user to get fresh data
                    user = session.get(type(current_user), current_user.id)
                    if user:
                        preferences_service.change_user_email(
                            session=session,
                            user=user,
                            new_email=new_email,
                        )
                        ui.notify("E-Mail-Adresse geändert", type="positive")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        with ui.button(on_click=save_email).classes("sp-btn-primary"):
            with ui.row().classes("items-center gap-2"):
                create_icon("actions/save", size="20px")
                ui.label("E-Mail speichern")


def _render_password_change_section(current_user: User) -> None:
    """Render password change section (Solarpunk theme)."""
    ui.label("Passwort ändern").classes("text-h6 font-semibold mb-3 text-fern")

    with ui.card().classes("sp-dashboard-card w-full p-4"):
        # Current password
        current_pw_input = (
            ui.input(
                label="Aktuelles Passwort",
                password=True,
                password_toggle_button=True,
            )
            .props("outlined")
            .classes("w-full mb-2")
        )

        # New password
        new_pw_input = (
            ui.input(
                label="Neues Passwort",
                password=True,
                password_toggle_button=True,
            )
            .props("outlined")
            .classes("w-full mb-2")
        )

        # Confirm password
        confirm_pw_input = (
            ui.input(
                label="Passwort bestätigen",
                password=True,
                password_toggle_button=True,
            )
            .props("outlined")
            .classes("w-full mb-4")
        )

        def change_password() -> None:
            current_pw = current_pw_input.value
            new_pw = new_pw_input.value
            confirm_pw = confirm_pw_input.value

            # Validation
            if not current_pw:
                ui.notify("Bitte aktuelles Passwort eingeben", type="negative")
                return

            if not new_pw:
                ui.notify("Bitte neues Passwort eingeben", type="negative")
                return

            if new_pw != confirm_pw:
                ui.notify("Passwörter stimmen nicht überein", type="negative")
                return

            try:
                with Session(get_engine()) as session:
                    # Re-fetch user to get fresh data
                    user = session.get(type(current_user), current_user.id)
                    if user:
                        success = preferences_service.change_user_password(
                            session=session,
                            user=user,
                            current_password=current_pw,
                            new_password=new_pw,
                        )
                        if success:
                            ui.notify("Passwort erfolgreich geändert", type="positive")
                            # Clear fields
                            current_pw_input.value = ""
                            new_pw_input.value = ""
                            confirm_pw_input.value = ""
                        else:
                            ui.notify("Aktuelles Passwort ist falsch", type="negative")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        ui.button("Passwort ändern", icon="lock", on_click=change_password).classes("sp-btn-primary")


def _get_user_preferences(current_user: User) -> dict[str, Any]:
    """Get preferences for current user with defaults."""
    with Session(get_engine()) as session:
        # Re-fetch user to get fresh data
        user = session.get(type(current_user), current_user.id)
        if user:
            return preferences_service.get_all_user_preferences(session, user)
    return {
        "item_type_time_window": DEFAULT_ITEM_TYPE_TIME_WINDOW,
        "category_time_window": DEFAULT_CATEGORY_TIME_WINDOW,
        "location_time_window": DEFAULT_LOCATION_TIME_WINDOW,
    }


def _render_smart_defaults_section(current_user: User) -> None:
    """Render the Smart Default settings section (Solarpunk theme)."""
    preferences = _get_user_preferences(current_user)

    ui.label("Smart Default Einstellungen").classes("text-h6 font-semibold mb-3 text-fern")

    with ui.card().classes("sp-dashboard-card w-full p-4"):
        ui.label("Zeitfenster für automatische Vorbelegung").classes("text-body2 text-charcoal mb-3")
        ui.label(
            "Wenn Sie innerhalb des Zeitfensters einen weiteren Artikel erfassen, "
            "werden die entsprechenden Werte automatisch vorbelegt."
        ).classes("text-caption text-stone mb-4")

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

        def save_preferences() -> None:
            item_type_val = int(item_type_input.value) if item_type_input.value else DEFAULT_ITEM_TYPE_TIME_WINDOW
            category_val = int(category_input.value) if category_input.value else DEFAULT_CATEGORY_TIME_WINDOW
            location_val = int(location_input.value) if location_input.value else DEFAULT_LOCATION_TIME_WINDOW

            with Session(get_engine()) as session:
                # Re-fetch user to get fresh data
                user = session.get(type(current_user), current_user.id)
                if user:
                    preferences_service.set_user_preference(session, user, "item_type_time_window", item_type_val)
                    preferences_service.set_user_preference(session, user, "category_time_window", category_val)
                    preferences_service.set_user_preference(session, user, "location_time_window", location_val)

            ui.notify("Einstellungen gespeichert", type="positive")

        with ui.button(on_click=save_preferences).classes("sp-btn-primary"):
            with ui.row().classes("items-center gap-2"):
                create_icon("actions/save", size="20px")
                ui.label("Speichern")
