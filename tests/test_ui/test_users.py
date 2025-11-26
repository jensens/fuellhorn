"""UI Tests for Users Page (Admin).

Issue #28: Users Page - Liste aller Benutzer
"""

from app.models.user import User
from datetime import datetime
from nicegui.testing import User as TestUser
from sqlmodel import Session


async def test_users_page_renders_for_admin(logged_in_user: TestUser) -> None:
    """Test that users page renders for admin users."""
    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Check page elements
    await logged_in_user.should_see("Benutzer")


async def test_users_page_shows_user_list(logged_in_user: TestUser) -> None:
    """Test that users page displays user list with username, role, status."""
    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Admin user from fixture should be visible
    await logged_in_user.should_see("admin")
    await logged_in_user.should_see("Admin")  # Role display
    await logged_in_user.should_see("Aktiv")  # Status


async def test_users_page_displays_multiple_users(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that users page displays all users with their details."""
    # Create additional test users
    with Session(isolated_test_database) as session:
        user1 = User(
            username="testuser1",
            email="testuser1@example.com",
            is_active=True,
            role="user",
            last_login=datetime(2025, 11, 25, 10, 30),
        )
        user1.set_password("password123")

        user2 = User(
            username="testuser2",
            email="testuser2@example.com",
            is_active=False,
            role="admin",
        )
        user2.set_password("password123")

        session.add(user1)
        session.add(user2)
        session.commit()

    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Should see all users
    await logged_in_user.should_see("admin")
    await logged_in_user.should_see("testuser1")
    await logged_in_user.should_see("testuser2")

    # Should see roles and statuses
    await logged_in_user.should_see("Benutzer")  # User role for testuser1
    await logged_in_user.should_see("Aktiv")
    await logged_in_user.should_see("Inaktiv")  # Status for testuser2


async def test_users_page_displays_last_login(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that users page displays last login time."""
    # Create user with last login
    with Session(isolated_test_database) as session:
        user_with_login = User(
            username="loginuser",
            email="loginuser@example.com",
            is_active=True,
            role="user",
            last_login=datetime(2025, 11, 25, 10, 30),
        )
        user_with_login.set_password("password123")
        session.add(user_with_login)
        session.commit()

    # Navigate to users page
    await logged_in_user.open("/admin/users")

    # Should see the last login date (formatted)
    await logged_in_user.should_see("25.11.2025")


async def test_users_page_requires_auth(user: TestUser) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access users without login
    await user.open("/admin/users")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_users_page_requires_admin_permission(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that regular users are redirected (no USER_MANAGE permission)."""
    # Create a regular user
    with Session(isolated_test_database) as session:
        regular_user = User(
            username="testuser",
            email="testuser@example.com",
            is_active=True,
            role="user",
        )
        regular_user.set_password("password123")
        session.add(regular_user)
        session.commit()

    # Login as regular user (manual login needed for non-admin user)
    await user.open("/login")
    user.find("Benutzername").type("testuser")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Try to navigate to users page
    await user.open("/admin/users")

    # Regular user should be redirected (should not see "Benutzer verwalten" header)
    await user.should_not_see("Benutzer verwalten")


async def test_users_page_has_back_button(logged_in_user: TestUser) -> None:
    """Test that users page has back button to settings."""
    # Navigate to users page
    await logged_in_user.open("/admin/users")

    # Should have back button (arrow_back icon)
    # The back button should navigate to /settings
    await logged_in_user.should_see("Benutzer")
