"""Tests: fuellhorn seed (Issue #376).

- ``seed`` legte Tabellen per ``create_all`` an; auf einer frischen Datenbank fehlte
  danach ``alembic_version`` und ``alembic upgrade head`` scheiterte.
- ``seed testdata`` legt ``admin/admin123`` an und darf in Produktion nicht ohne
  ausdrückliche Bestätigung laufen.
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from collections.abc import Iterator
import importlib
from pathlib import Path
import pytest
import sqlalchemy as sa
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_DIR = PROJECT_ROOT / "app" / "alembic"
SEED_SCRIPT = PROJECT_ROOT / "scripts" / "seed_testdata.py"


@pytest.fixture(name="fresh_sqlite")
def fresh_sqlite_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Leere SQLite-Datei als Anwendungsdatenbank.

    Config und Alembic-``env.py`` werden auf die Datei umgebogen. ``get_engine`` wird
    explizit ersetzt, weil die autouse-Fixture ``isolated_test_database`` es sonst auf
    die In-Memory-Testdatenbank zeigen lässt.
    """
    import app.database

    url = f"sqlite:///{tmp_path / 'seed.db'}"
    config_module = importlib.import_module("app.config")
    monkeypatch.setattr(config_module.config, "get_database_url", lambda: url)
    for config_class in {config_module.Config, type(app.database.config)}:
        monkeypatch.setattr(config_class, "DB_TYPE", "sqlite")
        monkeypatch.setattr(config_class, "DATABASE_URL", url)
    engine = app.database.create_app_engine()
    monkeypatch.setattr(app.database, "get_engine", lambda: engine)
    yield url
    engine.dispose()


def _alembic_config(url: str) -> AlembicConfig:
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


class TestSeedUsesMigrations:
    def test_shelf_life_defaults_on_empty_db_leaves_alembic_at_head(self, fresh_sqlite: str) -> None:
        """Nach dem Seed ist die Datenbank migriert; ein weiteres upgrade head ist ein No-op."""
        from app.cli import dispatch_command

        assert dispatch_command(["seed", "shelf-life-defaults"]) == 0

        command.upgrade(_alembic_config(fresh_sqlite), "head")
        engine = sa.create_engine(fresh_sqlite)
        with engine.connect() as conn:
            version = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
            categories = conn.execute(sa.text("SELECT COUNT(*) FROM category")).scalar_one()
        engine.dispose()

        assert version
        assert categories > 0


class TestTestdataGuard:
    def test_testdata_without_debug_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import app.cli
        import app.config

        monkeypatch.setattr(app.config.config, "DEBUG", False)
        with patch("app.seed.seed_testdata") as mock_seed, patch("app.cli.run_migrations"):
            result = app.cli.dispatch_command(["seed", "testdata"])

        assert result == 1
        mock_seed.assert_not_called()
        assert "--i-know-this-is-dev" in capsys.readouterr().out

    def test_testdata_runs_with_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import app.cli
        import app.config

        monkeypatch.setattr(app.config.config, "DEBUG", True)
        with (
            patch("app.cli.run_migrations"),
            patch("app.database.get_engine"),
            patch(
                "app.seed.seed_testdata", return_value={"admin": 1, "categories": 1, "locations": 1, "items": 1}
            ) as mock_seed,
        ):
            result = app.cli.dispatch_command(["seed", "testdata"])

        assert result == 0
        mock_seed.assert_called_once()

    def test_testdata_runs_with_explicit_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import app.cli
        import app.config

        monkeypatch.setattr(app.config.config, "DEBUG", False)
        with (
            patch("app.cli.run_migrations"),
            patch("app.database.get_engine"),
            patch(
                "app.seed.seed_testdata", return_value={"admin": 0, "categories": 0, "locations": 0, "items": 0}
            ) as mock_seed,
        ):
            result = app.cli.dispatch_command(["seed", "testdata", "--i-know-this-is-dev"])

        assert result == 0
        mock_seed.assert_called_once()


def test_seed_testdata_script_is_a_thin_wrapper() -> None:
    """scripts/seed_testdata.py enthält keine eigene Seed-Logik mehr (Akzeptanzkriterium #376)."""
    source = SEED_SCRIPT.read_text(encoding="utf-8")

    assert "from app.seed import seed_testdata" in source
    assert "def seed_admin" not in source
    assert "def seed_categories" not in source
    assert "def seed_items" not in source


def test_seed_shelf_life_defaults_script_is_a_thin_wrapper() -> None:
    """scripts/seed_shelf_life_defaults.py baut die Seed-Schleife nicht nach (#460)."""
    source = (PROJECT_ROOT / "scripts" / "seed_shelf_life_defaults.py").read_text(encoding="utf-8")

    assert "from app.seed import seed_shelf_life_defaults" in source
    assert "get_or_create_category" not in source
    assert "create_or_update_shelf_life" not in source
