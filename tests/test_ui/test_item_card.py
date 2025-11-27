"""UI Tests for Item Card component.

Tests both shelf-life items (two dates) and MHD items (single date).
"""

from nicegui.testing import User as TestUser


# =============================================================================
# Shelf-Life Item Tests (two dates: optimal + max)
# =============================================================================


async def test_item_card_shows_product_name(user: TestUser) -> None:
    """Test that item card displays the product name."""
    await user.open("/test-item-card")
    await user.should_see("Erbsen")


async def test_item_card_shows_quantity_and_unit(user: TestUser) -> None:
    """Test that item card displays quantity with unit."""
    await user.open("/test-item-card")
    await user.should_see("500 g")


async def test_item_card_shows_location(user: TestUser) -> None:
    """Test that item card displays the location name."""
    await user.open("/test-item-card")
    await user.should_see("Tiefkühltruhe")


async def test_item_card_shows_optimal_date_for_shelf_life(user: TestUser) -> None:
    """Test that shelf-life item card displays optimal date."""
    await user.open("/test-item-card")
    await user.should_see("Optimal bis:")


async def test_item_card_shows_max_date_for_shelf_life(user: TestUser) -> None:
    """Test that shelf-life item card displays max date."""
    await user.open("/test-item-card")
    await user.should_see("Max. bis:")


async def test_item_card_shows_categories(user: TestUser) -> None:
    """Test that item card displays categories."""
    await user.open("/test-item-card-with-categories")
    await user.should_see("Gemüse")


async def test_item_card_shows_critical_status_for_shelf_life(
    user: TestUser,
) -> None:
    """Test that item card shows critical status when close to max date."""
    await user.open("/test-item-card-critical")
    await user.should_see("Erbsen")


async def test_item_card_shows_warning_status_for_shelf_life(
    user: TestUser,
) -> None:
    """Test that item card shows warning status when past optimal but before max."""
    await user.open("/test-item-card-warning")
    await user.should_see("Erbsen")


async def test_item_card_shows_ok_status_for_shelf_life(user: TestUser) -> None:
    """Test that item card shows ok status when before optimal date."""
    await user.open("/test-item-card-ok")
    await user.should_see("Erbsen")


async def test_item_card_is_touch_friendly(user: TestUser) -> None:
    """Test that item card has touch-friendly size (min 48px height)."""
    await user.open("/test-item-card")
    await user.should_see("Erbsen")


# =============================================================================
# MHD Item Tests (single date)
# =============================================================================


async def test_item_card_mhd_shows_product_name(user: TestUser) -> None:
    """Test that MHD item card displays the product name."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Joghurt")


async def test_item_card_mhd_shows_mhd_label(user: TestUser) -> None:
    """Test that MHD item card shows MHD label instead of optimal/max."""
    await user.open("/test-item-card-mhd")
    await user.should_see("MHD:")


async def test_item_card_mhd_shows_quantity_and_unit(user: TestUser) -> None:
    """Test that MHD item card displays quantity with unit."""
    await user.open("/test-item-card-mhd")
    await user.should_see("150 g")


async def test_item_card_mhd_shows_location(user: TestUser) -> None:
    """Test that MHD item card displays the location name."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Kühlschrank")


async def test_item_card_mhd_critical_status(user: TestUser) -> None:
    """Test that MHD item shows critical status when < 3 days to MHD."""
    await user.open("/test-item-card-mhd-critical")
    await user.should_see("Joghurt")
    await user.should_see("MHD:")


async def test_item_card_mhd_warning_status(user: TestUser) -> None:
    """Test that MHD item shows warning status when 3-7 days to MHD."""
    await user.open("/test-item-card-mhd-warning")
    await user.should_see("Joghurt")
    await user.should_see("MHD:")
