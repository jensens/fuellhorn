"""Tests für auth_service.authenticate_user (Issue #388).

Vorher gab es keinen einzigen Test für den Kern des Logins; der einzige
Fehl-Login-Test war E2E und lief nie in CI.
"""

from app.models.user import User
from app.services import auth_service
from app.services.auth_service import AuthenticationError
from datetime import datetime
from freezegun import freeze_time
import logging
import pytest
from sqlmodel import Session


NOW = datetime(2026, 10, 4, 12, 0, 0)


@pytest.fixture(name="anna")
def anna_fixture(session: Session) -> User:
    user = User(username="anna", email="anna@example.com", role="user", is_active=True)
    user.set_password("richtig-geheim")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestAuthenticateUser:
    def test_unknown_username_is_rejected_with_generic_message(self, session: Session) -> None:
        with pytest.raises(AuthenticationError, match="Username oder Passwort falsch"):
            auth_service.authenticate_user(session, "niemand", "egal")

    def test_wrong_password_is_rejected_with_the_same_message(self, session: Session, anna: User) -> None:
        """Gleiche Meldung wie bei unbekanntem Benutzer: kein User-Enumeration-Leck."""
        with pytest.raises(AuthenticationError, match="Username oder Passwort falsch"):
            auth_service.authenticate_user(session, "anna", "falsch")

    def test_inactive_user_gets_the_generic_message_and_the_reason_is_logged(
        self, session: Session, anna: User, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Kein User-Enumeration-Leck: „deaktiviert“ steht nur im Log (Issue #402)."""
        anna.is_active = False
        session.add(anna)
        session.commit()

        with (
            caplog.at_level(logging.INFO, logger="app.services.auth_service"),
            pytest.raises(AuthenticationError) as excinfo,
        ):
            auth_service.authenticate_user(session, "anna", "richtig-geheim")

        assert str(excinfo.value) == "Username oder Passwort falsch"
        assert "deaktiviert" in caplog.text and "anna" in caplog.text

    def test_user_model_has_no_manual_lock_anymore(self) -> None:
        """locked_until hatte keinen Schreiber und keine UI; Deaktivieren über is_active reicht (Issue #402)."""
        assert "locked_until" not in User.model_fields

    def test_successful_login_updates_last_login(self, session: Session, anna: User) -> None:
        assert anna.last_login is None

        with freeze_time(NOW):
            user = auth_service.authenticate_user(session, "anna", "richtig-geheim")

        assert user.last_login == NOW
        session.refresh(anna)
        assert anna.last_login == NOW

    def test_failed_login_does_not_touch_last_login(self, session: Session, anna: User) -> None:
        with pytest.raises(AuthenticationError):
            auth_service.authenticate_user(session, "anna", "falsch")

        session.refresh(anna)
        assert anna.last_login is None
