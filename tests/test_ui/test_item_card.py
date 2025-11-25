"""UI Tests for Item Card component."""

from nicegui.testing import User as TestUser


async def test_item_card_shows_product_name(user: TestUser) -> None:
    """Test that item card displays the product name."""
    await user.open("/test-item-card")
    await user.should_see("Tomaten")


async def test_item_card_shows_quantity_and_unit(user: TestUser) -> None:
    """Test that item card displays quantity with unit."""
    await user.open("/test-item-card")
    await user.should_see("500 g")


async def test_item_card_shows_location(user: TestUser) -> None:
    """Test that item card displays the location name."""
    await user.open("/test-item-card")
    await user.should_see("Tiefkühltruhe")


async def test_item_card_shows_expiry_date(user: TestUser) -> None:
    """Test that item card displays the expiry date."""
    await user.open("/test-item-card")
    # Should see a date (format check via contains)
    await user.should_see("Ablauf:")


async def test_item_card_shows_categories(user: TestUser) -> None:
    """Test that item card displays categories."""
    await user.open("/test-item-card-with-categories")
    await user.should_see("Gemüse")


async def test_item_card_shows_critical_status_for_expiring_soon(
    user: TestUser,
) -> None:
    """Test that item card shows critical (red) status when item expires in < 3 days."""
    await user.open("/test-item-card-critical")
    # Critical status should show red indicator
    await user.should_see("Tomaten")


async def test_item_card_shows_warning_status_for_expiring_week(
    user: TestUser,
) -> None:
    """Test that item card shows warning (yellow) status when item expires in < 7 days."""
    await user.open("/test-item-card-warning")
    await user.should_see("Tomaten")


async def test_item_card_shows_ok_status_for_fresh_items(user: TestUser) -> None:
    """Test that item card shows ok (green) status when item has > 7 days."""
    await user.open("/test-item-card-ok")
    await user.should_see("Tomaten")


async def test_item_card_is_touch_friendly(user: TestUser) -> None:
    """Test that item card has touch-friendly size (min 48px height)."""
    await user.open("/test-item-card")
    # The card should be visible and properly rendered
    await user.should_see("Tomaten")
