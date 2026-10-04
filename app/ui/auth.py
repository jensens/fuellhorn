"""Authentication UI - Login/Logout."""

from ..auth.session import end_session
from ..auth.session import start_session
from ..config import config
from ..database import get_session
from ..services import rate_limit_service
from ..services.auth_service import AuthenticationError
from ..services.auth_service import authenticate_user
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


DEFAULT_AFTER_LOGIN = "/dashboard"


def safe_redirect_target(target: str | None) -> str:
    """Nur relative Pfade innerhalb der App; alles andere führt zum Dashboard (kein Open Redirect, #402)."""
    if not target or not target.startswith("/") or target.startswith("//") or "://" in target or "\\" in target:
        return DEFAULT_AFTER_LOGIN
    if target == "/login" or target.startswith("/login?"):
        return DEFAULT_AFTER_LOGIN
    return target


def show_login_page(next_url: str | None = None) -> None:
    """Zeigt die Login-Seite mit mobile-first Design; nach dem Login geht es zu ``next_url``."""
    redirect_target = safe_redirect_target(next_url)

    async def handle_login() -> None:
        """Login-Handler mit Remember-Me Support und Rate-Limiting."""
        username_val = (username_input.value or "").strip()
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

                # Sitzung beginnen (Issue #384): nur essenzielle Daten, Permissions kommen
                # bei Bedarf aus der DB; remember_me hebt die Inaktivitätsgrenze auf
                start_session(user, remember_me=bool(remember_me))

                ui.notify(f"Willkommen {user.username}!", type="positive")
                ui.navigate.to(redirect_target)

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

    # Grund einer erzwungenen Abmeldung anzeigen (Sitzung abgelaufen, Passwort geändert; #384).
    # Lokaler Import: app.ui.components importiert seinerseits logout() aus diesem Modul.
    from .components.flash import show_flash

    show_flash()

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
    """Logout: Sitzung leeren und zur Login-Seite."""
    end_session()

    ui.notify("Erfolgreich abgemeldet", type="positive")
    ui.navigate.to("/login")
