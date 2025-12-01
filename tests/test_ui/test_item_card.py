"""UI Tests for Item Card component.

Tests the unified item card with:
- Item-Type Badge (Frisch, TK gekauft, Eingefr., etc.)
- Expiry display: "MHD" + date or "Ablauf" + relative time
- Status colors based on days until expiry
"""

from nicegui.testing import User as TestUser


# =============================================================================
# Shelf-Life Item Tests (frozen items show "MHD" + date)
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


async def test_item_card_shows_mhd_label_for_frozen(user: TestUser) -> None:
    """Test that frozen item card displays MHD label."""
    await user.open("/test-item-card")
    await user.should_see("MHD")


async def test_item_card_shows_item_type_badge(user: TestUser) -> None:
    """Test that item card displays item type badge."""
    await user.open("/test-item-card")
    await user.should_see("Selbst eingefr.")


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
# Fresh Item Tests (MHD label or Ablauf with relative time)
# =============================================================================


async def test_item_card_fresh_shows_product_name(user: TestUser) -> None:
    """Test that fresh item card displays the product name."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Joghurt")


async def test_item_card_fresh_shows_mhd_label(user: TestUser) -> None:
    """Test that fresh item card shows MHD label when > 7 days."""
    await user.open("/test-item-card-mhd")
    await user.should_see("MHD")


async def test_item_card_fresh_shows_quantity_and_unit(user: TestUser) -> None:
    """Test that fresh item card displays quantity with unit."""
    await user.open("/test-item-card-mhd")
    await user.should_see("150 g")


async def test_item_card_fresh_shows_location(user: TestUser) -> None:
    """Test that fresh item card displays the location name."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Kühlschrank")


async def test_item_card_fresh_shows_item_type_badge(user: TestUser) -> None:
    """Test that fresh item card shows 'Frisch' badge."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Frisch")


async def test_item_card_fresh_critical_shows_ablauf(user: TestUser) -> None:
    """Test that fresh item shows 'Ablauf' when < 3 days to expiry."""
    await user.open("/test-item-card-mhd-critical")
    await user.should_see("Joghurt")
    await user.should_see("Ablauf")


async def test_item_card_fresh_warning_shows_ablauf(user: TestUser) -> None:
    """Test that fresh item shows 'Ablauf' when 3-7 days to expiry."""
    await user.open("/test-item-card-mhd-warning")
    await user.should_see("Joghurt")
    await user.should_see("Ablauf")


# =============================================================================
# Consume Button Tests
# =============================================================================


async def test_item_card_shows_entnahme_button(user: TestUser) -> None:
    """Test that item card shows 'Entnahme' button when on_consume is provided."""
    await user.open("/test-item-card-with-consume")
    await user.should_see("Entnahme")
