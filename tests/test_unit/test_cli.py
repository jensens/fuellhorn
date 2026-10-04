"""Tests für app.cli: Migrationen, run_app, create-admin, dispatch (vorher auf zwei Dateien verteilt, #392)."""

import app.cli
from app.models.user import Role
from app.services.auth_service import get_user_by_username
from pathlib import Path
import pytest
from sqlmodel import Session
from unittest.mock import MagicMock
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

    def test_create_admin_reset_password_recovers_locked_out_admin(self, session: Session, monkeypatch) -> None:
        """--reset-password macht einen degradierten/deaktivierten Admin wieder nutzbar (Issue #380)."""
        from app.models.user import User

        monkeypatch.setenv("ADMIN_PASSWORD", "recovered-password")
        locked_out = User(username="admin", email="admin@example.com", role=Role.USER, is_active=False)
        locked_out.set_password("forgotten")
        session.add(locked_out)
        session.commit()

        from app.cli import create_admin_user

        result = create_admin_user(session, reset_existing=True)

        assert result is True
        admin = get_user_by_username(session, "admin")
        assert admin.role == Role.ADMIN
        assert admin.is_active is True
        assert admin.check_password("recovered-password")

    def test_cli_create_admin_passes_reset_flag(self, session: Session, monkeypatch) -> None:
        monkeypatch.setenv("ADMIN_PASSWORD", "testpass")

        with (
            patch("app.database.get_session") as mock_get_session,
            patch("app.cli.create_admin_user", return_value=True) as mock_create,
        ):
            mock_get_session.return_value = iter([session])
            from app.cli import dispatch_command

            assert dispatch_command(["create-admin", "--reset-password"]) == 0

        assert mock_create.call_args.kwargs["reset_existing"] is True

    def test_cli_create_admin_rejects_short_password(self, session: Session, monkeypatch) -> None:
        """Kurzes ADMIN_PASSWORD → Exit 1 mit Meldung, kein Benutzer (Issue #383)."""
        monkeypatch.setenv("ADMIN_PASSWORD", "1")

        with patch("app.database.get_session") as mock_get_session:
            mock_get_session.return_value = iter([session])
            from app.cli import cli_create_admin

            assert cli_create_admin() == 1

        assert get_user_by_username(session, "admin") is None

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


class TestRunMigrations:
    """Tests for run_migrations function."""

    def test_creates_alembic_config_with_correct_script_location(self) -> None:
        """Should set script_location to alembic directory in package."""
        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch("app.config.Config.get_database_url", return_value="sqlite:///test.db"),
        ):
            import app.alembic
            from app.cli import run_migrations

            run_migrations()

            # Verify upgrade was called
            mock_upgrade.assert_called_once()

            # Get the config passed to upgrade
            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            expected_path = str(Path(app.alembic.__file__).parent)
            assert config.get_main_option("script_location") == expected_path

    def test_sets_database_url_from_environment(self) -> None:
        """Should set sqlalchemy.url from DATABASE_URL env var with psycopg3 dialect."""
        # Config.get_database_url() transforms postgresql:// to postgresql+psycopg://
        expected_url = "postgresql+psycopg://user:pass@localhost/testdb"

        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch("app.config.Config.get_database_url", return_value=expected_url),
        ):
            from app.cli import run_migrations

            run_migrations()

            # Get the config passed to upgrade
            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            assert config.get_main_option("sqlalchemy.url") == expected_url

    def test_sqlite_url_unchanged(self) -> None:
        """SQLite URLs should remain unchanged."""
        test_db_url = "sqlite:///test.db"

        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch("app.config.Config.get_database_url", return_value=test_db_url),
        ):
            from app.cli import run_migrations

            run_migrations()

            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            assert config.get_main_option("sqlalchemy.url") == test_db_url

    def test_uses_config_get_database_url(self) -> None:
        """Should use Config.get_database_url() for database URL."""
        mock_url = "sqlite:///default.db"

        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch("app.config.Config.get_database_url", return_value=mock_url) as mock_get_url,
        ):
            from app.cli import run_migrations

            run_migrations()

            # Verify Config.get_database_url() was called
            mock_get_url.assert_called_once()

            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            assert config.get_main_option("sqlalchemy.url") == mock_url

    def test_calls_upgrade_to_head(self) -> None:
        """Should call alembic upgrade to 'head'."""
        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch("app.config.Config.get_database_url", return_value="sqlite:///test.db"),
        ):
            from app.cli import run_migrations

            run_migrations()

            call_args = mock_upgrade.call_args
            assert call_args[0][1] == "head"


