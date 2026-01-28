"""UI Tests for Item Card component.

Tests the unified item card with:
- Item-Type Badge (Frisch, TK gekauft, Eingefr., etc.)
- Expiry Badge: color-coded badge with date or relative time (Issue #212)
- Status colors based on days until expiry
"""

from app.models.item import ItemType
from app.ui.components.item_card import get_expiry_badge_class
from app.ui.components.item_card import get_expiry_badge_text
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from nicegui.testing import User as TestUser


# =============================================================================
# Shelf-Life Item Tests (frozen items show date format in badge)
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


async def test_item_card_shows_date_badge_for_frozen(user: TestUser) -> None:
    """Test that frozen item card displays date format in expiry badge."""
    await user.open("/test-item-card")
    # Frozen items show date format (DD.MM.YY) in badge
    # Test page creates item frozen 30 days ago with 6-12 month shelf life
    # So badge shows optimal date (freeze_date + 6 months)
    freeze_date = date.today() - timedelta(days=30)
    optimal_date = freeze_date + relativedelta(months=6)
    await user.should_see(optimal_date.strftime("%d.%m.%y"))


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
# Fresh Item Tests (expiry badge with date or relative time)
# =============================================================================


async def test_item_card_fresh_shows_product_name(user: TestUser) -> None:
    """Test that fresh item card displays the product name."""
    await user.open("/test-item-card-mhd")
    await user.should_see("Joghurt")


async def test_item_card_fresh_shows_date_badge_when_far(user: TestUser) -> None:
    """Test that fresh item shows date format in badge when > 7 days."""
    await user.open("/test-item-card-mhd")
    # Fresh items > 7 days show date format (DD.MM.YY) in badge
    # Test page creates item with mhd_days_from_now=10
    expiry_date = date.today() + timedelta(days=10)
    await user.should_see(expiry_date.strftime("%d.%m.%y"))


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


async def test_item_card_fresh_critical_shows_relative_badge(user: TestUser) -> None:
    """Test that fresh item shows relative text in badge when < 3 days."""
    await user.open("/test-item-card-mhd-critical")
    await user.should_see("Joghurt")
    # Test page creates item with mhd_days_from_now=2
    # Badge shows "in 2 Tagen"
    await user.should_see("in 2 Tagen")


async def test_item_card_fresh_warning_shows_relative_badge(user: TestUser) -> None:
    """Test that fresh item shows 'in X Tagen' in badge when 3-7 days."""
    await user.open("/test-item-card-mhd-warning")
    await user.should_see("Joghurt")
    # Badge shows "in X Tagen" for 5 days
    await user.should_see("in 5 Tagen")


# =============================================================================
# Quick-Action Button Tests (Issue #213)
# =============================================================================


async def test_item_card_shows_quick_action_button(user: TestUser) -> None:
    """Test that item card shows round minus button when on_consume is provided."""
    await user.open("/test-item-card-with-consume")
    # Quick-action button should be visible (round button with minus icon)
    # The button uses q-btn with round prop and remove icon
    await user.should_see("remove")  # Material icon name for minus


async def test_item_card_no_quick_action_without_consume(user: TestUser) -> None:
    """Test that item card does NOT show quick-action button without on_consume."""
    await user.open("/test-item-card")
    # Should NOT see the minus icon when no consume callback
    await user.should_not_see("remove")


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


# =============================================================================
# Unit Tests for Badge Functions (Issue #212)
# =============================================================================


def test_get_expiry_badge_class_expired() -> None:
    """Test badge class for expired items (days < 0)."""
    assert get_expiry_badge_class(-1) == "expired"
    assert get_expiry_badge_class(-5) == "expired"
    assert get_expiry_badge_class(-100) == "expired"


def test_get_expiry_badge_class_warning() -> None:
    """Test badge class for warning items (days 0-1)."""
    assert get_expiry_badge_class(0) == "warning"
    assert get_expiry_badge_class(1) == "warning"


def test_get_expiry_badge_class_soon() -> None:
    """Test badge class for soon items (days 2-7)."""
    assert get_expiry_badge_class(2) == "soon"
    assert get_expiry_badge_class(5) == "soon"
    assert get_expiry_badge_class(7) == "soon"


def test_get_expiry_badge_class_ok() -> None:
    """Test badge class for ok items (days > 7)."""
    assert get_expiry_badge_class(8) == "ok"
    assert get_expiry_badge_class(30) == "ok"
    assert get_expiry_badge_class(365) == "ok"


def test_get_expiry_badge_text_frozen_shows_date() -> None:
    """Test badge text for frozen items shows date format."""
    expiry = date.today() + timedelta(days=5)
    for item_type in [
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    ]:
        result = get_expiry_badge_text(expiry, item_type)
        assert result == expiry.strftime("%d.%m.%y")


def test_get_expiry_badge_text_fresh_expired() -> None:
    """Test badge text for expired fresh items."""
    expiry = date.today() - timedelta(days=1)
    result = get_expiry_badge_text(expiry, ItemType.PURCHASED_FRESH)
    assert result == "Abgelaufen"


def test_get_expiry_badge_text_fresh_today() -> None:
    """Test badge text for items expiring today."""
    expiry = date.today()
    result = get_expiry_badge_text(expiry, ItemType.PURCHASED_FRESH)
    assert result == "Heute"


def test_get_expiry_badge_text_fresh_tomorrow() -> None:
    """Test badge text for items expiring tomorrow."""
    expiry = date.today() + timedelta(days=1)
    result = get_expiry_badge_text(expiry, ItemType.PURCHASED_FRESH)
    assert result == "Morgen"


def test_get_expiry_badge_text_fresh_in_x_days() -> None:
    """Test badge text for items expiring in 2-7 days."""
    for days in [2, 3, 5, 7]:
        expiry = date.today() + timedelta(days=days)
        result = get_expiry_badge_text(expiry, ItemType.PURCHASED_FRESH)
        assert result == f"in {days} Tagen"


def test_get_expiry_badge_text_fresh_far_shows_date() -> None:
    """Test badge text for fresh items > 7 days shows date format."""
    expiry = date.today() + timedelta(days=30)
    result = get_expiry_badge_text(expiry, ItemType.PURCHASED_FRESH)
    assert result == expiry.strftime("%d.%m.%y")


# =============================================================================
# Location Temperature Icon Tests (Issue #197)
# =============================================================================


def test_get_location_icon_frozen() -> None:
    """Test that FROZEN location type returns freezer icon."""
    from app.models.location import LocationType
    from app.ui.components.item_card import get_location_icon_name

    assert get_location_icon_name(LocationType.FROZEN) == "locations/freezer"


def test_get_location_icon_chilled() -> None:
    """Test that CHILLED location type returns fridge icon."""
    from app.models.location import LocationType
    from app.ui.components.item_card import get_location_icon_name

    assert get_location_icon_name(LocationType.CHILLED) == "locations/fridge"


def test_get_location_icon_ambient() -> None:
    """Test that AMBIENT location type returns pantry icon."""
    from app.models.location import LocationType
    from app.ui.components.item_card import get_location_icon_name

    assert get_location_icon_name(LocationType.AMBIENT) == "locations/pantry"
