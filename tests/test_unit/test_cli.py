"""Tests for CLI commands."""

from app.models.user import Role
from app.services.auth_service import get_user_by_username
import pytest
from sqlmodel import Session
from unittest.mock import patch


class TestCLIMigrate:
    """Tests for fuellhorn migrate command."""

    def test_migrate_runs_migrations(self) -> None:
        """Migrate command runs alembic migrations."""
        with patch("app.cli.run_migrations") as mock_migrations:
            from app.cli import cli_migrate

            cli_migrate()

            mock_migrations.assert_called_once()

    def test_migrate_returns_zero_on_success(self) -> None:
        """Migrate command returns 0 on success."""
        with patch("app.cli.run_migrations"):
            from app.cli import cli_migrate

            result = cli_migrate()

            assert result == 0


class TestCLICreateAdmin:
    """Tests for fuellhorn create-admin command."""

    def test_create_admin_creates_user_with_env_vars(self, session: Session, monkeypatch) -> None:
        """Create-admin command creates admin user from environment variables."""
        monkeypatch.setenv("ADMIN_USERNAME", "helmadmin")
        monkeypatch.setenv("ADMIN_EMAIL", "helm@example.com")
        monkeypatch.setenv("ADMIN_PASSWORD", "helmpassword123")

        from app.cli import create_admin_user

        result = create_admin_user(session)

        assert result is True
        admin = get_user_by_username(session, "helmadmin")
        assert admin is not None
        assert admin.email == "helm@example.com"
        assert admin.role == Role.ADMIN
        assert admin.check_password("helmpassword123")

    def test_create_admin_uses_defaults(self, session: Session, monkeypatch) -> None:
        """Create-admin uses default username/email when not specified."""
        monkeypatch.setenv("ADMIN_PASSWORD", "testpassword")
        monkeypatch.delenv("ADMIN_USERNAME", raising=False)
        monkeypatch.delenv("ADMIN_EMAIL", raising=False)

        from app.cli import create_admin_user

        result = create_admin_user(session)

        assert result is True
        admin = get_user_by_username(session, "admin")
        assert admin is not None
        assert admin.email == "admin@fuellhorn.local"

    def test_create_admin_skips_existing(self, session: Session, monkeypatch) -> None:
        """Create-admin returns False if admin already exists."""
        from app.models.user import User

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

        from app.cli import create_admin_user

        result = create_admin_user(session)

        assert result is False
        admin = get_user_by_username(session, "admin")
        assert admin.email == "existing@example.com"

    def test_create_admin_fails_without_password(self, session: Session, monkeypatch) -> None:
        """Create-admin raises error when ADMIN_PASSWORD not set."""
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

        from app.cli import create_admin_user

        with pytest.raises(ValueError, match="ADMIN_PASSWORD"):
            create_admin_user(session)

    def test_cli_create_admin_returns_zero_on_success(self, session: Session, monkeypatch) -> None:
        """CLI create-admin returns 0 on success."""
        monkeypatch.setenv("ADMIN_PASSWORD", "testpass")

        with patch("app.database.get_session") as mock_get_session:
            mock_get_session.return_value = iter([session])

            from app.cli import cli_create_admin

            result = cli_create_admin()

            assert result == 0

    def test_cli_create_admin_returns_one_on_error(self, session: Session, monkeypatch) -> None:
        """CLI create-admin returns 1 on error."""
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

        with patch("app.database.get_session") as mock_get_session:
            mock_get_session.return_value = iter([session])

            from app.cli import cli_create_admin

            result = cli_create_admin()

            assert result == 1


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_main_with_migrate_calls_migrate(self) -> None:
        """Main with 'migrate' argument calls cli_migrate."""
        with patch("app.cli.cli_migrate") as mock_migrate, patch("sys.argv", ["fuellhorn", "migrate"]):
            mock_migrate.return_value = 0

            # main() without args runs the app, so we test via dispatch
            from app.cli import dispatch_command

            result = dispatch_command(["migrate"])

            mock_migrate.assert_called_once()
            assert result == 0

    def test_main_with_create_admin_calls_create_admin(self) -> None:
        """Main with 'create-admin' argument calls cli_create_admin."""
        with patch("app.cli.cli_create_admin") as mock_create:
            mock_create.return_value = 0

            from app.cli import dispatch_command

            result = dispatch_command(["create-admin"])

            mock_create.assert_called_once()
            assert result == 0

    def test_main_without_args_runs_app(self) -> None:
        """Main without arguments starts the application."""
        with patch("app.cli.run_app") as mock_run:
            from app.cli import dispatch_command

            dispatch_command([])

            mock_run.assert_called_once()
