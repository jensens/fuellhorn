"""Expiry calculator - Calculate expiry dates and status for items."""

from ..models.freeze_time_config import ItemType
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Literal


# Type alias for expiry status
ExpiryStatus = Literal["critical", "warning", "ok"]


def calculate_expiry_date(
    item_type: ItemType,
    best_before_date: date,
    freeze_date: date | None,
    freeze_time_months: int | None,
) -> date:
    """Calculate expiry date for an item.

    Expiry calculation rules by item type:
    - PURCHASED_FRESH: best_before_date + freeze_time_months
    - HOMEMADE_PRESERVED: best_before_date + freeze_time_months
    - PURCHASED_FROZEN: freeze_date + freeze_time_months (requires freeze_date)
    - PURCHASED_THEN_FROZEN: freeze_date + freeze_time_months (requires freeze_date)
    - HOMEMADE_FROZEN: freeze_date + freeze_time_months (requires freeze_date)

    If freeze_time_months is None, uses best_before_date as expiry.

    Args:
        item_type: Type of item
        best_before_date: Best before/manufacture date
        freeze_date: Date when item was frozen (required for frozen types)
        freeze_time_months: Storage time in months from config (optional)

    Returns:
        Calculated expiry date

    Raises:
        ValueError: If frozen item without freeze_date
    """
    # If no freeze_time config, use best_before_date as-is
    if freeze_time_months is None:
        return best_before_date

    # Frozen items use freeze_date as base
    frozen_types = {
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    }

    if item_type in frozen_types:
        if freeze_date is None:
            raise ValueError("Frozen items must have a freeze_date")

        return freeze_date + relativedelta(months=freeze_time_months)

    # All other types use best_before_date as base
    return best_before_date + relativedelta(months=freeze_time_months)


def get_days_until_expiry(expiry_date: date) -> int:
    """Calculate days until expiry from today.

    Args:
        expiry_date: The expiry date of the item

    Returns:
        Number of days until expiry (negative if expired)
    """
    return (expiry_date - date.today()).days


def get_expiry_status(expiry_date: date) -> ExpiryStatus:
    """Get expiry status based on days until expiry.

    Status thresholds:
    - critical (red): < 3 days until expiry
    - warning (yellow): 3-7 days until expiry
    - ok (green): > 7 days until expiry

    Args:
        expiry_date: The expiry date of the item

    Returns:
        ExpiryStatus: "critical", "warning", or "ok"
    """
    days = get_days_until_expiry(expiry_date)

    if days < 3:
        return "critical"
    elif days <= 7:
        return "warning"
    else:
        return "ok"
