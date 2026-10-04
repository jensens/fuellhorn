"""Tests for application configuration."""

import os
import pytest
from unittest.mock import patch


class TestGetStorageSecret:
    """Tests for get_storage_secret function."""

    def test_returns_secret_when_set(self) -> None:
        """Should return the secret when FUELLHORN_SECRET is set."""
        with patch.dict(os.environ, {"FUELLHORN_SECRET": "test-secret-value"}):
            # Clear the cached import
            import app.config
            import importlib

            importlib.reload(app.config)

            result = app.config.get_storage_secret()
            assert result == "test-secret-value"

    def test_raises_error_when_not_set(self) -> None:
        """Should raise RuntimeError when FUELLHORN_SECRET is not set."""
        # Save current value if exists
        original = os.environ.get("FUELLHORN_SECRET")

        try:
            # Remove the env var
            if "FUELLHORN_SECRET" in os.environ:
                del os.environ["FUELLHORN_SECRET"]

            from app.config import get_storage_secret

            with pytest.raises(RuntimeError, match="FUELLHORN_SECRET environment variable must be set"):
                get_storage_secret()
        finally:
            # Restore original value
            if original:
                os.environ["FUELLHORN_SECRET"] = original


class TestConfigClass:
    """Tests for Config class."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("true", True), ("TRUE", True), (" true ", True), ("1", False), ("yes", False), ("false", False), ("", False)],
    )
    def test_env_flag_parses_truthy_strings(self, monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool) -> None:
        """DEBUG/SQL_ECHO/FUELLHORN_SKIP_MIGRATIONS: nur "true" (Groß-/Kleinschreibung, Leerraum egal) ist wahr."""
        from app.config import _env_flag

        monkeypatch.setenv("FUELLHORN_TEST_FLAG", raw)
        assert _env_flag("FUELLHORN_TEST_FLAG") is expected

    def test_env_flag_defaults_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.config import _env_flag

        monkeypatch.delenv("FUELLHORN_TEST_FLAG", raising=False)
        assert _env_flag("FUELLHORN_TEST_FLAG") is False

    def test_defaults_without_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ohne DEBUG/HOST/PORT in der Umgebung gelten false, 0.0.0.0 und 8080 (Reload wie in test_data_dir)."""
        import app.config
        import importlib

        monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
        for name in ("DEBUG", "HOST", "PORT"):
            monkeypatch.delenv(name, raising=False)
        importlib.reload(app.config)
        try:
            assert app.config.Config.DEBUG is False
            assert app.config.Config.HOST == "0.0.0.0"
            assert app.config.Config.PORT == 8080
        finally:
            monkeypatch.undo()
            importlib.reload(app.config)

    def test_session_max_age_is_int(self) -> None:
        """SESSION_MAX_AGE should be an integer."""
        from app.config import Config

        assert isinstance(Config.SESSION_MAX_AGE, int)

    def test_remember_me_max_age_is_int(self) -> None:
        """REMEMBER_ME_MAX_AGE should be an integer."""
        from app.config import Config

        assert isinstance(Config.REMEMBER_ME_MAX_AGE, int)

    def test_trusted_proxies_empty_by_default(self) -> None:
        """Ohne TRUSTED_PROXIES wird keinem Proxy vertraut (Issue #364)."""
        from app.config import parse_trusted_proxies

        assert parse_trusted_proxies("") == frozenset()

    def test_trusted_proxies_parses_comma_separated_list(self) -> None:
        """Kommagetrennte Liste mit Leerzeichen wird zu einer Menge von IPs."""
        from app.config import parse_trusted_proxies

        assert parse_trusted_proxies(" 10.0.0.1, 10.0.0.2 ,, ") == frozenset({"10.0.0.1", "10.0.0.2"})


class TestGetDatabaseUrl:
    """Tests for get_database_url method."""

    def test_sqlite_url_unchanged(self) -> None:
        """SQLite URLs should remain unchanged."""
        from app.config import Config

        original_db_type = Config.DB_TYPE
        original_url = Config.DATABASE_URL

        try:
            Config.DB_TYPE = "sqlite"
            Config.DATABASE_URL = "sqlite:///test.db"

            result = Config.get_database_url()
            assert result == "sqlite:///test.db"
        finally:
            Config.DB_TYPE = original_db_type
            Config.DATABASE_URL = original_url

    def test_postgresql_url_gets_psycopg_dialect(self) -> None:
        """PostgreSQL URLs should use psycopg3 dialect."""
        from app.config import Config

        original_db_type = Config.DB_TYPE
        original_url = Config.DATABASE_URL

        try:
            Config.DB_TYPE = "postgresql"
            Config.DATABASE_URL = "postgresql://user:pass@localhost/db"

            result = Config.get_database_url()
            assert result == "postgresql+psycopg://user:pass@localhost/db"
        finally:
            Config.DB_TYPE = original_db_type
            Config.DATABASE_URL = original_url

    def test_postgres_heroku_style_url_gets_psycopg_dialect(self) -> None:
        """Heroku-style postgres:// URLs should use psycopg3 dialect."""
        from app.config import Config

        original_db_type = Config.DB_TYPE
        original_url = Config.DATABASE_URL

        try:
            Config.DB_TYPE = "postgresql"
            Config.DATABASE_URL = "postgres://user:pass@localhost/db"

            result = Config.get_database_url()
            assert result == "postgresql+psycopg://user:pass@localhost/db"
        finally:
            Config.DB_TYPE = original_db_type
            Config.DATABASE_URL = original_url

    def test_already_correct_dialect_unchanged(self) -> None:
        """URLs with psycopg dialect should remain unchanged."""
        from app.config import Config

        original_db_type = Config.DB_TYPE
        original_url = Config.DATABASE_URL

        try:
            Config.DB_TYPE = "postgresql"
            Config.DATABASE_URL = "postgresql+psycopg://user:pass@localhost/db"

            result = Config.get_database_url()
            assert result == "postgresql+psycopg://user:pass@localhost/db"
        finally:
            Config.DB_TYPE = original_db_type
            Config.DATABASE_URL = original_url


class TestMaxFileSize:
    """Tests for MAX_FILE_SIZE constant."""

    def test_max_file_size_is_10mb(self) -> None:
        """MAX_FILE_SIZE should be 10 MB."""
        from app.config import MAX_FILE_SIZE

        assert MAX_FILE_SIZE == 10 * 1024 * 1024
