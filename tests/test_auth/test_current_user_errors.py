"""get_current_user: Fehlerarten bleiben unterscheidbar (Issue #402).

Vorher wandelte ``except Exception`` jede Ausnahme in ``AuthenticationError("Benutzer
nicht gefunden: …")`` – auch Datenbankausfälle (→ Redirect zum Login statt Fehler)
und den eigenen Deaktiviert-Fehler (→ "Benutzer nicht gefunden: Benutzer ist deaktiviert").
"""

from app.auth import dependencies
from app.auth.dependencies import AuthenticationError
from app.models.user import User
from app.services.auth_service import UserNotFoundError
import pytest
from sqlalchemy.exc import OperationalError


@pytest.fixture(autouse=True)
def _logged_in_as_user_7(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dependencies, "get_current_user_id", lambda: 7)
    dependencies.clear_current_user_cache()


def test_missing_user_becomes_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(session, user_id):
        raise UserNotFoundError(f"User {user_id} nicht gefunden")

    monkeypatch.setattr(dependencies, "get_user", missing)

    with pytest.raises(AuthenticationError, match="Benutzer nicht gefunden"):
        dependencies.get_current_user(require_auth=True)
    assert dependencies.get_current_user(require_auth=False) is None


def test_deactivated_user_keeps_its_own_message(monkeypatch: pytest.MonkeyPatch) -> None:
    inactive = User(id=7, username="anna", email="anna@example.com", role="user", is_active=False)
    monkeypatch.setattr(dependencies, "get_user", lambda session, user_id: inactive)

    with pytest.raises(AuthenticationError) as excinfo:
        dependencies.get_current_user(require_auth=True)

    assert str(excinfo.value) == "Benutzer ist deaktiviert"


def test_database_errors_are_not_disguised_as_login_problems(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ein DB-Ausfall soll als Fehler sichtbar werden, nicht als Abmeldung."""

    def db_down(session, user_id):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(dependencies, "get_user", db_down)

    with pytest.raises(OperationalError):
        dependencies.get_current_user(require_auth=True)
    with pytest.raises(OperationalError):
        dependencies.get_current_user(require_auth=False)
