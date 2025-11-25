"""Pytest configuration and fixtures for Fuellhorn tests."""

from app.models import User
from collections.abc import Generator
import os
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
import sys


# Set TESTING environment variable so main.py imports test pages
os.environ["TESTING"] = "true"


# ============================================================================
# NiceGUI Testing Plugin
# ============================================================================

pytest_plugins = ["nicegui.testing.plugin"]


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


# ============================================================================
# Database Isolation for UI Tests
# ============================================================================


@pytest.fixture(scope="function", autouse=True)
def isolated_test_database(monkeypatch):
    """Isolated In-Memory database for every UI test.

    This fixture ensures that:
    1. Each test gets a fresh, empty in-memory SQLite database
    2. Production database is NEVER touched
    3. Test admin user is automatically created
    4. Tests run 10-100x faster than file-based DBs

    How it works:
    - Patches app.database.get_engine() before NiceGUI starts
    - Creates in-memory engine with StaticPool
    - Creates all tables from SQLModel metadata
    - Creates admin test user for authentication

    Scope: function (fresh DB per test)
    Autouse: True (applies to ALL tests, including UI tests)
    """
    # Create in-memory test engine
    test_engine = create_engine(
        "sqlite://",  # In-memory SQLite
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Reuse connection across threads
    )

    # Patch get_engine() to return test engine
    monkeypatch.setattr("app.database.get_engine", lambda: test_engine)

    # Also reset the global _engine variable
    monkeypatch.setattr("app.database._engine", test_engine)

    # Create all tables
    SQLModel.metadata.create_all(test_engine)

    # Create test admin user (required for UI tests)
    with Session(test_engine) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
        )
        admin.set_password("password123")
        session.add(admin)
        session.commit()

    yield test_engine

    # Cleanup: Drop all tables
    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()


# ============================================================================
# UI Package Cleanup (Route Re-registration)
# ============================================================================


@pytest.fixture(scope="function", autouse=True)
def cleanup_ui_packages():
    """Remove UI package modules after each test.

    This fixture ensures that:
    1. Routes are correctly re-registered between tests
    2. No 404 errors due to stale route registrations
    3. Parent packages are properly cleaned up

    Why this is needed:
    - NiceGUI uses runpy.run_path() to load main.py
    - Routes are registered globally in NiceGUI
    - Without cleanup, routes from previous tests persist
    - This causes conflicts and 404 errors

    Solution:
    - Remove app.ui.* modules from sys.modules
    - Forces Python to re-import and re-register routes

    Scope: function (cleanup after each test)
    Autouse: True (applies to ALL tests)
    """
    yield  # Run test first

    # Cleanup after test
    modules_to_remove = [key for key in sys.modules.keys() if key.startswith("app.ui") or key.startswith("app.api")]

    for module in modules_to_remove:
        del sys.modules[module]


# ============================================================================
# Pre-Authenticated User Fixture (for faster UI tests)
# ============================================================================


@pytest.fixture
async def logged_in_user(user):
    """Return a pre-authenticated NiceGUI test user.

    This fixture logs in the user via /test-login-admin before the test runs,
    saving ~3 seconds per test compared to manual login (typing username/password).

    Usage:
        async def test_something(logged_in_user) -> None:
            await logged_in_user.open("/items")
            await logged_in_user.should_see("Vorrat")

    For direct navigation with login, use the ?next= parameter:
        await user.open("/test-login-admin?next=/items")
    """
    await user.open("/test-login-admin")
    return user


# ============================================================================
# User Fixtures
# ============================================================================


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
