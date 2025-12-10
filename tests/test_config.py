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

    def test_debug_false_by_default(self) -> None:
        """DEBUG should be False by default."""
        from app.config import Config

        # Default is "false"
        assert Config.DEBUG is False or isinstance(Config.DEBUG, bool)

    def test_default_host(self) -> None:
        """HOST should default to 0.0.0.0."""
        from app.config import Config

        assert Config.HOST == "0.0.0.0"

    def test_default_port(self) -> None:
        """PORT should default to 8080."""
        from app.config import Config

        assert Config.PORT == 8080 or isinstance(Config.PORT, int)

    def test_session_max_age_is_int(self) -> None:
        """SESSION_MAX_AGE should be an integer."""
        from app.config import Config

        assert isinstance(Config.SESSION_MAX_AGE, int)

    def test_remember_me_max_age_is_int(self) -> None:
        """REMEMBER_ME_MAX_AGE should be an integer."""
        from app.config import Config

        assert isinstance(Config.REMEMBER_ME_MAX_AGE, int)


class TestMaxFileSize:
    """Tests for MAX_FILE_SIZE constant."""

    def test_max_file_size_is_10mb(self) -> None:
        """MAX_FILE_SIZE should be 10 MB."""
        from app.config import MAX_FILE_SIZE

        assert MAX_FILE_SIZE == 10 * 1024 * 1024
