"""Tests for expiry_calculator."""

from app.models import ItemType
from app.services import expiry_calculator
from datetime import date
import pytest


def test_calculate_expiry_for_tinned_item() -> None:
    """Test expiry calculation for preserved items (formerly tinned)."""
    # Homemade preserved: best_before_date + X months (treated as long-term storage)
    best_before = date(2024, 1, 1)
    freeze_time_months = 24  # 2 years

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.HOMEMADE_PRESERVED,
        best_before_date=best_before,
        freeze_date=None,
        freeze_time_months=freeze_time_months,
    )

    assert expiry == date(2026, 1, 1)  # best_before + 24 months


def test_calculate_expiry_for_jarred_item() -> None:
    """Test expiry calculation for preserved items (formerly jarred)."""
    # Homemade preserved: best_before_date + X months (similar to canned)
    best_before = date(2024, 6, 15)
    freeze_time_months = 18  # 1.5 years

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.HOMEMADE_PRESERVED,
        best_before_date=best_before,
        freeze_date=None,
        freeze_time_months=freeze_time_months,
    )

    assert expiry == date(2025, 12, 15)  # best_before + 18 months


def test_calculate_expiry_for_frozen_item() -> None:
    """Test expiry calculation for purchased frozen items."""
    # Purchased frozen: freeze_date + X months
    best_before = date(2024, 1, 1)
    freeze_date_val = date(2024, 6, 1)
    freeze_time_months = 12

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.PURCHASED_FROZEN,
        best_before_date=best_before,
        freeze_date=freeze_date_val,
        freeze_time_months=freeze_time_months,
    )

    assert expiry == date(2025, 6, 1)  # freeze_date + 12 months


def test_calculate_expiry_for_frozen_item_without_freeze_date_fails() -> None:
    """Test that frozen item without freeze_date raises error."""
    with pytest.raises(ValueError, match="Frozen items must have a freeze_date"):
        expiry_calculator.calculate_expiry_date(
            item_type=ItemType.PURCHASED_FROZEN,
            best_before_date=date(2024, 1, 1),
            freeze_date=None,
            freeze_time_months=12,
        )


def test_calculate_expiry_for_chilled_item() -> None:
    """Test expiry calculation for fresh items (chilled)."""
    # Purchased fresh (chilled): best_before_date + X months (short-term storage)
    best_before = date(2024, 6, 1)
    freeze_time_months = 3

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.PURCHASED_FRESH,
        best_before_date=best_before,
        freeze_date=None,
        freeze_time_months=freeze_time_months,
    )

    assert expiry == date(2024, 9, 1)  # best_before + 3 months


def test_calculate_expiry_for_ambient_item() -> None:
    """Test expiry calculation for fresh items (ambient)."""
    # Purchased fresh (ambient): best_before_date + X months (room temperature storage)
    best_before = date(2024, 3, 15)
    freeze_time_months = 6

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.PURCHASED_FRESH,
        best_before_date=best_before,
        freeze_date=None,
        freeze_time_months=freeze_time_months,
    )

    assert expiry == date(2024, 9, 15)  # best_before + 6 months


def test_calculate_expiry_without_freeze_time_returns_best_before() -> None:
    """Test that items without freeze_time use best_before_date as expiry."""
    best_before = date(2024, 12, 31)

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.PURCHASED_FRESH,
        best_before_date=best_before,
        freeze_date=None,
        freeze_time_months=None,
    )

    assert expiry == best_before  # No extension, use best_before as-is


def test_calculate_expiry_frozen_without_freeze_time_returns_best_before() -> None:
    """Test that frozen items without freeze_time use best_before_date."""
    best_before = date(2024, 12, 31)
    freeze_date_val = date(2024, 6, 1)

    expiry = expiry_calculator.calculate_expiry_date(
        item_type=ItemType.PURCHASED_FROZEN,
        best_before_date=best_before,
        freeze_date=freeze_date_val,
        freeze_time_months=None,
    )

    # Without freeze_time config, frozen items use best_before_date
    assert expiry == best_before
