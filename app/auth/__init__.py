"""Auth Module fuer Fuellhorn.

Provides:
- Permission System
- User Dependencies
- Decorators fuer UI & API
"""

from .decorators import require_auth
from .decorators import require_permissions
from .decorators import with_permission_check
from .dependencies import AuthenticationError
from .dependencies import AuthorizationError
from .dependencies import check_permission
from .dependencies import clear_current_user_cache
from .dependencies import get_current_user
from .dependencies import get_current_user_from_request
from .dependencies import get_current_user_id
from .dependencies import require_api_permission
from .dependencies import require_permission
from .permissions import Permission
from .permissions import get_permissions_for_user


__all__ = [
    # Permissions
    "Permission",
    "get_permissions_for_user",
    # Dependencies
    "get_current_user",
    "get_current_user_id",
    "check_permission",
    "require_permission",
    "clear_current_user_cache",
    # FastAPI
    "get_current_user_from_request",
    "require_api_permission",
    # Decorators
    "require_auth",
    "require_permissions",
    "with_permission_check",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
]
