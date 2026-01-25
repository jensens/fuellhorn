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
            patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}),
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
        """Should set sqlalchemy.url from DATABASE_URL env var."""
        test_db_url = "postgresql://user:pass@localhost/testdb"

        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch.dict(os.environ, {"DATABASE_URL": test_db_url}),
        ):
            from app.cli import run_migrations

            run_migrations()

            # Get the config passed to upgrade
            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            assert config.get_main_option("sqlalchemy.url") == test_db_url

    def test_uses_empty_string_when_database_url_not_set(self) -> None:
        """Should use empty string when DATABASE_URL is not set."""
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)

        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch.dict(os.environ, env, clear=True),
        ):
            from app.cli import run_migrations

            run_migrations()

            call_args = mock_upgrade.call_args
            config = call_args[0][0]

            assert config.get_main_option("sqlalchemy.url") == ""

    def test_calls_upgrade_to_head(self) -> None:
        """Should call alembic upgrade to 'head'."""
        with (
            patch("alembic.command.upgrade") as mock_upgrade,
            patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}),
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
