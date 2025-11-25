"""UI Tests for Logout functionality."""

from nicegui.testing import User


async def test_mehr_page_shows_logout_button(logged_in_user: User) -> None:
    """Test that the 'Mehr' (More) page shows a logout button when logged in."""
    # Navigate to "Mehr" page (settings) - already logged in via fixture
    await logged_in_user.open("/settings")

    # Should see logout button
    await logged_in_user.should_see("Abmelden")


async def test_logout_redirects_to_login(logged_in_user: User) -> None:
    """Test that clicking logout redirects to login page."""
    # Navigate to "Mehr" page - already logged in via fixture
    await logged_in_user.open("/settings")
    await logged_in_user.should_see("Abmelden")

    # Click logout
    logged_in_user.find("Abmelden").click()

    # Should see logout success message
    await logged_in_user.should_see("Erfolgreich abgemeldet")


async def test_mehr_page_requires_auth(user: User) -> None:
    """Test that the 'Mehr' page requires authentication."""
    # Try to access settings without login
    await user.open("/settings")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_mehr_page_shows_username(logged_in_user: User) -> None:
    """Test that the 'Mehr' page shows the current user's name."""
    # Navigate to "Mehr" page - already logged in via fixture
    await logged_in_user.open("/settings")

    # Should see username
    await logged_in_user.should_see("admin")


async def test_logout_clears_session(logged_in_user: User) -> None:
    """Test that logout clears session and prevents access to protected pages."""
    # Navigate to "Mehr" page and logout - already logged in via fixture
    await logged_in_user.open("/settings")
    logged_in_user.find("Abmelden").click()
    await logged_in_user.should_see("Erfolgreich abgemeldet")

    # Try to access protected page - should redirect to login
    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Anmelden")


async def test_logout_clears_session_no_remnants(logged_in_user: User) -> None:
    """Test that after logout, no session data remains visible."""
    # Navigate to "Mehr" page and logout - already logged in via fixture
    await logged_in_user.open("/settings")
    logged_in_user.find("Abmelden").click()
    await logged_in_user.should_see("Erfolgreich abgemeldet")

    # Try to access "Mehr" page again - should redirect to login
    await logged_in_user.open("/settings")
    await logged_in_user.should_see("Anmelden")
