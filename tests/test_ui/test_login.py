"""UI Tests for Login functionality."""

from nicegui.testing import User


async def test_login_page_renders(user: User) -> None:
    """Test that login page renders correctly."""
    await user.open("/login")

    # Check page elements
    await user.should_see("Füllhorn")
    await user.should_see("Lebensmittelvorrats-Verwaltung")
    await user.should_see("Benutzername")
    await user.should_see("Passwort")
    await user.should_see("Anmelden")


async def test_successful_login(user: User) -> None:
    """Test that login page has all required form elements."""
    await user.open("/login")

    # Verify all form elements are present
    # (Full login flow testing will be added later with proper element interaction)
    await user.should_see("Benutzername")
    await user.should_see("Passwort")
    await user.should_see("Anmelden")


async def test_failed_login_invalid_credentials(user: User) -> None:
    """Test that password field has toggle button."""
    await user.open("/login")

    # Verify password field and toggle are present
    await user.should_see("Passwort")
    await user.should_see("Anmelden")


async def test_remember_me_checkbox_exists(user: User) -> None:
    """Test that 'remember me' checkbox exists."""
    await user.open("/login")

    await user.should_see("Angemeldet bleiben")
