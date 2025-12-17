"""Tests for item_service."""

from app.models import ItemType
from app.models import LocationType
from app.models import User
from app.services import category_service
from app.services import item_service
from app.services import location_service
from datetime import date
from datetime import timedelta
import pytest
from sqlmodel import Session


def test_get_all_items(session: Session, test_admin: User) -> None:
    """Test getting all items."""
    location = location_service.create_location(
        session=session,
        name="Vorratsraum",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Eingemachtes",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item_service.create_item(
        session=session,
        product_name="Tomaten",
        best_before_date=date(2025, 6, 1),
        quantity=6,
        unit="Stück",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )
    item_service.create_item(
        session=session,
        product_name="Bohnen",
        best_before_date=date(2025, 12, 1),
        quantity=4,
        unit="Dosen",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    items = item_service.get_all_items(session)

    assert len(items) == 2


def test_get_item(session: Session, test_admin: User) -> None:
    """Test getting an item by ID."""
    location = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Marmelade",
        created_by=test_admin.id,
    )

    assert category.id is not None

    created = item_service.create_item(
        session=session,
        product_name="Marmelade",
        best_before_date=date(2025, 3, 1),
        quantity=3,
        unit="Gläser",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    item = item_service.get_item(session, created.id)

    assert item.id == created.id
    assert item.product_name == "Marmelade"


def test_get_item_not_found_fails(session: Session) -> None:
    """Test that getting non-existent item fails."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.get_item(session, 999)


def test_update_item(session: Session, test_admin: User) -> None:
    """Test updating an item."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    created = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2024, 1, 1),
        quantity=1.0,
        unit="kg",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    updated = item_service.update_item(
        session=session,
        id=created.id,
        quantity=0.5,
        notes="Halbe Packung verwendet",
    )

    assert updated.quantity == 0.5
    assert updated.notes == "Halbe Packung verwendet"
    assert updated.product_name == "Erbsen"  # Unchanged


def test_mark_item_consumed(session: Session, test_admin: User) -> None:
    """Test marking an item as consumed."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milch",
        created_by=test_admin.id,
    )

    assert category.id is not None

    created = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1.0,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    updated = item_service.mark_item_consumed(session, created.id)

    assert updated.is_consumed is True


def test_delete_item(session: Session, test_admin: User) -> None:
    """Test deleting an item."""
    location = location_service.create_location(
        session=session,
        name="Vorratsraum",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Konserven",
        created_by=test_admin.id,
    )

    assert category.id is not None

    created = item_service.create_item(
        session=session,
        product_name="Alte Konserve",
        best_before_date=date(2020, 1, 1),
        quantity=1,
        unit="Dose",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    item_service.delete_item(session, created.id)

    with pytest.raises(ValueError, match="Item with id .* not found"):
        item_service.get_item(session, created.id)


def test_get_items_by_location(session: Session, test_admin: User) -> None:
    """Test getting items filtered by location."""
    location1 = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    location2 = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item_service.create_item(
        session=session,
        product_name="Eis",
        best_before_date=date(2025, 1, 1),
        quantity=1,
        unit="Packung",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location1.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )
    item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location2.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    items = item_service.get_items_by_location(session, location1.id)

    assert len(items) == 1
    assert items[0].product_name == "Eis"


def test_get_items_expiring_soon(session: Session, test_admin: User) -> None:
    """Test getting items expiring within X days."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Frische",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Item expiring in 5 days
    item_service.create_item(
        session=session,
        product_name="Joghurt",
        best_before_date=date.today() + timedelta(days=5),
        quantity=1,
        unit="Becher",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )
    # Item expiring in 20 days
    item_service.create_item(
        session=session,
        product_name="Käse",
        best_before_date=date.today() + timedelta(days=20),
        quantity=1,
        unit="Packung",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    items = item_service.get_items_expiring_soon(session, days=7)

    assert len(items) == 1
    assert items[0].product_name == "Joghurt"


# =============================================================================
# Partial Withdrawal Tests (Issue #16)
# =============================================================================


def test_withdraw_partial_reduces_quantity(session: Session, test_admin: User) -> None:
    """Test: Partial withdrawal reduces item quantity."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    updated = item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=200,
    )

    assert updated.quantity == 300
    assert updated.is_consumed is False


def test_withdraw_partial_complete_marks_consumed(session: Session, test_admin: User) -> None:
    """Test: Withdrawing all quantity marks item as consumed."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    updated = item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=500,
    )

    assert updated.quantity == 0
    assert updated.is_consumed is True


def test_withdraw_partial_exceeds_quantity_fails(session: Session, test_admin: User) -> None:
    """Test: Withdrawing more than available quantity fails."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    with pytest.raises(ValueError, match="Cannot withdraw more than available"):
        item_service.withdraw_partial(
            session=session,
            item_id=item.id,
            withdraw_quantity=600,
        )


def test_withdraw_partial_zero_quantity_fails(session: Session, test_admin: User) -> None:
    """Test: Withdrawing zero quantity fails."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    with pytest.raises(ValueError, match="Withdraw quantity must be positive"):
        item_service.withdraw_partial(
            session=session,
            item_id=item.id,
            withdraw_quantity=0,
        )


def test_withdraw_partial_negative_quantity_fails(session: Session, test_admin: User) -> None:
    """Test: Withdrawing negative quantity fails."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    with pytest.raises(ValueError, match="Withdraw quantity must be positive"):
        item_service.withdraw_partial(
            session=session,
            item_id=item.id,
            withdraw_quantity=-100,
        )


def test_withdraw_partial_item_not_found_fails(session: Session) -> None:
    """Test: Withdrawing from non-existent item fails."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.withdraw_partial(
            session=session,
            item_id=999,
            withdraw_quantity=100,
        )


