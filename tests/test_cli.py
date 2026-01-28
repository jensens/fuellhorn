"""Tests for CLI entry point."""

import os
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


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

    def test_uses_default_port_8080(self) -> None:
        """Should use port 8080 when PORT env var not set."""
        env = os.environ.copy()
        env.pop("PORT", None)
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run") as mock_run,
            patch("app.config.get_storage_secret", return_value="test-secret"),
            patch.dict(os.environ, env, clear=True),
        ):
            from app.cli import run_app

            run_app()

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["port"] == 8080

    def test_uses_custom_port_from_environment(self) -> None:
        """Should use port from PORT env var."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run") as mock_run,
            patch("app.config.get_storage_secret", return_value="test-secret"),
            patch.dict(os.environ, {"PORT": "9000"}),
        ):
            from app.cli import run_app

            run_app()

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["port"] == 9000

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

            assert call_kwargs["title"] == "Fuellhorn"
            assert call_kwargs["storage_secret"] == "my-secret"
            assert call_kwargs["reload"] is False
            assert call_kwargs["show"] is False

    def test_registers_on_connect_handler(self) -> None:
        """Should register on_connect handler for theme loading."""
        mock_app = self._create_mock_app()

        with (
            patch("app.cli.run_migrations"),
            patch("nicegui.app", mock_app),
            patch("nicegui.ui.run"),
            patch("app.config.get_storage_secret", return_value="test-secret"),
        ):
            from app.cli import run_app

            run_app()

            mock_app.on_connect.assert_called_once()


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
        """Should return 1 for unknown seed subcommand."""
        with (
            patch("app.database.create_db_and_tables"),
            patch("app.database.get_engine"),
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "unknown"])

            assert result == 1

    def test_seed_shelf_life_defaults_calls_seed_function(self) -> None:
        """Should call seed_shelf_life_defaults for shelf-life-defaults subcommand."""
        with (
            patch("app.database.create_db_and_tables"),
            patch("app.database.get_engine"),
            patch("app.seed.seed_shelf_life_defaults", return_value=(10, 20)) as mock_seed,
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "shelf-life-defaults"])

            mock_seed.assert_called_once()
            assert result == 0

    def test_seed_testdata_calls_seed_function(self) -> None:
        """Should call seed_testdata for testdata subcommand."""
        with (
            patch("app.database.create_db_and_tables"),
            patch("app.database.get_engine"),
            patch(
                "app.seed.seed_testdata", return_value={"admin": 1, "categories": 5, "locations": 3, "items": 8}
            ) as mock_seed,
        ):
            from app.cli import dispatch_command

            result = dispatch_command(["seed", "testdata"])

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
