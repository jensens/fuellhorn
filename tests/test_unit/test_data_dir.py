"""Tests: Datenverzeichnis und SQLite-Pfad (Issue #371).

Vorher lag ``DATA_DIR`` relativ zum Paket (``app/..``), im installierten Wheel
also in ``site-packages``. Im Container landete die SQLite-Datei damit außerhalb
des gemounteten Volumes und war nach jedem Neustart weg.
"""

import importlib
import os
from pathlib import Path
import pytest


class TestResolveDataDir:
    """``resolve_data_dir`` bestimmt das Datenverzeichnis aus Umgebung und Arbeitsverzeichnis."""

    def test_defaults_to_data_below_cwd(self, tmp_path: Path) -> None:
        from app.config import resolve_data_dir

        assert resolve_data_dir(env={}, cwd=tmp_path) == tmp_path / "data"

    def test_uses_fuellhorn_data_dir_when_set(self, tmp_path: Path) -> None:
        from app.config import resolve_data_dir

        result = resolve_data_dir(env={"FUELLHORN_DATA_DIR": str(tmp_path / "store")}, cwd=tmp_path)

        assert result == tmp_path / "store"

    def test_ignores_empty_fuellhorn_data_dir(self, tmp_path: Path) -> None:
        from app.config import resolve_data_dir

        assert resolve_data_dir(env={"FUELLHORN_DATA_DIR": "  "}, cwd=tmp_path) == tmp_path / "data"

    def test_is_not_relative_to_the_package(self, tmp_path: Path) -> None:
        """Der Paketpfad (site-packages im Wheel) darf keine Rolle mehr spielen."""
        import app.config

        package_root = Path(app.config.__file__).resolve().parent.parent
        result = app.config.resolve_data_dir(env={}, cwd=tmp_path)

        assert not result.is_relative_to(package_root)
        assert result == tmp_path / "data"


class TestEnsureSqliteDirectory:
    """``ensure_sqlite_directory`` legt das Verzeichnis der SQLite-Datei an."""

    def test_creates_missing_parent_directories(self, tmp_path: Path) -> None:
        from app.config import ensure_sqlite_directory

        target = tmp_path / "nested" / "deeper" / "fuellhorn.db"

        ensure_sqlite_directory(f"sqlite:///{target}")

        assert target.parent.is_dir()

    def test_relative_url_is_resolved_against_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.config import ensure_sqlite_directory

        monkeypatch.chdir(tmp_path)

        ensure_sqlite_directory("sqlite:///data/fuellhorn.db")

        assert (tmp_path / "data").is_dir()

    def test_ignores_in_memory_database(self) -> None:
        from app.config import ensure_sqlite_directory

        ensure_sqlite_directory("sqlite://")
        ensure_sqlite_directory("sqlite:///:memory:")

    @pytest.mark.skipif(os.geteuid() == 0, reason="root darf überall schreiben")
    def test_raises_clear_error_when_directory_is_not_writable(self, tmp_path: Path) -> None:
        from app.config import ensure_sqlite_directory

        locked = tmp_path / "locked"
        locked.mkdir()
        locked.chmod(0o500)
        try:
            with pytest.raises(RuntimeError, match="FUELLHORN_DATA_DIR"):
                ensure_sqlite_directory(f"sqlite:///{locked / 'data' / 'fuellhorn.db'}")
        finally:
            locked.chmod(0o700)


class TestConfigDatabaseUrl:
    """``Config.get_database_url`` nutzt das Datenverzeichnis aus der Umgebung."""

    def test_sqlite_default_lives_in_fuellhorn_data_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        data_dir = tmp_path / "volume"
        monkeypatch.setenv("FUELLHORN_DATA_DIR", str(data_dir))
        monkeypatch.setenv("DB_TYPE", "sqlite")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)

        import app.config

        importlib.reload(app.config)
        try:
            url = app.config.Config.get_database_url()
        finally:
            monkeypatch.undo()
            importlib.reload(app.config)

        assert url == f"sqlite:///{data_dir / 'fuellhorn.db'}"
        assert data_dir.is_dir()

    def test_sqlite_default_without_env_lives_below_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("FUELLHORN_DATA_DIR", raising=False)
        monkeypatch.setenv("DB_TYPE", "sqlite")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)

        import app.config

        importlib.reload(app.config)
        try:
            url = app.config.Config.get_database_url()
        finally:
            monkeypatch.undo()
            importlib.reload(app.config)

        assert url == f"sqlite:///{tmp_path / 'data' / 'fuellhorn.db'}"