def test_withdraw_partial_consumed_item_fails(session: Session, test_admin: User) -> None:
    """Test: Withdrawing from already consumed item fails."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Mark as consumed first
    item_service.mark_item_consumed(session, item.id)

    with pytest.raises(ValueError, match="Item is already consumed"):
        item_service.withdraw_partial(
            session=session,
            item_id=item.id,
            withdraw_quantity=200,
        )


# =============================================================================
# Withdrawal Tracking Tests (Issue #97)
# =============================================================================


def test_withdraw_partial_creates_withdrawal_entry(session: Session, test_admin: User) -> None:
    """Test: Partial withdrawal creates a Withdrawal record."""

    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Withdraw partial quantity
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=200,
        user_id=test_admin.id,
    )

    # Check withdrawal entry was created
    withdrawals = item_service.get_withdrawal_history(session, item.id)
    assert len(withdrawals) == 1
    assert withdrawals[0].item_id == item.id
    assert withdrawals[0].quantity == 200
    assert withdrawals[0].withdrawn_by == test_admin.id
    assert withdrawals[0].withdrawn_at is not None


def test_mark_item_consumed_creates_withdrawal_entry(session: Session, test_admin: User) -> None:
    """Test: Marking item as consumed creates a Withdrawal record with full quantity."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milch",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1.0,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    item_service.mark_item_consumed(session, item.id, user_id=test_admin.id)

    # Check withdrawal entry was created
    withdrawals = item_service.get_withdrawal_history(session, item.id)
    assert len(withdrawals) == 1
    assert withdrawals[0].item_id == item.id
    assert withdrawals[0].quantity == 1.0  # Full quantity
    assert withdrawals[0].withdrawn_by == test_admin.id


def test_get_withdrawal_history_returns_all_entries(session: Session, test_admin: User) -> None:
    """Test: Withdrawal history returns all entries in chronological order."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Multiple withdrawals
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=100,
        user_id=test_admin.id,
    )
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=150,
        user_id=test_admin.id,
    )

    withdrawals = item_service.get_withdrawal_history(session, item.id)
    assert len(withdrawals) == 2
    assert withdrawals[0].quantity == 100
    assert withdrawals[1].quantity == 150


def test_get_withdrawal_history_empty_for_new_item(session: Session, test_admin: User) -> None:
    """Test: New item has empty withdrawal history."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Obst",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Äpfel",
        best_before_date=date(2024, 12, 20),
        quantity=5,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    withdrawals = item_service.get_withdrawal_history(session, item.id)
    assert len(withdrawals) == 0


