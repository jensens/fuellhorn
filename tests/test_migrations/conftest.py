"""Gemeinsame Fixtures für Migrationstests gegen eine echte Datenbank.

Standard ist eine SQLite-Datei im Temp-Verzeichnis. Mit
``MIGRATION_TEST_DATABASE_URL=postgresql://user:pass@host:port/db`` laufen
dieselben Tests gegen PostgreSQL (die Datenbank wird dabei geleert).
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from collections.abc import Iterator
import importlib
import os
from pathlib import Path
import pytest
import sqlalchemy as sa
from sqlmodel import create_engine


ALEMBIC_DIR = Path(__file__).resolve().parents[2] / "app" / "alembic"


def _reset_postgres(cfg: AlembicConfig, engine: sa.Engine) -> None:
    """PostgreSQL leeren: alle Migrationen zurück und verwaiste Enum-Typen entfernen."""
    command.downgrade(cfg, "base")
    with engine.begin() as conn:
        conn.execute(sa.text("DROP TYPE IF EXISTS storagetype, locationtype, itemtype"))


@pytest.fixture(name="migration_db")
def migration_db_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[AlembicConfig, sa.Engine]]:
    """Alembic-Konfiguration und Engine für eine leere Datenbank.

    ``app/alembic/env.py`` holt die URL über ``app.config.config.get_database_url()``.
    Gepatcht wird die aktuell in ``sys.modules`` liegende Instanz, weil andere
    Tests (``tests/test_config.py``) das Modul neu laden.
    """
    url = os.environ.get("MIGRATION_TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'migration.db'}"
    is_postgres = url.startswith("postgres")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    config_module = importlib.import_module("app.config")
    monkeypatch.setattr(config_module.config, "get_database_url", lambda: url)

    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", url)

    engine = create_engine(url)
    if is_postgres:
        _reset_postgres(cfg, engine)
    yield cfg, engine
    if is_postgres:
        _reset_postgres(cfg, engine)
    engine.dispose()
