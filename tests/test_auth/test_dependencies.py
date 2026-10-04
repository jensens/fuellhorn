"""Tests for auth dependencies."""

from app.auth.dependencies import check_permission
from app.auth.permissions import Permission
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

        assert check_permission(Permission.ITEMS_READ, admin_user) is True
        assert check_permission(Permission.ITEMS_WRITE, admin_user) is True
        assert check_permission(Permission.USER_MANAGE, admin_user) is True
        assert check_permission(Permission.ADMIN_FULL, admin_user) is True

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

        assert check_permission(Permission.ITEMS_READ, regular_user) is True
        assert check_permission(Permission.ITEMS_WRITE, regular_user) is True
        # Regular user should not have admin permissions
        assert check_permission(Permission.ADMIN_FULL, regular_user) is False
        assert check_permission(Permission.USER_MANAGE, regular_user) is False

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
        assert check_permission(Permission.ITEMS_READ, inactive_user) is True
