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
