"""Auth Dependencies fuer User-Fetching und Permission-Checks.

Bietet Funktionen um den aktuellen User zu holen und Permissions zu pruefen.
"""

from ..database import get_session
from ..models.user import User
from ..services.auth_service import get_user
from .permissions import Permission
from .permissions import check_permission
from .session import end_session
from .session import session_problem
from .session import touch_session
from contextvars import ContextVar
from nicegui import app


# Request-scoped cache fuer current_user
# Wird automatisch pro Request gecleared (ContextVar ist request-scoped)
_current_user_cache: ContextVar[User | None] = ContextVar("current_user", default=None)


class AuthenticationError(Exception):
    """User ist nicht authentifiziert."""

    pass


class AuthorizationError(Exception):
    """User hat nicht die noetige Permission."""

    pass


def get_current_user_id() -> int | None:
    """Get current user ID aus NiceGUI session storage.

    Returns:
        User ID wenn authentifiziert, None sonst.
    """
    if not app.storage.user.get("authenticated", False):
        return None
    return app.storage.user.get("user_id")


def get_current_user(require_auth: bool = True, use_cache: bool = True) -> User | None:
    """Get current user from database (fresh data!).

    Fetched den User aus der Datenbank mit aktuellem Stand.
    Nutzt Request-Scoped Caching fuer Performance.

    Args:
        require_auth: Wenn True, raise Exception wenn nicht authentifiziert.
        use_cache: Wenn True, nutze Request-Scoped Cache.

    Returns:
        User object wenn authentifiziert, None wenn nicht required.

    Raises:
        AuthenticationError: Wenn require_auth=True und user nicht authentifiziert.
    """
    # Check cache first
    if use_cache:
        cached_user = _current_user_cache.get()
        if cached_user is not None:
            return cached_user

    # Get user ID from session
    user_id = get_current_user_id()

    if user_id is None:
        if require_auth:
            raise AuthenticationError("Nicht authentifiziert")
        return None

    # Fetch fresh user data from database
    with next(get_session()) as session:
        try:
            user = get_user(session, user_id)

            # Check if user is still active
            if not user.is_active:
                raise AuthenticationError("Benutzer ist deaktiviert")

            # Sitzung abgelaufen, Passwort geändert oder Konto gesperrt (Issue #384):
            # abmelden, Grund für die Login-Seite vormerken
            problem = session_problem(app.storage.user, user)
            if problem is not None:
                end_session(reason=problem)
                raise AuthenticationError(problem)
            touch_session()

            # Store in cache
            if use_cache:
                _current_user_cache.set(user)

            return user
        except AuthenticationError:
            # deaktiviert, Sitzung abgelaufen, Passwort geändert, gesperrt: Grund unverändert weitergeben
            if require_auth:
                raise
            return None
        except Exception as e:
            if require_auth:
                raise AuthenticationError(f"Benutzer nicht gefunden: {e}") from e
            return None


def clear_current_user_cache() -> None:
    """Clear den request-scoped user cache."""
    _current_user_cache.set(None)


def require_permission(permission: Permission, user: User | None = None) -> User:
    """Require dass current user eine bestimmte Permission hat.

    Args:
        permission: Die zu pruefende Permission.
        user: Optional user object (wird gefetched wenn nicht angegeben).

    Returns:
        Der authentifizierte und autorisierte User.

    Raises:
        AuthenticationError: Wenn nicht authentifiziert.
        AuthorizationError: Wenn nicht autorisiert.
    """
    if user is None:
        user = get_current_user(require_auth=True)

    # user is guaranteed to be not None here because require_auth=True
    assert user is not None

    if not check_permission(user, permission):
        raise AuthorizationError(f"Fehlende Permission: {permission.value}")

    return user
