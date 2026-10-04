"""Test-Route für den schnellen Admin-Login in UI-Tests (``logged_in_user``-Fixture).

Nur unter TESTING geladen. Vorher lag die Route in ``test_items_page.py`` neben 14
Harness-Routen, die kein Test öffnete (Issue #389).
"""

from ...auth.session import start_session
from ...database import get_engine
from ...services.auth_service import get_user_by_username
from nicegui import ui
from sqlmodel import Session


def _set_test_session() -> None:
    """Admin-Sitzung wie nach echtem Login beginnen (Issue #384)."""
    with Session(get_engine()) as session:
        admin = get_user_by_username(session, "admin")
        assert admin is not None, "Test-DB ohne admin"
        start_session(admin, remember_me=False)


@ui.page("/test-login-admin")
def page_test_login_admin(next: str = "") -> None:
    """Simuliert den Admin-Login; ``next`` leitet direkt auf eine Seite weiter."""
    _set_test_session()
    if next:
        ui.navigate.to(next)
    else:
        ui.label("Angemeldet als admin")
        ui.label("Willkommen")
