"""Tests for create_admin.py script with environment variable support."""

from app.models.user import Role
from app.models.user import User
from app.services.auth_service import get_user_by_username
import pytest
from sqlmodel import Session


class TestCreateAdmin:
    """Tests for admin user creation script."""

    def test_creates_admin_with_env_vars(self, session: Session, monkeypatch) -> None:
        """Creates admin with credentials from environment variables."""
        monkeypatch.setenv("ADMIN_USERNAME", "customadmin")
        monkeypatch.setenv("ADMIN_EMAIL", "custom@example.com")
        monkeypatch.setenv("ADMIN_PASSWORD", "securepassword123")

        from create_admin import create_admin_user

        result = create_admin_user(session)

        assert result is True
        admin = get_user_by_username(session, "customadmin")
        assert admin.email == "custom@example.com"
        assert admin.role == Role.ADMIN
        assert admin.check_password("securepassword123")

    def test_creates_admin_with_defaults(self, session: Session, monkeypatch) -> None:
        """Creates admin with default username/email when only password is set."""
        monkeypatch.setenv("ADMIN_PASSWORD", "securepassword123")
        monkeypatch.delenv("ADMIN_USERNAME", raising=False)
        monkeypatch.delenv("ADMIN_EMAIL", raising=False)

        from create_admin import create_admin_user

        result = create_admin_user(session)

        assert result is True
        admin = get_user_by_username(session, "admin")
        assert admin.email == "admin@fuellhorn.local"
        assert admin.role == Role.ADMIN

    def test_skips_if_admin_exists(self, session: Session, monkeypatch) -> None:
        """Returns False and does not modify existing admin user."""
        monkeypatch.setenv("ADMIN_PASSWORD", "newpassword")

        # Create existing admin
        existing = User(
            username="admin",
            email="existing@example.com",
            role=Role.ADMIN,
            is_active=True,
        )
        existing.set_password("oldpassword")
        session.add(existing)
        session.commit()

        from create_admin import create_admin_user

        result = create_admin_user(session)

        assert result is False
        admin = get_user_by_username(session, "admin")
        assert admin.email == "existing@example.com"
        assert admin.check_password("oldpassword")

    def test_fails_without_password_env_var(self, session: Session, monkeypatch) -> None:
        """Raises error when ADMIN_PASSWORD is not set."""
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

        from create_admin import create_admin_user

        with pytest.raises(ValueError, match="ADMIN_PASSWORD"):
            create_admin_user(session)
