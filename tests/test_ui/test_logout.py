"""UI Tests for Logout functionality."""

from nicegui.testing import User


async def test_mehr_page_shows_logout_button(user: User) -> None:
    """Test that the 'Mehr' (More) page shows a logout button when logged in."""
    # First login
    await user.open("/login")
    # Enter credentials
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    # Click login button
    user.find("Anmelden").click()
    await user.should_see("Willkommen")

    # Navigate to "Mehr" page (settings)
    await user.open("/settings")

    # Should see logout button
    await user.should_see("Abmelden")


async def test_logout_redirects_to_login(user: User) -> None:
    """Test that clicking logout redirects to login page."""
    # First login
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.should_see("Willkommen")

    # Navigate to "Mehr" page
    await user.open("/settings")
    await user.should_see("Abmelden")

    # Click logout
    user.find("Abmelden").click()

    # Should see logout success message
    await user.should_see("Erfolgreich abgemeldet")


async def test_mehr_page_requires_auth(user: User) -> None:
    """Test that the 'Mehr' page requires authentication."""
    # Try to access settings without login
    await user.open("/settings")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_mehr_page_shows_username(user: User) -> None:
    """Test that the 'Mehr' page shows the current user's name."""
    # First login
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.should_see("Willkommen")

    # Navigate to "Mehr" page
    await user.open("/settings")

    # Should see username
    await user.should_see("admin")


async def test_logout_clears_session(user: User) -> None:
    """Test that logout clears session and prevents access to protected pages."""
    # First login
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.should_see("Willkommen")

    # Navigate to "Mehr" page and logout
    await user.open("/settings")
    user.find("Abmelden").click()
    await user.should_see("Erfolgreich abgemeldet")

    # Try to access protected page - should redirect to login
    await user.open("/dashboard")
    await user.should_see("Anmelden")


async def test_logout_clears_session_no_remnants(user: User) -> None:
    """Test that after logout, no session data remains visible."""
    # First login
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.should_see("Willkommen")

    # Navigate to "Mehr" page and logout
    await user.open("/settings")
    user.find("Abmelden").click()
    await user.should_see("Erfolgreich abgemeldet")

    # Try to access "Mehr" page again - should redirect to login
    await user.open("/settings")
    await user.should_see("Anmelden")
