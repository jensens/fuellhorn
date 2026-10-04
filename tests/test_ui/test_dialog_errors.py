"""UI-Tests: Dialoge zeigen verständliche Meldungen, nie rohes SQL (Issue #382)."""

from nicegui.testing import User as TestUser
import pytest
from sqlalchemy.exc import IntegrityError


async def _open_new_user_dialog(user: TestUser, *, username: str, email: str) -> None:
    await user.open("/admin/users")
    user.find(marker="new-user-button").click()
    await user.should_see("Neuen Benutzer erstellen")
    user.find("Benutzername").type(username)
    user.find("E-Mail").type(email)
    user.find(marker="password-input").type("geheim-123")
    user.find(marker="password-confirm-input").type("geheim-123")


async def test_duplicate_email_names_the_email_field(logged_in_user: TestUser, standard_users) -> None:
    """Vorher traf das SQLite-Parsing 'username' auch bei E-Mail-Duplikaten (Spaltenname im SQL)."""
    await _open_new_user_dialog(logged_in_user, username="ganzneu", email="testuser1@example.com")
    logged_in_user.find("Speichern").click()

    await logged_in_user.should_see("E-Mail-Adresse 'testuser1@example.com' ist bereits vorhanden")
    await logged_in_user.should_not_see("Benutzername 'ganzneu'")


async def test_unexpected_database_error_shows_generic_message_without_sql(
    logged_in_user: TestUser, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def explode(*args, **kwargs):
        raise IntegrityError(
            "INSERT INTO users (username) VALUES (?)", {"password_hash": "$2b$12$geheim"}, Exception("boom")
        )

    monkeypatch.setattr("app.services.auth_service.create_user", explode)

    await _open_new_user_dialog(logged_in_user, username="pech", email="pech@example.com")
    logged_in_user.find("Speichern").click()

    await logged_in_user.should_see("fehlgeschlagen. Details stehen im Server-Log.")
    await logged_in_user.should_not_see("INSERT INTO")
    await logged_in_user.should_not_see("password_hash")

    # Der Fehler gehört ins Log (mit SQL), nicht in den Dialog. Die NiceGUI-User-Fixture
    # würde den erwarteten ERROR-Eintrag sonst als Testfehler werten.
    error_records = [r for r in caplog.get_records("call") if r.levelname == "ERROR"]
    assert any("Unerwarteter Fehler" in r.getMessage() for r in error_records)
    caplog.get_records("call").clear()


async def test_settings_reject_inverted_thresholds_without_saving(
    logged_in_user: TestUser, isolated_test_database
) -> None:
    from nicegui import ui

    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Ablauf-Schwellwerte")

    critical_input = logged_in_user.find(marker="expiry-critical-days").elements.pop()
    warning_input = logged_in_user.find(marker="expiry-warning-days").elements.pop()
    assert isinstance(critical_input, ui.number) and isinstance(warning_input, ui.number)
    critical_input.set_value(10)
    warning_input.set_value(5)
    logged_in_user.find(marker="save-expiry-thresholds").click()

    await logged_in_user.should_see("Kritisch")
    from app.services import preferences_service
    from sqlmodel import Session

    with Session(isolated_test_database) as session:
        assert preferences_service.get_system_setting(session, "expiry_critical_days") is None