def test_delete_item_cascades_withdrawals(session: Session, test_admin: User) -> None:
    """Test: Deleting item also deletes associated withdrawal entries."""
    from app.models import Withdrawal
    from sqlmodel import select

    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Create withdrawal
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=100,
        user_id=test_admin.id,
    )

    item_id = item.id

    # Delete item
    item_service.delete_item(session, item_id)

    # Verify withdrawals are also deleted
    remaining = list(session.exec(select(Withdrawal).where(Withdrawal.item_id == item_id)).all())
    assert len(remaining) == 0


# =============================================================================
# Initial Quantity Tests (Issue #204)
# =============================================================================


def test_get_item_initial_quantity_no_withdrawals(session: Session, test_admin: User) -> None:
    """Test: Initial quantity equals current quantity when no withdrawals."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    initial_quantity = item_service.get_item_initial_quantity(session, item.id)

    assert initial_quantity == 500


def test_get_item_initial_quantity_with_single_withdrawal(session: Session, test_admin: User) -> None:
    """Test: Initial quantity = current + withdrawn when one withdrawal exists."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Withdraw 200g
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=200,
        user_id=test_admin.id,
    )

    # Current quantity is 300, initial should be 500
    initial_quantity = item_service.get_item_initial_quantity(session, item.id)

    assert initial_quantity == 500


def test_get_item_initial_quantity_with_multiple_withdrawals(session: Session, test_admin: User) -> None:
    """Test: Initial quantity = current + sum of all withdrawals."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Multiple withdrawals: 100 + 150 = 250
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=100,
        user_id=test_admin.id,
    )
    item_service.withdraw_partial(
        session=session,
        item_id=item.id,
        withdraw_quantity=150,
        user_id=test_admin.id,
    )

    # Current quantity is 250, initial should be 500
    initial_quantity = item_service.get_item_initial_quantity(session, item.id)

    assert initial_quantity == 500


def test_get_item_initial_quantity_not_found_fails(session: Session) -> None:
    """Test: Getting initial quantity for non-existent item fails."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.get_item_initial_quantity(session, 999)


# =============================================================================
# Consumed Items Filter Tests (Issue #207)
# =============================================================================


def test_get_consumed_items_returns_only_items_with_withdrawals(session: Session, test_admin: User) -> None:
    """Test: get_consumed_items returns only items that have withdrawals."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    # Item without any withdrawal (should NOT appear)
    item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    # Item with partial withdrawal (SHOULD appear)
    partial_item = item_service.create_item(
        session=session,
        product_name="Karotten",
        best_before_date=date(2025, 2, 1),
        quantity=300,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )
    item_service.withdraw_partial(
        session=session,
        item_id=partial_item.id,
        withdraw_quantity=100,
        user_id=test_admin.id,
    )

    # Item fully consumed (SHOULD appear)
    consumed_item = item_service.create_item(
        session=session,
        product_name="Spinat",
        best_before_date=date(2025, 3, 1),
        quantity=200,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )
    item_service.mark_item_consumed(session, consumed_item.id, user_id=test_admin.id)

    consumed_items = item_service.get_consumed_items(session)

    assert len(consumed_items) == 2
    product_names = {item.product_name for item in consumed_items}
    assert "Karotten" in product_names
    assert "Spinat" in product_names
    assert "Erbsen" not in product_names


def test_get_consumed_items_sorted_by_last_withdrawal_descending(session: Session, test_admin: User) -> None:
    """Test: get_consumed_items returns items sorted by last withdrawal date (newest first)."""
    from time import sleep

    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    # First item - withdrawn first
    item1 = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )
    item_service.withdraw_partial(
        session=session,
        item_id=item1.id,
        withdraw_quantity=100,
        user_id=test_admin.id,
    )

    # Small delay to ensure different timestamps
    sleep(0.01)

    # Second item - withdrawn second (should appear first in results)
    item2 = item_service.create_item(
        session=session,
        product_name="Karotten",
        best_before_date=date(2025, 2, 1),
        quantity=300,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )
    item_service.withdraw_partial(
        session=session,
        item_id=item2.id,
        withdraw_quantity=50,
        user_id=test_admin.id,
    )

    consumed_items = item_service.get_consumed_items(session)

    assert len(consumed_items) == 2
    # Most recently withdrawn should be first
    assert consumed_items[0].product_name == "Karotten"
    assert consumed_items[1].product_name == "Erbsen"


def test_get_consumed_items_empty_when_no_withdrawals(session: Session, test_admin: User) -> None:
    """Test: get_consumed_items returns empty list when no items have withdrawals."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create items without withdrawals
    item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=date(2025, 1, 1),
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
        freeze_date=date(2024, 6, 1),
    )

    consumed_items = item_service.get_consumed_items(session)

    assert len(consumed_items) == 0


