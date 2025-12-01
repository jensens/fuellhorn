"""UI Tests for Login functionality."""

from nicegui.testing import User


async def test_login_page_has_all_elements(user: User) -> None:
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
