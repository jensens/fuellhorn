"""UI Tests for User Dropdown in Header (Issue #83).

Tests the user dropdown functionality:
- Username is clickable in header
- Dropdown shows: Einstellungen (admin only), Abmelden
- Bottom nav only has 3 items (no more "Mehr")
"""

from nicegui.testing import User as TestUser
import pytest


async def test_header_shows_username(logged_in_user: TestUser) -> None:
    """Test that the header shows the current username."""
    await logged_in_user.open("/dashboard")
    # Username should be visible in header (as button text)
    await logged_in_user.should_see("admin")


async def test_username_opens_dropdown_menu(logged_in_user: TestUser) -> None:
    """Test that clicking username opens a dropdown menu."""
    await logged_in_user.open("/dashboard")

    # Click on the username button to open dropdown
    logged_in_user.find("admin").click()

    # Should see dropdown menu items
    await logged_in_user.should_see("Abmelden")


async def test_dropdown_shows_logout_option(logged_in_user: TestUser) -> None:
    """Test that dropdown shows logout option."""
    await logged_in_user.open("/dashboard")

    # Click on username to open dropdown
    logged_in_user.find("admin").click()

    # Should see "Abmelden" option
    await logged_in_user.should_see("Abmelden")


async def test_dropdown_shows_settings_for_admin(logged_in_user: TestUser) -> None:
    """Test that dropdown shows 'Einstellungen' for admin users."""
    await logged_in_user.open("/dashboard")

    # Click on username to open dropdown
    logged_in_user.find("admin").click()

    # Admin should see "Einstellungen" option
    await logged_in_user.should_see("Einstellungen")


async def test_bottom_nav_has_three_items(logged_in_user: TestUser) -> None:
    """Test that bottom navigation only has 3 items (no 'Mehr')."""
    await logged_in_user.open("/dashboard")

    # Should see the 3 main nav items
    await logged_in_user.should_see("Übersicht")
    await logged_in_user.should_see("Erfassen")
    await logged_in_user.should_see("Vorrat")


async def test_bottom_nav_no_mehr(logged_in_user: TestUser) -> None:
    """Test that 'Mehr' is NOT in bottom navigation."""
    await logged_in_user.open("/dashboard")

    # "Mehr" should not be visible (it was removed)
    await logged_in_user.should_not_see("Mehr")


async def test_old_settings_route_returns_404(logged_in_user: TestUser) -> None:
    """Test that old /settings route returns 404 (route was removed)."""
    # Navigate to old /settings route - should get 404
    # We use try/except because open() raises on non-200 status
    try:
        await logged_in_user.open("/settings")
        # If we get here, the route exists which is wrong
        pytest.fail("Expected /settings to return 404")
    except AssertionError as e:
        # Expected: route returns 404
        assert "404" in str(e)


async def test_dropdown_on_add_item_page(logged_in_user: TestUser) -> None:
    """Test that add item page loads correctly (has close button, not dropdown)."""
    await logged_in_user.open("/items/add")

    # The add item page has a close button, not the standard header
    # Just verify the page loads
    await logged_in_user.should_see("Artikel erfassen")


async def test_admin_settings_page_accessible(logged_in_user: TestUser) -> None:
    """Test that admin settings page is accessible directly."""
    # Navigate directly to admin settings
    await logged_in_user.open("/admin/settings")

    # Should see the settings page content
    await logged_in_user.should_see("Verwaltung")
    await logged_in_user.should_see("Einstellungen")
