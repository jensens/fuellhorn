"""Decorators für Permission-Checking in UI und Actions.

Bietet Decorators für UI-Pages und Helper-Funktionen.
"""

from .dependencies import AuthenticationError
from .dependencies import AuthorizationError
from .dependencies import check_permission
from .dependencies import get_current_user
from .permissions import Permission
from .permissions import get_permissions_for_user
from collections.abc import Callable
from functools import wraps
from nicegui import ui
from typing import ParamSpec
from typing import TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def require_auth(func: Callable[P, R]) -> Callable[P, R | None]:
    """Decorator um Authentication für eine UI-Page zu erzwingen.

    Redirected zum Login wenn nicht authentifiziert.

    Usage:
        @ui.page("/dashboard")
        @require_auth
        def dashboard():
            # User ist garantiert authentifiziert
            ...

    Args:
        func: Die zu schützende Funktion.

    Returns:
        Wrapped function die Authentication prüft.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            get_current_user(require_auth=True)
            return func(*args, **kwargs)
        except AuthenticationError:
            ui.navigate.to("/login")
            return None

    return wrapper


def require_permissions(
    *permissions: Permission, require_all: bool = False, redirect_to: str = "/dashboard"
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Decorator um spezifische Permissions für eine UI-Page zu erzwingen.

    Redirected und zeigt Notification wenn nicht autorisiert.

    Args:
        *permissions: Permission(s) die required sind.
        require_all: Wenn True, require ALLE permissions. Wenn False, require ANY.
        redirect_to: Wohin redirected werden soll wenn nicht autorisiert.

    Usage:
        @ui.page("/users")
        @require_permissions(Permission.USER_MANAGE)
        def users_page():
            # User hat garantiert USER_MANAGE permission
            ...

        @ui.page("/config")
        @require_permissions(
            Permission.CONFIG_MANAGE,
            Permission.ADMIN_FULL,
            require_all=False
        )
        def config_page():
            # User hat mindestens eine der beiden permissions
            ...

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                user = get_current_user(require_auth=True)
                # user is guaranteed to be not None here because require_auth=True
                assert user is not None

                # Check permissions
                user_perms = get_permissions_for_user(user)

                if require_all:
                    has_access = all(perm in user_perms for perm in permissions)
                else:
                    has_access = any(perm in user_perms for perm in permissions)

                if not has_access:
                    perm_names = ", ".join(p.value for p in permissions)
                    ui.notify(
                        f"Keine Berechtigung für diese Seite ({perm_names})",
                        type="negative",
                    )
                    ui.navigate.to(redirect_to)
                    return None

                return func(*args, **kwargs)

            except AuthenticationError:
                ui.navigate.to("/login")
                return None

        return wrapper

    return decorator


def with_permission_check(
    permission: Permission,
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Decorator für UI helper functions die Permission-Checks brauchen.

    Zeigt Notification und returned None wenn nicht autorisiert.
    Nützlich für Action-Handler (z.B. Button Click Handler).

    Usage:
        @with_permission_check(Permission.ITEMS_WRITE)
        def add_item():
            # Nur ausgeführt wenn user die Permission hat
            # Notification wird automatisch gezeigt wenn nicht
            ...

        @with_permission_check(Permission.USER_MANAGE)
        def delete_user(user_id: int):
            # Safe delete - nur wenn autorisiert
            ...

    Args:
        permission: Die required Permission.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                user = get_current_user(require_auth=True)

                if not check_permission(permission, user):
                    ui.notify(
                        f"Keine Berechtigung für diese Aktion ({permission.value})",
                        type="negative",
                    )
                    return None

                return func(*args, **kwargs)

            except (AuthenticationError, AuthorizationError) as e:
                ui.notify(str(e), type="negative")
                return None

        return wrapper

    return decorator
