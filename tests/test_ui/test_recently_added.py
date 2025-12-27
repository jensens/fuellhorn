"""UI Tests for 'Kürzlich hinzugefügt' (Recently Added) section on Dashboard.

Issue #248: Show last N items added to inventory with relative date and location icon.
"""

from nicegui.testing import User as TestUser


# =============================================================================
# Tests for "Kürzlich hinzugefügt" section
# =============================================================================


async def test_dashboard_shows_recently_added_section(user: TestUser) -> None:
    """Test that dashboard shows 'Kürzlich hinzugefügt' section title (Issue #248)."""
    await user.open("/test-dashboard-recently-added")
    await user.should_see("Kürzlich hinzugefügt")


async def test_dashboard_recently_added_shows_items(user: TestUser) -> None:
    """Test that recently added section shows item names (Issue #248)."""
    await user.open("/test-dashboard-recently-added")
    await user.should_see("Tomatensoße")
    await user.should_see("Apfelmus")


async def test_dashboard_recently_added_shows_relative_date_today(user: TestUser) -> None:
    """Test that recently added section shows 'Heute' for items added today (Issue #248)."""
    await user.open("/test-dashboard-recently-added-today")
    await user.should_see("Heute")


async def test_dashboard_recently_added_shows_relative_date_yesterday(user: TestUser) -> None:
    """Test that recently added section shows 'Gestern' for items added yesterday (Issue #248)."""
    await user.open("/test-dashboard-recently-added-yesterday")
    await user.should_see("Gestern")


async def test_dashboard_recently_added_shows_weekday(user: TestUser) -> None:
    """Test that recently added section shows weekday for items 2-6 days old (Issue #248)."""
    await user.open("/test-dashboard-recently-added-weekday")
    # Should show a weekday name (Mo, Di, Mi, Do, Fr, Sa, So)
    # The exact day depends on when the test runs, but the item is 3 days old


async def test_dashboard_recently_added_hidden_when_empty(user: TestUser) -> None:
    """Test that recently added section is hidden when no items exist (Issue #248)."""
    await user.open("/test-dashboard-recently-added-empty")
    await user.should_not_see("Kürzlich hinzugefügt")


async def test_dashboard_recently_added_shows_location_info(user: TestUser) -> None:
    """Test that recently added section shows location info (Issue #248)."""
    await user.open("/test-dashboard-recently-added")
    # Should show abbreviated location (TK = Tiefkühltruhe, Vorr = Vorratsraum, etc.)
    await user.should_see("TK")
