"""Pytest configuration and fixtures for Fuellhorn tests."""

from collections.abc import Generator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine

from app.models import User


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create In-Memory SQLite session for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_admin")
def test_admin_fixture(session: Session) -> User:
    """Create admin test user."""
    user = User(
        username="admin",
        email="admin@example.com",
        is_active=True,
        role="admin",
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create regular test user."""
    user = User(
        username="user",
        email="user@example.com",
        is_active=True,
        role="user",
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
