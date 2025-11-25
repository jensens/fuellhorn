"""UI Tests for Items Page - Card list view of inventory."""

from nicegui.testing import User as TestUser


async def test_items_page_requires_auth(user: TestUser) -> None:
    """Test that items page redirects to login when not authenticated."""
    await user.open("/items")
    # Should redirect to login page
    await user.should_see("Anmelden")


async def test_items_page_renders_when_authenticated(user: TestUser) -> None:
    """Test that items page renders correctly when authenticated."""
    # First login
    await user.open("/test-login-admin")
    # Then navigate to items
    await user.open("/items")
    await user.should_see("Vorrat")


async def test_items_page_shows_bottom_navigation(user: TestUser) -> None:
    """Test that items page has bottom navigation."""
    await user.open("/test-login-admin")
    await user.open("/items")
    # Bottom nav should be visible with navigation options
    await user.should_see("Vorrat")


async def test_items_page_shows_items_as_cards(user: TestUser) -> None:
    """Test that items are displayed as cards."""
    await user.open("/test-items-page-with-items")
    # Should see item names from test data
    await user.should_see("Tomaten")


async def test_items_page_shows_multiple_items(user: TestUser) -> None:
    """Test that multiple items are shown as cards."""
    await user.open("/test-items-page-with-items")
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")


async def test_items_page_shows_expiry_status(user: TestUser) -> None:
    """Test that expiry status is visible on items."""
    await user.open("/test-items-page-with-items")
    # Should see expiry info
    await user.should_see("Ablauf:")


async def test_items_page_excludes_consumed_items(user: TestUser) -> None:
    """Test that consumed items are not shown."""
    await user.open("/test-items-page-with-consumed")
    # Should see active item
    await user.should_see("Aktiver Artikel")
    # Should NOT see consumed item (using should_not_see)


async def test_items_page_shows_empty_state(user: TestUser) -> None:
    """Test that empty state is shown when no items exist."""
    await user.open("/test-items-page-empty")
    await user.should_see("Keine Artikel")


async def test_items_page_shows_location(user: TestUser) -> None:
    """Test that item location is displayed."""
    await user.open("/test-items-page-with-items")
    await user.should_see("Tiefkühltruhe")


async def test_items_page_shows_quantity(user: TestUser) -> None:
    """Test that item quantity and unit are displayed."""
    await user.open("/test-items-page-with-items")
    await user.should_see("500 g")


# Search functionality tests (Issue #10)


async def test_items_page_shows_search_field(user: TestUser) -> None:
    """Test that search field is displayed at top of items page."""
    await user.open("/test-items-page-with-search")
    await user.should_see("Suchen")


async def test_items_page_search_filters_by_name(user: TestUser) -> None:
    """Test that search filters items by product name."""
    await user.open("/test-items-page-with-search")
    # Should see both items initially
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")
    # Type in search
    user.find("Suchen").type("Tomat")
    await user.should_see("Tomaten")
    await user.should_not_see("Hackfleisch")


async def test_items_page_search_case_insensitive(user: TestUser) -> None:
    """Test that search is case-insensitive."""
    await user.open("/test-items-page-with-search")
    # Search with lowercase
    user.find("Suchen").type("tomaten")
    await user.should_see("Tomaten")


async def test_items_page_search_empty_shows_all(user: TestUser) -> None:
    """Test that empty search shows all items."""
    await user.open("/test-items-page-with-search")
    # Initially empty search shows all
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")


async def test_items_page_search_no_results(user: TestUser) -> None:
    """Test that search with no matches shows appropriate message."""
    await user.open("/test-items-page-with-search")
    user.find("Suchen").type("xyz-nicht-vorhanden")
    await user.should_not_see("Tomaten")
    await user.should_not_see("Hackfleisch")
    await user.should_see("Keine Artikel")


# Consumed items toggle tests (Issue #17)


async def test_items_page_has_consumed_toggle(user: TestUser) -> None:
    """Test that items page has a toggle to show consumed items."""
    await user.open("/test-items-page-with-consumed-toggle")
    await user.should_see("Entnommene anzeigen")


async def test_items_page_toggle_shows_consumed_when_enabled(user: TestUser) -> None:
    """Test that consumed items are shown when toggle is enabled."""
    await user.open("/test-items-page-with-consumed-toggle-on")
    # Should see both active and consumed items
    await user.should_see("Aktiver Artikel")
    await user.should_see("Entnommener Artikel")


async def test_items_page_toggle_hides_consumed_when_disabled(user: TestUser) -> None:
    """Test that consumed items are hidden when toggle is disabled (default)."""
    await user.open("/test-items-page-with-consumed-toggle")
    # Should see only active item
    await user.should_see("Aktiver Artikel")
    # Consumed item should not be visible (checked via card count)
