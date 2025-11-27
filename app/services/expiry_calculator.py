"""Expiry calculator - Calculate expiry dates and status for items."""

from ..models.category_shelf_life import StorageType
from ..models.freeze_time_config import ItemType
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Literal


# Type alias for expiry status
ExpiryStatus = Literal["critical", "warning", "ok"]


def get_storage_type_for_item_type(item_type: ItemType) -> StorageType | None:
    """Get the storage type for shelf life calculation.

    Maps item types to storage types for looking up CategoryShelfLife data.
    Returns None for item types that use best_before_date directly (MHD).

    Args:
        item_type: The type of item

    Returns:
        StorageType for shelf life lookup, or None if item uses MHD directly
    """
    if item_type in [ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN]:
        return StorageType.FROZEN
    elif item_type == ItemType.HOMEMADE_PRESERVED:
        return StorageType.AMBIENT
    return None  # PURCHASED_FRESH, PURCHASED_FROZEN use MHD directly


def calculate_expiry_dates(
    item_type: ItemType,
    base_date: date,
    months_min: int,
    months_max: int,
) -> tuple[date, date]:
    """Calculate optimal and maximum expiry dates.

    Uses months_min for optimal consumption date and months_max for
    maximum storage date.

    Args:
        item_type: Type of item (not currently used, for future extension)
        base_date: The base date (freeze_date or production_date)
        months_min: Minimum recommended storage time in months
        months_max: Maximum recommended storage time in months

    Returns:
        Tuple of (optimal_date, max_date)
    """
    optimal_date = base_date + relativedelta(months=months_min)
    max_date = base_date + relativedelta(months=months_max)
    return (optimal_date, max_date)


def get_expiry_status_minmax(
    optimal_date: date | None,
    max_date: date | None,
    best_before_date: date | None = None,
) -> ExpiryStatus:
    """Get expiry status based on optimal and maximum dates.

    Status logic:
    - ok: today < optimal_date
    - warning: optimal_date <= today < max_date - 3 days
    - critical: today >= max_date - 3 days

    If best_before_date is provided (for items with MHD), it takes precedence
    using the old 3/7 day thresholds.

    Args:
        optimal_date: Optimal consumption date (from months_min)
        max_date: Maximum storage date (from months_max)
        best_before_date: Best before date from package (MHD)

    Returns:
        ExpiryStatus: "critical", "warning", or "ok"
    """
    today = date.today()

    # If best_before_date is provided, use it as the primary date
    # (for PURCHASED_FRESH, PURCHASED_FROZEN with MHD)
    if best_before_date is not None:
        days_until_best_before = (best_before_date - today).days
        if days_until_best_before < 3:
            return "critical"
        elif days_until_best_before <= 7:
            return "warning"
        else:
            return "ok"

    # If only max_date is provided (no optimal)
    if optimal_date is None and max_date is not None:
        days_until_max = (max_date - today).days
        if days_until_max <= 3:
            return "critical"
        else:
            return "ok"

    # If only optimal_date is provided (no max)
    if max_date is None and optimal_date is not None:
        days_until_optimal = (optimal_date - today).days
        if days_until_optimal < 0:
            return "warning"
        else:
            return "ok"

    # Both optimal_date and max_date are None - shouldn't happen but handle gracefully
    if optimal_date is None or max_date is None:
        return "ok"

    # Normal case: both optimal and max dates provided
    # (mypy now knows both are not None due to the check above)
    days_until_optimal = (optimal_date - today).days
    days_until_max = (max_date - today).days

    # Critical: within 3 days of max_date (or past it)
    if days_until_max <= 3:
        return "critical"

    # Ok: before optimal_date
    if days_until_optimal > 0:
        return "ok"

    # Warning: past optimal but more than 3 days before max
    return "warning"


def calculate_expiry_date(
    item_type: ItemType,
    best_before_date: date,
    freeze_date: date | None,
    freeze_time_months: int | None,
) -> date:
    """Calculate expiry date for an item.

    Expiry calculation rules by item type:
    - PURCHASED_FRESH: best_before_date + freeze_time_months
    - PURCHASED_FROZEN: best_before_date (MHD on package, no freeze_date needed)
    - PURCHASED_THEN_FROZEN: freeze_date + freeze_time_months (requires freeze_date)
    - HOMEMADE_FROZEN: freeze_date + freeze_time_months (requires freeze_date)
    - HOMEMADE_PRESERVED: best_before_date + freeze_time_months

    If freeze_time_months is None, uses best_before_date as expiry.

    Args:
        item_type: Type of item
        best_before_date: Best before/manufacture date
        freeze_date: Date when item was frozen (required for self-frozen types)
        freeze_time_months: Storage time in months from config (optional)

    Returns:
        Calculated expiry date

    Raises:
        ValueError: If self-frozen item without freeze_date
    """
    # If no freeze_time config, use best_before_date as-is
    if freeze_time_months is None:
        return best_before_date

    # Only self-frozen items use freeze_date as base
    # PURCHASED_FROZEN uses best_before_date (MHD on package)
    self_frozen_types = {
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    }

    if item_type in self_frozen_types:
        if freeze_date is None:
            raise ValueError("Self-frozen items must have a freeze_date")

        return freeze_date + relativedelta(months=freeze_time_months)

    # All other types (including PURCHASED_FROZEN) use best_before_date as base
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
