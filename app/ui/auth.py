"""Authentication UI - Login/Logout."""

from ..config import config
from ..database import get_session
from ..services import rate_limit_service
from ..services.auth_service import AuthenticationError
from ..services.auth_service import authenticate_user
from ..services.auth_service import generate_remember_token
from ..services.auth_service import get_user
from ..services.auth_service import revoke_remember_token
from nicegui import app
from nicegui import context
from nicegui import ui


UNKNOWN_CLIENT_IP = "unknown"


def resolve_client_ip(peer_ip: str | None, forwarded_for: str | None, trusted_proxies: frozenset[str]) -> str:
    """Bestimmt die Client-IP für das Rate-Limiting (reine Funktion, Issue #364).

    X-Forwarded-For ist frei setzbar und zählt deshalb nur, wenn der direkte Peer
    ein konfigurierter Proxy ist; dann gilt der erste Eintrag der Kette.

    Args:
        peer_ip: IP der direkten TCP-Gegenstelle (``request.client.host``).
        forwarded_for: Wert des X-Forwarded-For-Headers oder None.
        trusted_proxies: IPs vertrauenswürdiger Reverse-Proxys (``config.TRUSTED_PROXIES``).

    Returns:
        IP-Adresse als String, ``"unknown"`` wenn keine Peer-Information vorliegt.
    """
    if not peer_ip:
        return UNKNOWN_CLIENT_IP
    if forwarded_for and peer_ip in trusted_proxies:
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop
    return peer_ip


def _get_client_ip() -> str:
    """Ermittelt die Client-IP des aktuellen NiceGUI-Clients.

    Nutzt den Request des Clients (``context.client.request``); ohne Client-Kontext
    (sollte in UI-Handlern nicht vorkommen) wird ``"unknown"`` verwendet.
    """
    try:
        request = context.client.request
    except RuntimeError:
        return UNKNOWN_CLIENT_IP
    peer_ip = request.client.host if request.client is not None else None
    return resolve_client_ip(peer_ip, request.headers.get("x-forwarded-for"), config.TRUSTED_PROXIES)


def show_login_page() -> None:
    """Zeigt die Login-Seite mit mobile-first Design."""

    async def handle_login() -> None:
        """Login-Handler mit Remember-Me Support und Rate-Limiting."""
        username_val = username_input.value
        password_val = password_input.value
        remember_me = remember_checkbox.value

        if not username_val or not password_val:
            ui.notify("Bitte Username und Passwort eingeben", type="warning")
            return

        client_ip = _get_client_ip()

        with next(get_session()) as session:
            # Rate-Limiting prüfen (IP-basiert)
            required_delay = rate_limit_service.get_required_delay(session, client_ip)
            if required_delay > 0:
                ui.notify(
                    f"Zu viele Fehlversuche. Bitte {required_delay} Sekunden warten.",
                    type="warning",
                )
                return

            try:
                user = authenticate_user(session, username_val, password_val)

                # Login erfolgreich - Rate-Limit zurücksetzen
                rate_limit_service.record_successful_login(session, client_ip)

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
                # Fehlversuch aufzeichnen
                fail_count = rate_limit_service.record_failed_attempt(session, client_ip)
                next_delay = rate_limit_service.get_delay_seconds(fail_count + 1)

                if next_delay > 0:
                    ui.notify(
                        f"{e} (Nächster Versuch: {next_delay}s Wartezeit)",
                        type="negative",
                    )
                else:
                    ui.notify(str(e), type="negative")

    # Mobile-First Layout: Full-screen auf Mobile, zentrierte Card auf Desktop (Solarpunk theme)
    with ui.column().classes("w-full min-h-screen items-center justify-center bg-cream p-4"):
        # Responsive Card: full width auf Mobile, max-w-md auf Desktop
        with ui.card().classes("sp-dashboard-card w-full max-w-md p-6"):
            # Logo Placeholder (wird spaeter durch echtes Logo ersetzt)
            with ui.row().classes("w-full justify-center mb-4"):
                ui.icon("kitchen", size="64px").classes("text-fern")

            # Titel (Solarpunk display font)
            ui.label("Füllhorn").classes("font-display text-h4 text-fern text-center w-full mb-2")
            ui.label("Lebensmittelvorrats-Verwaltung").classes("text-subtitle2 text-center w-full mb-6 text-stone")

            # Formular
            with ui.column().classes("w-full gap-4"):
                username_input = ui.input("Benutzername").classes("w-full").props("outlined")

                password_input = (
                    ui.input(
                        "Passwort",
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

                # Login Button - groesser fuer Touch (min 48px), Solarpunk primary button
                ui.button("Anmelden", on_click=handle_login).classes("w-full mt-4 sp-btn-primary").props(
                    "size=lg"
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
