"""Users Page - Admin page for managing users (Mobile-First).

Based on Issue #28: Users Page - Liste aller Benutzer
Issue #29: Users Page - Benutzer erstellen
Issue #30: Users Page - Benutzer bearbeiten
Issue #31: Users Page - Benutzer löschen
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.user import Role
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
        # Section header with "Neuer Benutzer" button
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Benutzer verwalten").classes("text-h6 font-semibold")
            ui.button("Neuer Benutzer", icon="add", on_click=_open_create_dialog).props("color=primary size=sm")

        _render_users_list()


def _render_users_list() -> None:
    """Render the list of users."""
    # Get current user to prevent self-deletion
    current_user = get_current_user(require_auth=True)
    current_user_id = current_user.id if current_user else None

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

                        # Right side: status, last login, and edit button
                        with ui.row().classes("items-center gap-2"):
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

                            # Edit button - capture user data for the closure
                            user_id = user.id
                            username = user.username
                            email = user.email
                            role = user.role
                            is_active = user.is_active
                            ui.button(
                                icon="edit",
                                on_click=lambda uid=user_id,
                                un=username,
                                em=email,
                                ro=role,
                                ia=is_active: _open_edit_dialog(uid, un, em, ro, ia),
                            ).props("flat round color=grey-7 size=sm").mark(f"edit-{username}")

                            # Delete button - only if not current user
                            if user_id != current_user_id:
                                ui.button(
                                    icon="delete",
                                    on_click=lambda uid=user_id, un=username: _open_delete_dialog(uid, un),
                                ).props("flat round color=red-7 size=sm").mark(f"delete-{username}")
        else:
            # Empty state (shouldn't happen since there's always at least one admin)
            with ui.card().classes("w-full"):
                with ui.column().classes("w-full items-center py-8"):
                    ui.icon("person_off", size="48px").classes("text-gray-400 mb-2")
                    ui.label("Keine Benutzer vorhanden").classes("text-gray-600 text-center")


def _open_create_dialog() -> None:
    """Open dialog to create a new user."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Neuen Benutzer erstellen").classes("text-h6 font-semibold mb-4")

        # Username input (required)
        username_input = (
            ui.input(label="Benutzername", placeholder="z.B. maxmuster").classes("w-full mb-2").props("outlined")
        )

        # Email input (required)
        email_input = (
            ui.input(label="E-Mail", placeholder="z.B. max@example.com").classes("w-full mb-2").props("outlined")
        )

        # Password input (required)
        password_input = (
            ui.input(label="Passwort", password=True, password_toggle_button=True)
            .classes("w-full mb-2")
            .props("outlined")
            .mark("password-input")
        )

        # Password confirmation input (required)
        password_confirm_input = (
            ui.input(label="Wiederholung", password=True, password_toggle_button=True)
            .classes("w-full mb-2")
            .props("outlined")
            .mark("password-confirm-input")
        )

        # Role selection
        role_options = {Role.USER.value: "Benutzer", Role.ADMIN.value: "Admin"}
        role_select = (
            ui.select(
                label="Rolle",
                options=role_options,
                value=Role.USER.value,
            )
            .classes("w-full mb-4")
            .props("outlined")
        )

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_user() -> None:
                """Validate and save the new user."""
                username = username_input.value.strip() if username_input.value else ""
                email = email_input.value.strip() if email_input.value else ""
                password = password_input.value if password_input.value else ""
                password_confirm = password_confirm_input.value if password_confirm_input.value else ""
                role_value = role_select.value

                # Validation: username is required
                if not username:
                    error_label.set_text("Benutzername ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Validation: email is required
                if not email:
                    error_label.set_text("E-Mail ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Validation: password is required
                if not password:
                    error_label.set_text("Passwort ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Validation: passwords must match
                if password != password_confirm:
                    error_label.set_text("Passwörter stimmen nicht überein")
                    error_label.set_visibility(True)
                    return

                # Map role value to Role enum
                role = Role.ADMIN if role_value == Role.ADMIN.value else Role.USER

                try:
                    with next(get_session()) as session:
                        auth_service.create_user(
                            session=session,
                            username=username,
                            email=email,
                            password=password,
                            role=role,
                        )
                    ui.notify(f"Benutzer '{username}' erstellt", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/users")
                except Exception as e:
                    # Handle duplicate username/email error
                    error_msg = str(e)
                    if "UNIQUE constraint" in error_msg:
                        if "username" in error_msg.lower():
                            error_label.set_text(f"Benutzername '{username}' bereits vorhanden")
                        elif "email" in error_msg.lower():
                            error_label.set_text(f"E-Mail '{email}' bereits vorhanden")
                        else:
                            error_label.set_text("Benutzer bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_user).props("color=primary")

    dialog.open()


def _open_edit_dialog(
    user_id: int,
    current_username: str,
    current_email: str,
    current_role: str,
    current_is_active: bool,
) -> None:
    """Open dialog to edit an existing user."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Benutzer bearbeiten").classes("text-h6 font-semibold mb-4")

        # Username input (pre-filled)
        username_input = (
            ui.input(label="Benutzername", value=current_username)
            .classes("w-full mb-2")
            .props("outlined")
            .mark("edit-username")
        )

        # Email input (pre-filled)
        email_input = (
            ui.input(label="E-Mail", value=current_email).classes("w-full mb-2").props("outlined").mark("edit-email")
        )

        # Role selection (pre-filled)
        role_options = {Role.USER.value: "Benutzer", Role.ADMIN.value: "Admin"}
        role_select = (
            ui.select(
                label="Rolle",
                options=role_options,
                value=current_role,
            )
            .classes("w-full mb-2")
            .props("outlined")
            .mark("edit-role")
        )

        # Active status toggle
        is_active_switch = ui.switch("Aktiv", value=current_is_active).classes("mb-4").mark("edit-is-active")

        # Password change section (optional)
        ui.label("Passwort ändern (optional)").classes("text-sm text-gray-600 mb-2")

        password_input = (
            ui.input(label="Neues Passwort", password=True, password_toggle_button=True)
            .classes("w-full mb-2")
            .props("outlined")
            .mark("edit-password")
        )

        password_confirm_input = (
            ui.input(label="Passwort bestätigen", password=True, password_toggle_button=True)
            .classes("w-full mb-4")
            .props("outlined")
            .mark("edit-password-confirm")
        )

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_changes() -> None:
                """Validate and save the user changes."""
                username = username_input.value.strip() if username_input.value else ""
                email = email_input.value.strip() if email_input.value else ""
                role_value = role_select.value
                is_active = is_active_switch.value
                password = password_input.value if password_input.value else ""
                password_confirm = password_confirm_input.value if password_confirm_input.value else ""

                # Validation: username is required
                if not username:
                    error_label.set_text("Benutzername ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Validation: email is required
                if not email:
                    error_label.set_text("E-Mail ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Validation: if password provided, confirmation must match
                if password and password != password_confirm:
                    error_label.set_text("Passwörter stimmen nicht überein")
                    error_label.set_visibility(True)
                    return

                # Map role value to Role enum
                role = Role.ADMIN if role_value == Role.ADMIN.value else Role.USER

                try:
                    with next(get_session()) as session:
                        auth_service.update_user(
                            session=session,
                            user_id=user_id,
                            username=username if username != current_username else None,
                            email=email if email != current_email else None,
                            password=password if password else None,
                            role=role if role_value != current_role else None,
                            is_active=is_active if is_active != current_is_active else None,
                        )
                    ui.notify(f"Benutzer '{username}' aktualisiert", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/users")
                except Exception as e:
                    # Handle duplicate username/email error
                    error_msg = str(e)
                    if "UNIQUE constraint" in error_msg:
                        if "username" in error_msg.lower():
                            error_label.set_text(f"Benutzername '{username}' bereits vorhanden")
                        elif "email" in error_msg.lower():
                            error_label.set_text(f"E-Mail '{email}' bereits vorhanden")
                        else:
                            error_label.set_text("Benutzer bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_changes).props("color=primary")

    dialog.open()


def _open_delete_dialog(user_id: int, username: str) -> None:
    """Open confirmation dialog to delete a user."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Benutzer löschen").classes("text-h6 font-semibold mb-4")

        # Warning message
        ui.label(f"Möchten Sie den Benutzer '{username}' wirklich löschen?").classes("mb-2")
        ui.label("Diese Aktion kann nicht rückgängig gemacht werden.").classes("text-sm text-red-600 mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def confirm_delete() -> None:
                """Perform the deletion."""
                try:
                    with next(get_session()) as session:
                        auth_service.delete_user(session=session, user_id=user_id)
                    ui.notify("Benutzer gelöscht", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/users")
                except Exception as e:
                    error_label.set_text(str(e))
                    error_label.set_visibility(True)

            ui.button("Löschen", on_click=confirm_delete).props("color=red")

    dialog.open()
