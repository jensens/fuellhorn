"""Tests: Konfigurationsbereinigung (Issue #374).

- ``SECRET_KEY`` wurde nirgends gelesen, aber beim Import erzwungen.
- ``DB_TYPE`` wurde nicht validiert.
- SQL-Echo hing an ``DEBUG`` und schrieb jedes Statement samt Parametern ins Log.
"""

import importlib
from pathlib import Path
import pytest


def _reload_config(monkeypatch: pytest.MonkeyPatch, **env: str):
    """Lädt ``app.config`` mit kontrollierter Umgebung neu (ohne .env-Datei)."""
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    for key in ("SECRET_KEY", "DB_TYPE", "DEBUG", "SQL_ECHO", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import app.config

    return importlib.reload(app.config)


@pytest.fixture(autouse=True)
def _restore_config(monkeypatch: pytest.MonkeyPatch):
    """Stellt nach jedem Test die reguläre Konfiguration wieder her (erst Umgebung, dann Modul)."""
    yield
    monkeypatch.undo()
    import app.config

    importlib.reload(app.config)


class TestSecretKeyRemoved:
    def test_config_imports_without_secret_key(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Ohne SECRET_KEY startet die Konfiguration (die Variable wurde nie verwendet)."""
        module = _reload_config(monkeypatch, FUELLHORN_DATA_DIR=str(tmp_path))

        assert not hasattr(module.Config, "SECRET_KEY")

    def test_secret_key_is_not_referenced_anywhere_in_app(self) -> None:
        """Akzeptanzkriterium: kein SECRET_KEY mehr im Anwendungscode."""
        app_dir = Path(__file__).resolve().parents[2] / "app"
        hits = [path for path in app_dir.rglob("*.py") if "SECRET_KEY" in path.read_text(encoding="utf-8")]

        assert hits == []


class TestDbTypeValidation:
    def test_invalid_db_type_raises_clear_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="DB_TYPE"):
            _reload_config(monkeypatch, DB_TYPE="mysql", FUELLHORN_DATA_DIR=str(tmp_path))

    @pytest.mark.parametrize("db_type", ["sqlite", "postgresql"])
    def test_valid_db_types_are_accepted(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, db_type: str) -> None:
        module = _reload_config(monkeypatch, DB_TYPE=db_type, FUELLHORN_DATA_DIR=str(tmp_path))

        assert module.Config.DB_TYPE == db_type


class TestSqlEcho:
    def test_debug_alone_does_not_enable_sql_echo(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        module = _reload_config(monkeypatch, DEBUG="true", FUELLHORN_DATA_DIR=str(tmp_path))

        assert module.Config.DEBUG is True
        assert module.Config.SQL_ECHO is False

    def test_sql_echo_env_enables_it(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        module = _reload_config(monkeypatch, SQL_ECHO="true", FUELLHORN_DATA_DIR=str(tmp_path))

        assert module.Config.SQL_ECHO is True

    def test_engine_echo_follows_sql_echo_not_debug(self) -> None:
        """Die Engine loggt SQL nur mit SQL_ECHO, nicht schon im DEBUG-Modus."""
        from app.database import create_app_engine

        class Settings:
            DEBUG: bool = True
            SQL_ECHO: bool = False
            DB_TYPE: str = "sqlite"
            DATABASE_URL: str = "sqlite://"

            def get_database_url(self) -> str:
                return self.DATABASE_URL

        settings = Settings()
        assert not create_app_engine(settings).echo  # type: ignore[arg-type]

        settings.SQL_ECHO = True
        assert create_app_engine(settings).echo  # type: ignore[arg-type]