# =============================================================================
# Bug Fix Tests (Issue #222)
# =============================================================================


def test_mark_item_consumed_sets_quantity_to_zero(session: Session, test_admin: User) -> None:
    """Test: mark_item_consumed sets quantity to 0.

    Bug #222: When marking item as consumed, quantity was not set to 0,
    causing get_item_initial_quantity to calculate wrong value (current + withdrawn).
    """
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milch",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1.0,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    updated = item_service.mark_item_consumed(session, item.id, user_id=test_admin.id)

    # quantity must be 0 after marking as consumed
    assert updated.quantity == 0
    assert updated.is_consumed is True


def test_get_initial_quantity_correct_after_mark_consumed(session: Session, test_admin: User) -> None:
    """Test: get_item_initial_quantity returns correct value after mark_item_consumed.

    Bug #222: Initial quantity was calculated as current + withdrawn.
    If quantity wasn't set to 0, this would return 1 + 1 = 2 instead of 1.
    """
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milch",
        created_by=test_admin.id,
    )

    assert category.id is not None
    assert test_admin.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2024, 12, 10),
        quantity=1.0,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    item_service.mark_item_consumed(session, item.id, user_id=test_admin.id)

    # Initial quantity should be 1 (not 2!)
    initial_qty = item_service.get_item_initial_quantity(session, item.id)
    assert initial_qty == 1.0


# =============================================================================
# Dashboard Statistics Tests (Issue #243)
# =============================================================================