class TestRunApp:
    """Tests for run_app function."""

    def _create_mock_app(self) -> MagicMock:
        """Create a mock nicegui app."""
        mock_app = MagicMock()
        mock_app.add_static_files = MagicMock()
        mock_app.on_connect = MagicMock(return_value=lambda f: f)
        return mock_app

    def test_calls_run_migrations(self) -> None:
        """Should call run_migrations on startup."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations") as mock_run_migrations,
            patch.dict("sys.modules", {"nicegui": MagicMock()}),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run"),
            patch("app.config.get_storage_secret", return_value="test-secret"),
        ):
            from app.cli import run_app

            run_app()

            mock_run_migrations.assert_called_once()

    def test_skips_migrations_when_configured(self) -> None:
        """FUELLHORN_SKIP_MIGRATIONS=true: Helm migriert per Job/Init-Container, nicht jeder Pod (Issue #377)."""
        import app.config

        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations") as mock_run_migrations,
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run"),
            patch("app.config.get_storage_secret", return_value="test-secret"),
            patch.object(app.config.config, "SKIP_MIGRATIONS", True, create=True),
        ):
            from app.cli import run_app

            run_app()

            mock_run_migrations.assert_not_called()

    def test_configures_static_files(self) -> None:
        """Should configure static files directory."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run"),
            patch("app.config.get_storage_secret", return_value="test-secret"),
        ):
            from app.cli import run_app

            run_app()

            mock_app.add_static_files.assert_called_once()
            call_args = mock_app.add_static_files.call_args
            assert call_args[0][0] == "/static"
            assert "static" in call_args[0][1]

    def test_uses_configured_port(self) -> None:
        """Der Port aus der Konfiguration (PORT) wird an ui.run durchgereicht."""
        import app.config

        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run") as mock_run,
            patch("app.config.get_storage_secret", return_value="test-secret"),
            patch.object(app.config.config, "PORT", 9000),
        ):
            from app.cli import run_app

            run_app()

            assert mock_run.call_args[1]["port"] == 9000

    def test_uses_configured_host(self) -> None:
        """Die Bind-Adresse aus der Konfiguration (HOST) wird an ui.run durchgereicht (Issue #374)."""
        import app.config

        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run") as mock_run,
            patch("app.config.get_storage_secret", return_value="test-secret"),
            patch.object(app.config.config, "HOST", "127.0.0.1"),
        ):
            from app.cli import run_app

            run_app()

            assert mock_run.call_args[1]["host"] == "127.0.0.1"

    def test_runs_nicegui_with_correct_settings(self) -> None:
        """Should run NiceGUI with correct configuration."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run") as mock_run,
            patch("app.config.get_storage_secret", return_value="my-secret"),
        ):
            from app.cli import run_app

            run_app()

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]

            from app.startup import APP_TITLE

            assert call_kwargs["title"] == APP_TITLE
            assert call_kwargs["favicon"].endswith("fuellhorn-icon-192.png")
            assert call_kwargs["storage_secret"] == "my-secret"
            assert call_kwargs["reload"] is False
            assert call_kwargs["show"] is False

    def test_registers_pwa_routes_like_main(self) -> None:
        """Das CLI (Prod-Image) liefert Manifest und Icons wie main.py (Issue #375)."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run"),
            patch("app.config.get_storage_secret", return_value="test-secret"),
        ):
            from app.cli import run_app

            run_app()

            registered = {call.kwargs["url_path"] for call in mock_app.add_static_file.call_args_list}
            assert {"/manifest.json", "/icon-192.png", "/icon-512.png", "/apple-touch-icon.png"} <= registered


class TestMainEntryPoint:
    """Tests for __main__ entry point."""

    def test_main_is_callable(self) -> None:
        """Should export main as callable function."""
        from app.cli import main

        assert callable(main)


class TestDispatchCommand:
    """Tests for dispatch_command function."""

    def test_seed_command_without_subcommand_returns_error(self) -> None:
        """Should return 1 when seed called without subcommand."""
        from app.cli import dispatch_command

        result = dispatch_command(["seed"])

        assert result == 1

    def test_seed_command_with_unknown_subcommand_returns_error(self) -> None:
        """Should return 1 for unknown seed subcommand (ohne Migrationen anzustoßen)."""
        with (
            patch("app.cli.run_migrations") as mock_migrations,
            patch("app.database.get_engine"),
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "unknown"])

            assert result == 1
            mock_migrations.assert_not_called()

    def test_seed_shelf_life_defaults_runs_migrations_then_seeds(self) -> None:
        """shelf-life-defaults migriert per Alembic (statt create_all) und seedet dann (#376)."""
        with (
            patch("app.cli.run_migrations") as mock_migrations,
            patch("app.database.get_engine"),
            patch("app.seed.seed_shelf_life_defaults", return_value=(10, 20)) as mock_seed,
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "shelf-life-defaults"])

            mock_migrations.assert_called_once()
            mock_seed.assert_called_once()
            assert result == 0

    def test_seed_testdata_calls_seed_function(self) -> None:
        """Should call seed_testdata for testdata subcommand (mit ausdrücklichem Dev-Flag)."""
        with (
            patch("app.cli.run_migrations"),
            patch("app.database.get_engine"),
            patch(
                "app.seed.seed_testdata", return_value={"admin": 1, "categories": 5, "locations": 3, "items": 8}
            ) as mock_seed,
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "testdata", "--i-know-this-is-dev"])

            mock_seed.assert_called_once()
            assert result == 0

    def test_unknown_command_returns_error(self) -> None:
        """Should return 1 for unknown command."""
        from app.cli import dispatch_command

        result = dispatch_command(["unknown-command"])

        assert result == 1

    def test_seed_in_available_commands_message(self) -> None:
        """Should list seed in available commands."""
        from app.cli import dispatch_command
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        dispatch_command(["unknown"])

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        assert "seed" in output


class TestCreateAdminScript:
    """Das Wurzel-Skript create_admin.py ist nur ein Re-Export des CLI (vorher 4 doppelte Tests)."""

    def test_script_reexports_cli_function(self) -> None:
        import create_admin

        assert create_admin.create_admin_user is app.cli.create_admin_user
