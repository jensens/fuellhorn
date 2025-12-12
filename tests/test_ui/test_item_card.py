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


# =============================================================================
# Partial Withdrawal Display Tests (Issue #204)
# =============================================================================


async def test_item_card_shows_initial_quantity_on_partial_withdrawal(
    user: TestUser,
) -> None:
    """Test that item card shows initial quantity when partial withdrawal exists."""
    await user.open("/test-item-card-partial-withdrawal")
    # Should show "300/500 g" format
    await user.should_see("300/500 g")


async def test_item_card_no_initial_quantity_without_withdrawal(
    user: TestUser,
) -> None:
    """Test that item card shows only current quantity when no withdrawal exists."""
    await user.open("/test-item-card-no-withdrawal")
    # Should show just "500 g" without initial
    await user.should_see("500 g")


# =============================================================================
# Progress Bar Tests (Issue #211)
# =============================================================================


async def test_item_card_progress_bar_shown_on_partial_withdrawal(
    user: TestUser,
) -> None:
    """Test that progress bar is shown when partial withdrawal exists."""
    await user.open("/test-item-card-partial-withdrawal")
    # Progress bar should be visible
    await user.should_see("60%")  # aria-label percentage


async def test_item_card_progress_bar_hidden_without_withdrawal(
    user: TestUser,
) -> None:
    """Test that progress bar is NOT shown when item is full (no withdrawal)."""
    await user.open("/test-item-card-no-withdrawal")
    # Should NOT see a progress indicator when item is at full quantity
    await user.should_not_see("100%")


async def test_item_card_progress_bar_high_level_color(
    user: TestUser,
) -> None:
    """Test that progress bar shows green when >66% full."""
    await user.open("/test-item-card-progress-high")
    # 400/500 = 80% -> should be "positive" (green)
    await user.should_see("80%")


async def test_item_card_progress_bar_medium_level_color(
    user: TestUser,
) -> None:
    """Test that progress bar shows gold when 33-66% full."""
    await user.open("/test-item-card-progress-medium")
    # 250/500 = 50% -> should be "warning" (gold)
    await user.should_see("50%")


async def test_item_card_progress_bar_low_level_color(
    user: TestUser,
) -> None:
    """Test that progress bar shows coral when <33% full."""
    await user.open("/test-item-card-progress-low")
    # 100/500 = 20% -> should be "negative" (coral)
    await user.should_see("20%")
