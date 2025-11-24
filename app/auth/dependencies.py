"""Auth Dependencies fuer User-Fetching und Permission-Checks.

Bietet Funktionen um den aktuellen User zu holen und Permissions zu pruefen.
"""

from ..database import get_session
from ..models.user import User
from ..services.auth_service import get_user
from .permissions import Permission
from .permissions import get_permissions_for_user
from collections.abc import Callable
from contextvars import ContextVar
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from nicegui import app
from typing import Any


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

            # Store in cache
            if use_cache:
                _current_user_cache.set(user)

            return user
        except Exception as e:
            if require_auth:
                raise AuthenticationError(f"Benutzer nicht gefunden: {e}") from e
            return None


def clear_current_user_cache() -> None:
    """Clear den request-scoped user cache."""
    _current_user_cache.set(None)


def check_permission(permission: Permission, user: User | None = None) -> bool:
    """Check ob current user eine bestimmte Permission hat.

    Args:
        permission: Die zu pruefende Permission.
        user: Optional user object (wird gefetched wenn nicht angegeben).

    Returns:
        True wenn user die Permission hat, False sonst.
    """
    if user is None:
        try:
            user = get_current_user(require_auth=True)
        except AuthenticationError:
            return False

    if user is None:
        return False

    user_permissions = get_permissions_for_user(user)
    return permission in user_permissions


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

    if not check_permission(permission, user):
        raise AuthorizationError(f"Fehlende Permission: {permission.value}")

    return user


# FastAPI Dependencies fuer API Routes


async def get_current_user_from_request(request: Request) -> User:
    """FastAPI dependency um current user aus request zu holen.

    Usage in API routes:
        @app.get("/api/protected")
        async def protected_endpoint(
            current_user: User = Depends(get_current_user_from_request)
        ):
            # current_user ist garantiert authentifiziert
            ...

    Args:
        request: FastAPI Request object.

    Returns:
        Authenticated User object.

    Raises:
        HTTPException: 401 wenn nicht authentifiziert.
    """
    # Get session cookie
    session_id = request.cookies.get("nicegui-storage-session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    # Try to get user from session
    try:
        user = get_current_user(require_auth=True)
        # user is guaranteed to be not None here because require_auth=True
        assert user is not None
        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def require_api_permission(permission: Permission) -> Callable[[User], Any]:
    """FastAPI dependency factory fuer Permission-Checking.

    Usage:
        @app.get("/api/items")
        async def get_items(
            user: User = Depends(require_api_permission(Permission.ITEMS_READ))
        ):
            # user ist garantiert authentifiziert UND hat ITEMS_READ
            ...

    Args:
        permission: Die required Permission.

    Returns:
        FastAPI dependency function.
    """

    async def permission_checker(
        user: User = Depends(get_current_user_from_request),
    ) -> User:
        """Check permission for API endpoint."""
        if not check_permission(permission, user):
            raise HTTPException(status_code=403, detail=f"Fehlende Permission: {permission.value}")
        return user

    return permission_checker
