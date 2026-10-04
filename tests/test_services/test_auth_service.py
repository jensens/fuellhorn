"""Tests für auth_service.authenticate_user (Issue #388).

Vorher gab es keinen einzigen Test für den Kern des Logins; der einzige
Fehl-Login-Test war E2E und lief nie in CI.
"""

from app.models.user import User
from app.services import auth_service
from app.services.auth_service import AuthenticationError
from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
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

    def test_inactive_user_is_rejected(self, session: Session, anna: User) -> None:
        anna.is_active = False
        session.add(anna)
        session.commit()

        with pytest.raises(AuthenticationError, match="deaktiviert"):
            auth_service.authenticate_user(session, "anna", "richtig-geheim")

    def test_locked_user_is_rejected_until_lock_expires(self, session: Session, anna: User) -> None:
        anna.locked_until = NOW + timedelta(minutes=30)
        session.add(anna)
        session.commit()

        with freeze_time(NOW), pytest.raises(AuthenticationError, match="gesperrt bis 12:30 Uhr"):
            auth_service.authenticate_user(session, "anna", "richtig-geheim")

    def test_expired_lock_does_not_block(self, session: Session, anna: User) -> None:
        anna.locked_until = NOW - timedelta(minutes=1)
        session.add(anna)
        session.commit()

        with freeze_time(NOW):
            user = auth_service.authenticate_user(session, "anna", "richtig-geheim")

        assert user.id == anna.id

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
