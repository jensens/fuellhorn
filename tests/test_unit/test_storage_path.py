"""NiceGUI-Storage (Sitzungen) liegt im Datenverzeichnis (Issue #429).

Vorher schrieb NiceGUI ``.nicegui/`` ins Arbeitsverzeichnis des Containers, das
weder in Helm noch in docker-compose auf einem Volume liegt: jeder Neustart
meldete alle Benutzer ab, "Angemeldet bleiben" hielt nur bis zum nächsten Deploy.
"""

from nicegui import app as nicegui_app
from nicegui.storage import Storage
from pathlib import Path
import pytest


class TestResolveStoragePath:
    def test_defaults_to_dot_nicegui_below_data_dir(self, tmp_path: Path) -> None:
        from app.config import resolve_storage_path

        assert resolve_storage_path(env={}, data_dir=tmp_path / "data") == tmp_path / "data" / ".nicegui"

    def test_env_override_wins(self, tmp_path: Path) -> None:
        from app.config import resolve_storage_path

        result = resolve_storage_path(env={"NICEGUI_STORAGE_PATH": str(tmp_path / "sessions")}, data_dir=tmp_path)

        assert result == tmp_path / "sessions"

    def test_blank_env_is_ignored(self, tmp_path: Path) -> None:
        from app.config import resolve_storage_path

        assert resolve_storage_path(env={"NICEGUI_STORAGE_PATH": " "}, data_dir=tmp_path) == tmp_path / ".nicegui"


class TestConfigureAppStoragePath:
    def test_configure_app_points_nicegui_storage_at_config_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.config
        from app.startup import configure_app

        target = tmp_path / "data" / ".nicegui"
        monkeypatch.setattr(app.config.config, "STORAGE_PATH", target)
        monkeypatch.setattr(Storage, "path", tmp_path / "elsewhere")

        configure_app(nicegui_app)

        assert Storage.path == target
        assert target.is_dir(), "Verzeichnis wird angelegt, damit NiceGUI sofort schreiben kann"
