"""Pytest configuration and fixtures for Fuellhorn tests."""

from app.models import User
from app.models.category import Category
from app.models.location import Location
from app.models.location import LocationType
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


@pytest.fixture(scope="module")
def _module_engine():
    """One database engine per test module (not per test!).

    This fixture creates the engine and tables once per module, with the
    admin user already created. This saves ~0.5s per test by avoiding:
    - Engine creation per test
    - Table creation per test (create_all)
    - bcrypt password hashing per test (~100ms)

    The isolated_test_database fixture handles per-test cleanup via rollback.
    """
    # Create in-memory test engine with StaticPool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables once
    SQLModel.metadata.create_all(engine)

    # Create admin user once (bcrypt is expensive!)
    with Session(engine) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
        )
        admin.set_password("password123")
        session.add(admin)
        session.commit()

    yield engine

    # Cleanup when module is done
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def isolated_test_database(_module_engine, monkeypatch):
    """Isolated database state for every test using transaction rollback.

    This fixture ensures that:
    1. Each test gets a clean database state
    2. Production database is NEVER touched
    3. Test admin user is always available
    4. Tests run much faster via rollback instead of recreate

    How it works:
    - Uses module-scoped engine (tables + admin already created)
    - Patches app.database.get_engine() before test runs
    - After test: Deletes all data except admin user (rollback pattern)

    This approach is ~5x faster than creating tables per test because:
    - No create_engine() per test
    - No create_all() per test
    - No bcrypt hashing per test (admin exists)
    - DELETE is faster than drop_all + create_all
    """
    from sqlalchemy import text

    # Patch get_engine() to return test engine
    monkeypatch.setattr("app.database.get_engine", lambda: _module_engine)
    monkeypatch.setattr("app.database._engine", _module_engine)

    yield _module_engine

    # Cleanup: Delete all data except admin user
    # Order matters due to foreign key constraints
    with Session(_module_engine) as session:
        session.exec(text("DELETE FROM withdrawal"))
        session.exec(text("DELETE FROM item"))
        session.exec(text("DELETE FROM category_shelf_life"))
        session.exec(text("DELETE FROM category"))
        session.exec(text("DELETE FROM location"))
        session.exec(text("DELETE FROM login_attempt"))
        session.exec(text("DELETE FROM system_settings"))
        session.exec(text("DELETE FROM users WHERE username != 'admin'"))
        session.commit()


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


# ============================================================================
# Shared Test Data Fixtures
# ============================================================================


@pytest.fixture
def standard_categories(isolated_test_database) -> list[Category]:
    """Standard categories for tests.

    Creates 3 categories with fixed IDs (100, 101, 102) to avoid conflicts
    with dynamically created objects.

    Returns:
        List of Category objects: Gemüse, Fleisch, Obst
    """
    with Session(isolated_test_database) as session:
        categories = [
            Category(id=100, name="Gemüse", color="#00FF00", created_by=1),
            Category(id=101, name="Fleisch", color="#FF0000", created_by=1),
            Category(id=102, name="Obst", color="#FFA500", created_by=1),
        ]
        session.add_all(categories)
        session.commit()
        for cat in categories:
            session.refresh(cat)
        return categories


@pytest.fixture
def standard_locations(isolated_test_database) -> list[Location]:
    """Standard locations for tests.

    Creates 3 locations with fixed IDs (100, 101, 102) to avoid conflicts
    with dynamically created objects.

    Returns:
        List of Location objects: Kühlschrank, Tiefkühler, Speisekammer
    """
    with Session(isolated_test_database) as session:
        locations = [
            Location(
                id=100,
                name="Kühlschrank",
                location_type=LocationType.CHILLED,
                color="#0000FF",
                created_by=1,
            ),
            Location(
                id=101,
                name="Tiefkühler",
                location_type=LocationType.FROZEN,
                color="#00FFFF",
                created_by=1,
            ),
            Location(
                id=102,
                name="Speisekammer",
                location_type=LocationType.AMBIENT,
                color="#8B4513",
                created_by=1,
            ),
        ]
        session.add_all(locations)
        session.commit()
        for loc in locations:
            session.refresh(loc)
        return locations


@pytest.fixture
def standard_users(isolated_test_database) -> list[User]:
    """Standard test users for tests.

    Creates 2 additional users with fixed IDs (100, 101) to avoid conflicts.
    Note: Admin user (id=1) already exists from _module_engine.

    Returns:
        List of User objects: testuser1, testuser2
    """
    with Session(isolated_test_database) as session:
        users = []
        user1 = User(
            id=100,
            username="testuser1",
            email="testuser1@example.com",
            is_active=True,
            role="user",
        )
        user1.set_password("password123")
        users.append(user1)

        user2 = User(
            id=101,
            username="testuser2",
            email="testuser2@example.com",
            is_active=False,
            role="admin",
        )
        user2.set_password("password123")
        users.append(user2)

        session.add_all(users)
        session.commit()
        for user in users:
            session.refresh(user)
        return users


@pytest.fixture
def seeded_database(
    standard_categories,
    standard_locations,
    isolated_test_database,
):
    """Fully seeded test database.

    Contains:
    - Admin user (from isolated_test_database)
    - 3 categories (Gemüse, Fleisch, Obst)
    - 3 locations (Kühlschrank, Tiefkühler, Speisekammer)

    Use this when a test needs all standard test data.
    """
    return isolated_test_database
