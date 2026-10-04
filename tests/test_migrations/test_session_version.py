"""Migrationstests für 6a96c7f23335 (Issue #384): ``users.session_version`` ersetzt ``users.remember_token``.

Bestandsdaten mit gesetztem Remember-Token müssen die Migration überleben und
danach mit Version 0 vom ORM lesbar sein.
"""

from alembic import command
from alembic.config import Config as AlembicConfig
from app.models import User
from datetime import datetime
import sqlalchemy as sa
from sqlmodel import Session
from sqlmodel import select


PREVIOUS_REVISION = "7fc1ce95c5b3"
SESSION_VERSION_REVISION = "6a96c7f23335"
NOW = datetime(2026, 1, 1, 12, 0, 0)

legacy_users_table = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
    sa.column("password_hash", sa.String),
    sa.column("email", sa.String),
    sa.column("role", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("remember_token", sa.String),
    sa.column("created_at", sa.DateTime),
)
new_users_table = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
    sa.column("password_hash", sa.String),
    sa.column("email", sa.String),
    sa.column("role", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("session_version", sa.Integer),
    sa.column("created_at", sa.DateTime),
)


def _column_names(engine: sa.Engine) -> set[str]:
    return {column["name"] for column in sa.inspect(engine).get_columns("users")}


def _insert_legacy_user(engine: sa.Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            legacy_users_table.insert().values(
                id=1,
                username="admin",
                password_hash="hash",
                email="admin@test.local",
                role="admin",
                is_active=True,
                remember_token="altes-token",
                created_at=NOW,
            )
        )


def test_upgrade_adds_session_version_and_drops_remember_token(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    cfg, engine = migration_db
    command.upgrade(cfg, PREVIOUS_REVISION)
    _insert_legacy_user(engine)

    command.upgrade(cfg, "head")

    columns = _column_names(engine)
    assert "session_version" in columns
    assert "remember_token" not in columns
    with Session(engine) as session:
        users = session.exec(select(User)).all()
    assert [(u.username, u.session_version) for u in users] == [("admin", 0)]


def test_downgrade_restores_remember_token(migration_db: tuple[AlembicConfig, sa.Engine]) -> None:
    cfg, engine = migration_db
    command.upgrade(cfg, "head")
    with engine.begin() as conn:
        conn.execute(
            new_users_table.insert().values(
                id=1,
                username="admin",
                password_hash="hash",
                email="admin@test.local",
                role="admin",
                is_active=True,
                session_version=5,
                created_at=NOW,
            )
        )

    command.downgrade(cfg, PREVIOUS_REVISION)

    columns = _column_names(engine)
    assert "remember_token" in columns
    assert "session_version" not in columns
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT count(*) FROM users")).scalar() == 1
