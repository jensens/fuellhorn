"""Permission System für Fuellhorn.

Definiert alle Permissions und mappt Rollen auf Permissions.
"""

from ..models.user import Role
from ..models.user import User
from enum import Enum


class Permission(str, Enum):
    """Alle verfügbaren Permissions im System.

    Fuellhorn hat ein vereinfachtes Permission-System mit nur 2 Rollen:
    - ADMIN: Voller Zugriff + Benutzerverwaltung + Konfiguration
    - USER: Artikel erfassen, entnehmen, durchsuchen
    """

    # Admin Permissions
    ADMIN_FULL = "admin:full"
    USER_MANAGE = "admin:users:manage"
    CONFIG_MANAGE = "admin:config:manage"  # Kategorien, Lagerorte, Gefrierzeiten

    # Item Permissions
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"


def get_permissions_for_user(user: User) -> set[Permission]:
    """Get all permissions für einen User basierend auf seiner Rolle.

    Dies ist die zentrale Stelle wo Rollen → Permissions gemappt werden.

    Args:
        user: Der User für den die Permissions ermittelt werden.

    Returns:
        Set von Permissions die der User hat.
    """
    permissions: set[Permission] = set()

    # Admin hat ALLE Permissions
    if user.has_role(Role.ADMIN):
        permissions.update(
            [
                Permission.ADMIN_FULL,
                Permission.USER_MANAGE,
                Permission.CONFIG_MANAGE,
                Permission.ITEMS_READ,
                Permission.ITEMS_WRITE,
            ]
        )

    # User (Befüller) - kann Artikel lesen und schreiben
    if user.has_role(Role.USER):
        permissions.update(
            [
                Permission.ITEMS_READ,
                Permission.ITEMS_WRITE,
            ]
        )

    return permissions


def check_permission(user: User, permission: Permission) -> bool:
    """Prüft ob ein User eine bestimmte Permission hat.

    Args:
        user: Der zu prüfende User
        permission: Die zu prüfende Permission

    Returns:
        True wenn der User die Permission hat, sonst False
    """
    return permission in get_permissions_for_user(user)