def test_get_recently_added_items_returns_newest_first(session: Session, test_admin: User) -> None:
    """Test: get_recently_added_items returns items sorted by created_at descending."""
    from time import sleep

    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create items with slight delay to ensure different timestamps
    item1 = item_service.create_item(
        session=session,
        product_name="Erstes Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    sleep(0.01)

    item2 = item_service.create_item(
        session=session,
        product_name="Zweites Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    sleep(0.01)

    item3 = item_service.create_item(
        session=session,
        product_name="Drittes Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    items = item_service.get_recently_added_items(session, limit=5)

    assert len(items) == 3
    # Newest first
    assert items[0].id == item3.id
    assert items[1].id == item2.id
    assert items[2].id == item1.id


def test_get_recently_added_items_respects_limit(session: Session, test_admin: User) -> None:
    """Test: get_recently_added_items returns at most 'limit' items."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create 5 items
    for i in range(5):
        item_service.create_item(
            session=session,
            product_name=f"Item {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=test_admin.id,
            category_id=category.id,
        )

    items = item_service.get_recently_added_items(session, limit=3)

    assert len(items) == 3


def test_get_recently_added_items_excludes_consumed(session: Session, test_admin: User) -> None:
    """Test: get_recently_added_items excludes consumed items."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Active item
    active_item = item_service.create_item(
        session=session,
        product_name="Aktives Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    # Consumed item
    consumed_item = item_service.create_item(
        session=session,
        product_name="Verbrauchtes Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )
    item_service.mark_item_consumed(session, consumed_item.id)

    items = item_service.get_recently_added_items(session, limit=5)

    assert len(items) == 1
    assert items[0].id == active_item.id


def test_get_recently_added_items_empty_database(session: Session) -> None:
    """Test: get_recently_added_items returns empty list when no items exist."""
    items = item_service.get_recently_added_items(session, limit=5)

    assert len(items) == 0


def test_get_item_count_by_location(session: Session, test_admin: User) -> None:
    """Test: get_item_count_by_location returns correct counts per location."""
    location1 = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    location2 = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # 3 items in location1
    for i in range(3):
        item_service.create_item(
            session=session,
            product_name=f"Kühlschrank Item {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location1.id,
            created_by=test_admin.id,
            category_id=category.id,
        )

    # 2 items in location2
    for i in range(2):
        item_service.create_item(
            session=session,
            product_name=f"Gefrierschrank Item {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=location2.id,
            created_by=test_admin.id,
            category_id=category.id,
            freeze_date=date(2024, 6, 1),
        )

    counts = item_service.get_item_count_by_location(session)

    assert counts[location1.id] == 3
    assert counts[location2.id] == 2


def test_get_item_count_by_location_excludes_consumed(session: Session, test_admin: User) -> None:
    """Test: get_item_count_by_location excludes consumed items."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # 2 active items
    for i in range(2):
        item_service.create_item(
            session=session,
            product_name=f"Aktives Item {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=test_admin.id,
            category_id=category.id,
        )

    # 1 consumed item
    consumed_item = item_service.create_item(
        session=session,
        product_name="Verbrauchtes Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )
    item_service.mark_item_consumed(session, consumed_item.id)

    counts = item_service.get_item_count_by_location(session)

    assert counts[location.id] == 2


def test_get_item_count_by_location_empty_database(session: Session) -> None:
    """Test: get_item_count_by_location returns empty dict when no items exist."""
    counts = item_service.get_item_count_by_location(session)

    assert counts == {}


def test_get_item_count_by_category(session: Session, test_admin: User) -> None:
    """Test: get_item_count_by_category returns correct counts per category."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category1 = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )
    category2 = category_service.create_category(
        session=session,
        name="Obst",
        created_by=test_admin.id,
    )

    assert category1.id is not None
    assert category2.id is not None

    # 3 items in category1
    for i in range(3):
        item_service.create_item(
            session=session,
            product_name=f"Gemüse {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=test_admin.id,
            category_id=category1.id,
        )

    # 2 items in category2
    for i in range(2):
        item_service.create_item(
            session=session,
            product_name=f"Obst {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=test_admin.id,
            category_id=category2.id,
        )

    counts = item_service.get_item_count_by_category(session)

    assert counts[category1.id] == 3
    assert counts[category2.id] == 2


def test_get_item_count_by_category_excludes_consumed(session: Session, test_admin: User) -> None:
    """Test: get_item_count_by_category excludes consumed items."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # 2 active items
    for i in range(2):
        item_service.create_item(
            session=session,
            product_name=f"Aktives Item {i}",
            best_before_date=date(2025, 6, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,
            created_by=test_admin.id,
            category_id=category.id,
        )

    # 1 consumed item
    consumed_item = item_service.create_item(
        session=session,
        product_name="Verbrauchtes Item",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )
    item_service.mark_item_consumed(session, consumed_item.id)

    counts = item_service.get_item_count_by_category(session)

    assert counts[category.id] == 2


def test_get_item_count_by_category_excludes_items_without_category(session: Session, test_admin: User) -> None:
    """Test: get_item_count_by_category excludes items without a category."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Lebensmittel",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Item with category
    item_service.create_item(
        session=session,
        product_name="Mit Kategorie",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    # Item without category
    item_service.create_item(
        session=session,
        product_name="Ohne Kategorie",
        best_before_date=date(2025, 6, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=None,
    )

    counts = item_service.get_item_count_by_category(session)

    assert counts[category.id] == 1
    assert len(counts) == 1  # Only the category with items should be in the dict


def test_get_item_count_by_category_empty_database(session: Session) -> None:
    """Test: get_item_count_by_category returns empty dict when no items exist."""
    counts = item_service.get_item_count_by_category(session)

    assert counts == {}
