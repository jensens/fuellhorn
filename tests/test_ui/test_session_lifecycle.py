"""UI-Tests für Session-Dauer, Remember-Me und Abmelden anderer Sitzungen (Issue #384)."""

from app.services.auth_service import get_user_by_username
from app.services.auth_service import update_user
from collections.abc import Callable
from nicegui.testing import User as TestUser
import pytest
from sqlmodel import Session


DASHBOARD_MARKER = "Auf einen Blick"
ADMIN_PASSWORD = "password123"


@pytest.fixture(autouse=True)
def _restore_admin_password(isolated_test_database):
    """Die Test-DB ist modulweit; ein geändertes Admin-Passwort darf nicht in den nächsten Test lecken."""
    yield
    with Session(isolated_test_database) as session:
        admin = get_user_by_username(session, "admin")
        if admin is not None and not admin.check_password(ADMIN_PASSWORD):
            admin.set_password(ADMIN_PASSWORD)
            session.add(admin)
            session.commit()


async def _login(user: TestUser, *, remember_me: bool = False) -> None:
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type(ADMIN_PASSWORD)
    if remember_me:
        user.find("Angemeldet bleiben").click()
    user.find("Anmelden").click()
    await user.should_see("Willkommen admin")


async def test_password_change_logs_out_other_session(
    create_user: Callable[[], TestUser], isolated_test_database
) -> None:
    """Akzeptanzkriterium: Passwortänderung → andere Session ist beim nächsten Request abgemeldet."""
    phone, laptop = create_user(), create_user()
    await phone.open("/test-login-admin")
    await laptop.open("/test-login-admin")

    with Session(isolated_test_database) as session:
        admin = get_user_by_username(session, "admin")
        assert admin is not None and admin.id is not None
        update_user(session, admin.id, password="ganz-neues-passwort")

    await laptop.open("/dashboard")
    await laptop.should_see("Anmelden")
    await laptop.should_see("Passwort wurde geändert")


async def test_own_session_survives_own_password_change(logged_in_user: TestUser) -> None:
    """Wer sein Passwort selbst ändert, bleibt angemeldet."""
    await logged_in_user.open("/profile")
    logged_in_user.find("Aktuelles Passwort").type(ADMIN_PASSWORD)
    logged_in_user.find("Neues Passwort").type("mein-neues-passwort")
    logged_in_user.find("Passwort bestätigen").type("mein-neues-passwort")
    logged_in_user.find("Passwort ändern").click()
    await logged_in_user.should_see("Passwort erfolgreich geändert")

    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see(DASHBOARD_MARKER)


async def test_inactive_session_expires(user: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ohne 'Angemeldet bleiben' endet die Sitzung nach SESSION_MAX_AGE ohne Aktivität."""
    import app.config

    await _login(user)
    monkeypatch.setattr(app.config.config, "SESSION_MAX_AGE", 0)

    await user.open("/dashboard")
    await user.should_see("Anmelden")
    await user.should_see("Sitzung abgelaufen")


async def test_remember_me_session_outlives_session_max_age(user: TestUser, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mit 'Angemeldet bleiben' gilt die Inaktivitätsgrenze nicht (Cookie-Laufzeit: REMEMBER_ME_MAX_AGE)."""
    import app.config

    await _login(user, remember_me=True)
    monkeypatch.setattr(app.config.config, "SESSION_MAX_AGE", 0)

    await user.open("/dashboard")
    await user.should_see(DASHBOARD_MARKER)
