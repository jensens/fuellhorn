"""Ausgabe von ``run_migrations()``: Stand vorher/nachher und jede angewendete Revision (Issue #475).

Ohne ``alembic.ini`` hat der Logger ``alembic`` keinen Handler; die Zeilen „Running upgrade …“
gingen verloren. ``fuellhorn migrate`` nennt die Revisionen deshalb selbst.
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
import importlib
import pytest
import sqlalchemy as sa


INITIAL_REVISION = "d34a94a28640"


@pytest.fixture(name="cli_db")
def cli_db_fixture(
    migration_db: tuple[AlembicConfig, sa.Engine], monkeypatch: pytest.MonkeyPatch
) -> tuple[AlembicConfig, ScriptDirectory]:
    """``run_migrations()`` liest die URL über die Klasse ``Config``: auf die Test-DB umbiegen."""
    cfg, _engine = migration_db
    url = cfg.get_main_option("sqlalchemy.url")
    config_module = importlib.import_module("app.config")
    monkeypatch.setattr(config_module.Config, "get_database_url", classmethod(lambda cls: url))
    return cfg, ScriptDirectory.from_config(cfg)


def _run_migrations() -> None:
    from app.cli import run_migrations

    run_migrations()


def test_empty_db_names_every_revision(cli_db: tuple[AlembicConfig, ScriptDirectory], capsys) -> None:
    _cfg, script = cli_db

    _run_migrations()

    out = capsys.readouterr().out
    for revision in script.walk_revisions():
        assert f"{revision.revision} {revision.doc}" in out


def test_empty_db_shows_before_and_after(cli_db: tuple[AlembicConfig, ScriptDirectory], capsys) -> None:
    _cfg, script = cli_db

    _run_migrations()

    assert f"(leer) -> {script.get_current_head()}" in capsys.readouterr().out


def test_pending_migrations_lists_only_applied_ones(cli_db: tuple[AlembicConfig, ScriptDirectory], capsys) -> None:
    cfg, script = cli_db
    command.upgrade(cfg, INITIAL_REVISION)
    capsys.readouterr()

    _run_migrations()

    out = capsys.readouterr().out
    assert f"{INITIAL_REVISION} -> {script.get_current_head()}" in out
    assert f"angewendet: {INITIAL_REVISION}" not in out


def test_pending_migrations_are_listed_in_upgrade_order(cli_db: tuple[AlembicConfig, ScriptDirectory], capsys) -> None:
    cfg, script = cli_db
    command.upgrade(cfg, INITIAL_REVISION)
    capsys.readouterr()

    _run_migrations()

    out = capsys.readouterr().out
    pending = [r.revision for r in script.iterate_revisions("head", INITIAL_REVISION)][::-1]
    assert [out.index(f"angewendet: {rev}") for rev in pending] == sorted(
        out.index(f"angewendet: {rev}") for rev in pending
    )


def test_current_db_reports_up_to_date(cli_db: tuple[AlembicConfig, ScriptDirectory], capsys) -> None:
    cfg, script = cli_db
    command.upgrade(cfg, "head")
    capsys.readouterr()

    _run_migrations()

    assert capsys.readouterr().out.strip() == f"Datenbank ist aktuell ({script.get_current_head()})"
