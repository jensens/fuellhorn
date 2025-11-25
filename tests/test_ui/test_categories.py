"""UI Tests for Categories Page (Admin)."""

from app.models.category import Category
from app.models.user import User
from nicegui.testing import User as TestUser
from sqlmodel import Session


async def test_categories_page_renders_for_admin(user: TestUser) -> None:
    """Test that categories page renders for admin users."""
    # Login as admin (created by isolated_test_database fixture)
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Check page elements
    await user.should_see("Kategorien")


async def test_categories_page_shows_empty_state(user: TestUser) -> None:
    """Test that categories page shows empty state when no categories exist."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Should show empty state message
    await user.should_see("Keine Kategorien vorhanden")


async def test_categories_page_displays_categories(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that categories page displays categories with name and color."""
    # Create test categories
    with Session(isolated_test_database) as session:
        cat1 = Category(
            name="Gemüse",
            color="#00FF00",
            created_by=1,  # admin user from fixture
        )
        cat2 = Category(
            name="Fleisch",
            color="#FF0000",
            created_by=1,
        )
        session.add(cat1)
        session.add(cat2)
        session.commit()

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Should see categories
    await user.should_see("Gemüse")
    await user.should_see("Fleisch")


async def test_categories_page_requires_auth(user: TestUser) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access categories without login
    await user.open("/admin/categories")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_categories_page_requires_admin_permission(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that regular users are redirected (no CONFIG_MANAGE permission)."""
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

    # Login as regular user
    await user.open("/login")
    user.find("Benutzername").type("testuser")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Try to navigate to categories page
    await user.open("/admin/categories")

    # Regular user should be redirected to dashboard (should not see "Kategorien" header)
    # They should see the dashboard or a permission error
    await user.should_not_see("Kategorien verwalten")
