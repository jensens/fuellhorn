"""Authentication UI - Login/Logout."""

from ..database import get_session
from ..services.auth_service import AuthenticationError
from ..services.auth_service import authenticate_user
from ..services.auth_service import generate_remember_token
from ..services.auth_service import get_user
from ..services.auth_service import revoke_remember_token
from nicegui import app
from nicegui import ui


def show_login_page() -> None:
    """Zeigt die Login-Seite mit mobile-first Design."""

    async def handle_login() -> None:
        """Login-Handler mit Remember-Me Support."""
        username_val = username_input.value
        password_val = password_input.value
        remember_me = remember_checkbox.value

        if not username_val or not password_val:
            ui.notify("Bitte Username und Passwort eingeben", type="warning")
            return

        with next(get_session()) as session:
            try:
                user = authenticate_user(session, username_val, password_val)

                # Session speichern (nur essenzielle Daten, Permissions werden bei Bedarf aus DB geholt)
                app.storage.user["authenticated"] = True
                app.storage.user["user_id"] = user.id
                app.storage.user["username"] = user.username

                # Remember-Me Token generieren wenn gewuenscht
                if remember_me:
                    token = generate_remember_token(session, user)
                    app.storage.user["remember_token"] = token
                    # Laengere Session-Lifetime fuer Remember-Me
                    # (wird in config.py definiert: REMEMBER_ME_MAX_AGE = 30 Tage)

                ui.notify(f"Willkommen {user.username}!", type="positive")
                ui.navigate.to("/dashboard")

            except AuthenticationError as e:
                ui.notify(str(e), type="negative")

    # Mobile-First Layout: Full-screen auf Mobile, zentrierte Card auf Desktop
    with ui.column().classes("w-full min-h-screen items-center justify-center bg-gray-100 p-4"):
        # Responsive Card: full width auf Mobile, max-w-md auf Desktop
        with ui.card().classes("w-full max-w-md"):
            # Logo Placeholder (wird spaeter durch echtes Logo ersetzt)
            with ui.row().classes("w-full justify-center mb-4"):
                ui.icon("kitchen", size="64px").classes("text-primary")

            # Titel
            ui.label("Füllhorn").classes("text-h4 text-center w-full mb-2")
            ui.label("Lebensmittelvorrats-Verwaltung").classes("text-subtitle2 text-center w-full mb-6 text-gray-600")

            # Formular
            with ui.column().classes("w-full gap-4"):
                username_input = ui.input("Benutzername", placeholder="Username").classes("w-full").props("outlined")

                password_input = (
                    ui.input(
                        "Passwort",
                        placeholder="Passwort",
                        password=True,
                        password_toggle_button=True,
                    )
                    .classes("w-full")
                    .props("outlined")
                )

                # Remember-Me Checkbox
                remember_checkbox = ui.checkbox("Angemeldet bleiben (30 Tage)").classes("mb-2")

                # Enter-Taste fuer Submit
                password_input.on("keydown.enter", handle_login)

                # Login Button - groesser fuer Touch (min 48px)
                ui.button("Anmelden", on_click=handle_login).props("color=primary size=lg").classes(
                    "w-full mt-4"
                ).style("min-height: 48px")


def logout() -> None:
    """Logout und Session loeschen.

    Fuehrt folgende Schritte aus:
    1. Remember-Token in DB invalidieren (falls vorhanden)
    2. app.storage.user leeren
    3. Redirect zur Login-Seite
    """
    # Remember-Token in DB invalidieren wenn User eingeloggt ist
    user_id = app.storage.user.get("user_id")
    if user_id:
        try:
            with next(get_session()) as session:
                user = get_user(session, user_id)
                if user.remember_token:
                    revoke_remember_token(session, user)
        except Exception:
            # Fehler beim Token-Revoke ignorieren - Session wird trotzdem geloescht
            pass

    # Session vollstaendig leeren
    app.storage.user.clear()

    ui.notify("Erfolgreich abgemeldet", type="positive")
    ui.navigate.to("/login")
