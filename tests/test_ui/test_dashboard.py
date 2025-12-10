"""UI Tests for Dashboard page.

Tests that expiry status is calculated correctly for all item types:
- MHD items (PURCHASED_FRESH, PURCHASED_FROZEN): Use best_before_date directly
- Shelf-life items (HOMEMADE_FROZEN, etc.): Use calculated expiry from freeze_date + shelf life
"""

from nicegui.testing import User as TestUser


# =============================================================================
# Tests for dashboard page with authentication
# =============================================================================


async def test_dashboard_page_loads(logged_in_user: TestUser) -> None:
    """Test that the dashboard page loads correctly."""
    await logged_in_user.open("/dashboard")

    # Should see main sections
    await logged_in_user.should_see("Füllhorn")
    await logged_in_user.should_see("Bald abgelaufen")
    await logged_in_user.should_see("Vorrats-Statistik")
    await logged_in_user.should_see("Schnellfilter")


async def test_dashboard_shows_statistics(logged_in_user: TestUser) -> None:
    """Test that dashboard shows statistics section."""
    await logged_in_user.open("/dashboard")

    # Should see statistics labels
    await logged_in_user.should_see("Artikel")
    await logged_in_user.should_see("Ablauf")


async def test_dashboard_has_user_dropdown(logged_in_user: TestUser) -> None:
    """Test that dashboard shows user dropdown."""
    await logged_in_user.open("/dashboard")

    # Should see admin user in dropdown
    await logged_in_user.should_see("admin")


# =============================================================================
# Tests for correct expiry calculation
# =============================================================================


async def test_dashboard_shelf_life_item_not_expired(user: TestUser) -> None:
    """Test that shelf-life item with future expiry is shown as fresh, not expired.

    Bug #149: Dashboard was showing all items as expired because it used
    best_before_date directly instead of calculating expiry via get_item_expiry_info().

    For HOMEMADE_FROZEN items, best_before_date is the freeze date (in the past),
    but the actual expiry is freeze_date + shelf life months (in the future).
    """
    await user.open("/test-dashboard-shelf-life-ok")
    # Item should NOT be shown as "Abgelaufen" - it's fresh (frozen 30 days ago with 6-12 months shelf life)
    await user.should_not_see("Abgelaufen")


async def test_dashboard_mhd_item_future_not_expired(user: TestUser) -> None:
    """Test that MHD item with future best_before_date is not shown as expired."""
    await user.open("/test-dashboard-mhd-ok")
    await user.should_not_see("Abgelaufen")


async def test_dashboard_mhd_item_expired_shows_correctly(user: TestUser) -> None:
    """Test that MHD item past best_before_date is shown as expired."""
    await user.open("/test-dashboard-mhd-expired")
    await user.should_see("Abgelaufen")


async def test_dashboard_shows_correct_days_for_shelf_life_item(user: TestUser) -> None:
    """Test that days until expiry is calculated from shelf life, not freeze date."""
    await user.open("/test-dashboard-shelf-life-ok")
    # Should show "Läuft ab: in X Tagen" where X is based on optimal date (6 months from freeze)
    # NOT "Abgelaufen" which would happen if using freeze_date directly
    await user.should_see("Läuft ab:")


async def test_dashboard_no_expiring_items_message(user: TestUser) -> None:
    """Test that message is shown when no items are expiring soon."""
    await user.open("/test-dashboard-no-expiring")
    await user.should_see("Keine Artikel laufen in den nächsten 7 Tagen ab")
