"""Tests dürfen die konfigurierte Datenbank nie anfassen (Issue #392).

Vorher prüfte diese Datei nur, dass der Monkeypatch greift. Jetzt wird negativ
formuliert: Schreiben über ``get_session()`` landet in der In-Memory-Engine, die
Datei hinter ``DATABASE_URL`` entsteht nicht.
"""

from app.config import Config
from app.database import get_engine
from app.database import get_session
from app.models import User
from pathlib import Path
from sqlmodel import Session
from sqlmodel import select


def test_engine_under_test_is_not_the_configured_database(isolated_test_database) -> None:
    engine = get_engine()

    assert str(engine.url) == "sqlite://"
    assert str(engine.url) != Config.DATABASE_URL


def test_writes_via_get_session_never_create_the_configured_database_file(isolated_test_database) -> None:
    configured = Config.DATABASE_URL
    assert configured.startswith("sqlite:///"), "tests/conftest.py setzt eine Wegwerf-Datei pro Prozess"
    db_file = Path(configured.removeprefix("sqlite:///"))

    with next(get_session()) as session:
        user = User(username="probe", email="probe@test.local", role="user", is_active=True)
        user.set_password("irrelevant-12")
        session.add(user)
        session.commit()

    with Session(isolated_test_database) as session:
        assert session.exec(select(User).where(User.username == "probe")).one()
    assert not db_file.exists()


def test_each_test_starts_with_only_the_admin(isolated_test_database) -> None:
    with Session(isolated_test_database) as session:
        users = session.exec(select(User)).all()

    assert [user.username for user in users] == ["admin"]
