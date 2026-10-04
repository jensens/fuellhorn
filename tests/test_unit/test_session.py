"""Tests für die Login-Sitzung in app.storage.user (Issue #384).

Vorher: Remember-Me erzeugte ein Token, das nie zurückgelesen wurde; die
Session-Dauer war für alle der Starlette-Default (14 Tage); Passwortänderung
und Admin-Reset meldeten andere Sitzungen nicht ab.
"""

from app.auth.session import PASSWORD_CHANGED_MESSAGE
from app.auth.session import SESSION_EXPIRED_MESSAGE
from app.auth.session import end_session
from app.auth.session import refresh_session_version
from app.auth.session import session_problem
from app.auth.session import start_session
from app.auth.session import touch_session
from app.models.user import User
from datetime import datetime
from datetime import timedelta


NOW = datetime(2026, 10, 4, 12, 0, 0)
DAY = 86400


def _user(**overrides) -> User:
    values = {"id": 7, "username": "anna", "email": "anna@example.com", "role": "user", "session_version": 3}
    values.update(overrides)
    return User(**values)


class TestStartAndEndSession:
    def test_start_session_stores_identity_version_and_activity(self) -> None:
        storage: dict = {"flash": {"message": "alt"}}

        start_session(_user(), remember_me=False, storage=storage, now=NOW)

        assert storage["authenticated"] is True
        assert storage["user_id"] == 7
        assert storage["username"] == "anna"
        assert storage["remember_me"] is False
        assert storage["session_version"] == 3
        assert storage["last_seen"] == NOW.isoformat()
        assert "flash" not in storage, "Reste einer alten Sitzung dürfen nicht überleben"

    def test_start_session_remember_me_flag(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=True, storage=storage, now=NOW)
        assert storage["remember_me"] is True

    def test_end_session_clears_everything(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=True, storage=storage, now=NOW)
        end_session(storage)
        assert storage == {}


class TestSessionProblem:
    def test_fresh_session_is_valid(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=False, storage=storage, now=NOW)

        assert session_problem(storage, _user(), now=NOW + timedelta(hours=1), max_age=DAY) is None

    def test_inactive_session_expires_after_max_age(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=False, storage=storage, now=NOW)

        later = NOW + timedelta(seconds=DAY)
        assert session_problem(storage, _user(), now=later, max_age=DAY) == SESSION_EXPIRED_MESSAGE

    def test_activity_extends_the_session(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=False, storage=storage, now=NOW)

        touch_session(storage, now=NOW + timedelta(hours=20))
        still_later = NOW + timedelta(hours=30)
        assert session_problem(storage, _user(), now=still_later, max_age=DAY) is None

    def test_remember_me_ignores_inactivity_limit(self) -> None:
        storage: dict = {}
        start_session(_user(), remember_me=True, storage=storage, now=NOW)

        weeks_later = NOW + timedelta(days=20)
        assert session_problem(storage, _user(), now=weeks_later, max_age=DAY) is None

    def test_password_change_invalidates_session(self) -> None:
        storage: dict = {}
        start_session(_user(session_version=3), remember_me=True, storage=storage, now=NOW)

        assert session_problem(storage, _user(session_version=4), now=NOW, max_age=DAY) == PASSWORD_CHANGED_MESSAGE

    def test_legacy_session_without_version_is_expired(self) -> None:
        """Sitzungen aus der Zeit vor #384 haben weder Version noch Aktivität → einmal neu anmelden."""
        legacy = {"authenticated": True, "user_id": 7, "username": "anna"}

        assert session_problem(legacy, _user(), now=NOW, max_age=DAY) == SESSION_EXPIRED_MESSAGE

    def test_refresh_session_version_keeps_own_session_after_password_change(self) -> None:
        storage: dict = {}
        user = _user(session_version=3)
        start_session(user, remember_me=False, storage=storage, now=NOW)

        user.set_password("neues-passwort-123")
        refresh_session_version(user, storage=storage)

        assert session_problem(storage, user, now=NOW, max_age=DAY) is None


class TestSessionVersionOnUser:
    def test_set_password_bumps_session_version(self) -> None:
        user = _user(session_version=0)

        user.set_password("erstes-passwort")
        user.set_password("zweites-passwort")

        assert user.session_version == 2

    def test_user_has_no_remember_token_anymore(self) -> None:
        assert "remember_token" not in User.model_fields
        assert "session_version" in User.model_fields
