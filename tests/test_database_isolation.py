"""Verify that tests never touch production database."""

from app.database import get_engine
from app.models import User
from sqlmodel import Session
from sqlmodel import select


def test_database_is_in_memory(isolated_test_database):
    """Verify that test database is in-memory SQLite."""
    engine = get_engine()

    # Check that it's SQLite
    assert "sqlite" in str(engine.url).lower()

    # Check that it's in-memory (no file path)
    assert str(engine.url) == "sqlite://"


def test_database_isolation_between_tests(isolated_test_database):
    """Verify each test gets a fresh database."""
    with Session(isolated_test_database) as session:
        # Count users (should only be test admin from fixture)
        statement = select(User)
        users = session.exec(statement).all()

        # Only the fixture-created admin should exist
        assert len(users) == 1
        assert users[0].username == "admin"


def test_production_db_not_loaded():
    """Verify that production database URL is not used."""
    engine = get_engine()

    # Should NOT be PostgreSQL (production)
    assert "postgresql" not in str(engine.url).lower()

    # Should NOT point to any file
    assert "file:" not in str(engine.url).lower()
    assert ".db" not in str(engine.url).lower()
