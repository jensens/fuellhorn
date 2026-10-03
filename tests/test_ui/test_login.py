"""UI Tests for Login functionality."""

from app.models import LoginAttempt
from datetime import datetime
from nicegui.testing import User as TestUser
from sqlmodel import Session
from sqlmodel import select


async def _submit_login(user: TestUser, username: str, password: str) -> None:
    await user.open("/login")
    user.find("Benutzername").type(username)
    user.find("Passwort").type(password)
    user.find("Anmelden").click()


# =============================================================================
# Issue #364: Rate-Limiting pro Client-IP (vorher ein globaler Zähler "test")
# =============================================================================


async def test_failed_login_records_attempt_for_real_client_ip(user: TestUser, isolated_test_database) -> None:
    """Ein Fehlversuch wird unter der echten Client-IP gezählt, nicht unter dem Platzhalter 'test'."""
    await _submit_login(user, "admin", "falsches-passwort")
    await user.should_see("Username oder Passwort falsch")

    with Session(isolated_test_database) as session:
        attempts = session.exec(select(LoginAttempt)).all()
    assert [a.ip_address for a in attempts] == ["127.0.0.1"]


async def test_other_clients_failures_do_not_block_this_client(user: TestUser, isolated_test_database) -> None:
    """Fehlversuche einer anderen IP (früher: der globale Zähler) sperren diesen Client nicht."""
    with Session(isolated_test_database) as session:
        session.add(LoginAttempt(ip_address="test", fail_count=6, last_attempt=datetime.now()))
        session.add(LoginAttempt(ip_address="203.0.113.9", fail_count=6, last_attempt=datetime.now()))
        session.commit()

    await _submit_login(user, "admin", "password123")
    await user.should_see("Willkommen admin")


async def test_login_is_blocked_after_failures_from_this_client(user: TestUser, isolated_test_database) -> None:
    """Nach mehreren Fehlversuchen derselben Client-IP erscheint die Wartezeit-Meldung."""
    with Session(isolated_test_database) as session:
        session.add(LoginAttempt(ip_address="127.0.0.1", fail_count=6, last_attempt=datetime.now()))
        session.commit()

    await _submit_login(user, "admin", "password123")
    await user.should_see("Zu viele Fehlversuche")


async def test_login_page_has_all_elements(user: TestUser) -> None:
    """Test that login page renders all required elements."""
    await user.open("/login")

    # Branding
    await user.should_see("Füllhorn")
    await user.should_see("Lebensmittelvorrats-Verwaltung")

    # Form elements
    await user.should_see("Benutzername")
    await user.should_see("Passwort")
    await user.should_see("Anmelden")
    await user.should_see("Angemeldet bleiben")


async def test_login_input_fields_have_no_placeholder_text(user: TestUser) -> None:
    """Test that input fields use labels only, not duplicate placeholders.

    Issue #254: Labels and placeholders were overlapping. The fix removes
    placeholders - labels alone are sufficient for outlined inputs.
    """
    await user.open("/login")

    # Should NOT see the old placeholder texts that caused overlap
    await user.should_not_see("Username")
    await user.should_not_see("Password")


async def test_root_redirects_to_login_when_not_authenticated(user: TestUser) -> None:
    """Test that / redirects to /login when not authenticated."""
    await user.open("/")
    # Should redirect to login page
    await user.should_see("Füllhorn")
    await user.should_see("Anmelden")


async def test_root_redirects_to_dashboard_when_authenticated(logged_in_user: TestUser) -> None:
    """Test that / redirects to /dashboard when authenticated."""
    await logged_in_user.open("/")
    # Should redirect to dashboard
    await logged_in_user.should_see("Bald ablaufend")
    await logged_in_user.should_see("Auf einen Blick")  # Issue #245
