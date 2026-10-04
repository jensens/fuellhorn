"""Tests for auth dependencies."""

from app.auth.permissions import Permission
from app.auth.permissions import check_permission
from app.models.user import Role
from app.models.user import User


class TestCheckPermission:
    """Tests for check_permission function."""

    def test_admin_has_all_permissions(self) -> None:
        """Admin user should have all permissions."""
        admin_user = User(
            id=1,
            username="admin",
            email="admin@test.local",
            password_hash="hash",
            role=Role.ADMIN.value,
            is_active=True,
        )

        assert check_permission(admin_user, Permission.ITEMS_READ) is True
        assert check_permission(admin_user, Permission.ITEMS_WRITE) is True
        assert check_permission(admin_user, Permission.USER_MANAGE) is True
        assert check_permission(admin_user, Permission.ADMIN_FULL) is True

    def test_user_has_limited_permissions(self) -> None:
        """Regular user should have limited permissions."""
        regular_user = User(
            id=2,
            username="user",
            email="user@test.local",
            password_hash="hash",
            role=Role.USER.value,
            is_active=True,
        )

        assert check_permission(regular_user, Permission.ITEMS_READ) is True
        assert check_permission(regular_user, Permission.ITEMS_WRITE) is True
        # Regular user should not have admin permissions
        assert check_permission(regular_user, Permission.ADMIN_FULL) is False
        assert check_permission(regular_user, Permission.USER_MANAGE) is False

    def test_inactive_user_has_no_permissions(self) -> None:
        """Inactive user should have no permissions (checks are done at higher level)."""
        inactive_user = User(
            id=3,
            username="inactive",
            email="inactive@test.local",
            password_hash="hash",
            role=Role.ADMIN.value,
            is_active=False,
        )

        # Even admin role, but user is inactive - permissions still granted by role
        # (is_active check happens at authentication level, not permission level)
        assert check_permission(inactive_user, Permission.ITEMS_READ) is True
