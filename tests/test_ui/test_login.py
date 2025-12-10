"""UI Tests for Login functionality."""

from nicegui.testing import User as TestUser


async def test_login_page_has_all_elements(user: TestUser) -> None:
    """Test that login page renders all required elements."""
    await user.open("/login")

    # Branding
    await user.should_see("Füllhorn")
    await user.should_see("Lebensmittelvorrats-Verwaltung")

    # Form elements
    await user.should_see("Benutzername")
    await user.should_see("Passwort")
    await user.should_see("Anmelden")
    await user.should_see("Angemeldet bleiben")


async def test_root_redirects_to_login_when_not_authenticated(user: TestUser) -> None:
    """Test that / redirects to /login when not authenticated."""
    await user.open("/")
    # Should redirect to login page
    await user.should_see("Füllhorn")
    await user.should_see("Anmelden")


async def test_root_redirects_to_dashboard_when_authenticated(logged_in_user: TestUser) -> None:
    """Test that / redirects to /dashboard when authenticated."""
    await logged_in_user.open("/")
    # Should redirect to dashboard
    await logged_in_user.should_see("Bald abgelaufen")
    await logged_in_user.should_see("Vorrats-Statistik")
