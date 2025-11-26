"""UI Tests for Logout functionality.

Updated for Issue #83: Logout is now via user dropdown in header.
"""

from nicegui.testing import User


async def test_dashboard_shows_username(logged_in_user: User) -> None:
    """Test that the dashboard shows the current user's name in header."""
    # Navigate to dashboard - already logged in via fixture
    await logged_in_user.open("/dashboard")

    # Should see username in header (as button)
    await logged_in_user.should_see("admin")


async def test_logout_option_visible_in_dropdown(logged_in_user: User) -> None:
    """Test that clicking username shows logout option in dropdown."""
    # Navigate to dashboard - already logged in via fixture
    await logged_in_user.open("/dashboard")

    # Click on username to open dropdown
    logged_in_user.find("admin").click()

    # Should see "Abmelden" option in dropdown
    await logged_in_user.should_see("Abmelden")
