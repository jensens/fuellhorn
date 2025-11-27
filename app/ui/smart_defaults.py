"""Smart Defaults logic for Item Capture Wizard.

This module handles the saving and loading of smart defaults
for the bulk capture workflow. When a user saves an item and
clicks "Speichern & Nächster", the relevant form values are
stored and used to pre-fill the next item entry.

Time Windows (from UI_KONZEPT.md):
- Item type: 30 minutes
- Categories: 30 minutes
- Location: Always (no time window)
- Unit: Always (no time window)
"""

from ..models.freeze_time_config import ItemType
from datetime import date as date_type
from datetime import datetime
from typing import Any


def create_smart_defaults_dict(
    item_type: ItemType,
    unit: str,
    location_id: int,
    category_ids: list[int] | None,
    best_before_date_str: str,
) -> dict[str, Any]:
    """Create a dictionary with smart defaults to store in browser storage.

    Args:
        item_type: The item type enum value.
        unit: The unit string (g, kg, ml, etc.).
        location_id: The location ID.
        category_ids: List of category IDs (optional).
        best_before_date_str: Best before date as string (DD.MM.YYYY format).

    Returns:
        Dictionary suitable for storing in app.storage.user.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "item_type": item_type.value,
        "unit": unit,
        "location_id": location_id,
        "category_ids": category_ids if category_ids else [],
        "best_before_date": best_before_date_str,
    }


def is_within_time_window(timestamp_str: str | None, window_minutes: int) -> bool:
    """Check if a timestamp is within the specified time window.

    Args:
        timestamp_str: ISO format timestamp string.
        window_minutes: Time window in minutes.

    Returns:
        True if timestamp is within window, False otherwise.
    """
    if not timestamp_str:
        return False

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        time_diff = (datetime.now() - timestamp).total_seconds() / 60
        return time_diff < window_minutes
    except (ValueError, TypeError):
        return False


def get_default_item_type(
    last_entry: dict[str, Any] | None,
    window_minutes: int = 30,
) -> ItemType | None:
    """Get the default item type from last entry if within time window.

    Args:
        last_entry: The last item entry from browser storage.
        window_minutes: Time window in minutes (default: 30).

    Returns:
        ItemType enum value or None if not within window.
    """
    if not last_entry:
        return None

    timestamp = last_entry.get("timestamp")
    if not is_within_time_window(timestamp, window_minutes):
        return None

    item_type_value = last_entry.get("item_type")
    if item_type_value:
        try:
            return ItemType(item_type_value)
        except ValueError:
            return None
    return None


def get_default_unit(last_entry: dict[str, Any] | None) -> str:
    """Get the default unit from last entry (no time window).

    Args:
        last_entry: The last item entry from browser storage.

    Returns:
        Unit string or "g" as fallback.
    """
    if not last_entry:
        return "g"

    unit = last_entry.get("unit", "g")
    return str(unit) if unit else "g"


def get_default_location(last_entry: dict[str, Any] | None) -> int | None:
    """Get the default location ID from last entry (no time window).

    Args:
        last_entry: The last item entry from browser storage.

    Returns:
        Location ID or None if not available.
    """
    if not last_entry:
        return None

    return last_entry.get("location_id")


def get_default_categories(
    last_entry: dict[str, Any] | None,
    window_minutes: int = 30,
) -> list[int]:
    """Get the default category IDs from last entry if within time window.

    Args:
        last_entry: The last item entry from browser storage.
        window_minutes: Time window in minutes (default: 30).

    Returns:
        List of category IDs or empty list if not within window.
    """
    if not last_entry:
        return []

    timestamp = last_entry.get("timestamp")
    if not is_within_time_window(timestamp, window_minutes):
        return []

    category_ids = last_entry.get("category_ids", [])
    return list(category_ids) if category_ids else []


def get_reset_form_data(
    default_item_type: ItemType | None,
    default_unit: str,
    default_location_id: int | None,
    default_category_ids: list[int],
) -> dict[str, Any]:
    """Get reset form data with smart defaults applied.

    This creates a fresh form data dictionary for the wizard,
    applying any smart defaults that should be pre-filled.

    Args:
        default_item_type: Default item type (or None).
        default_unit: Default unit string.
        default_location_id: Default location ID (or None).
        default_category_ids: Default category IDs list.

    Returns:
        Dictionary with form data for the wizard.
    """
    return {
        "product_name": "",
        "item_type": default_item_type,
        "quantity": None,
        "unit": default_unit,
        "best_before_date": date_type.today(),
        "freeze_date": None,
        "notes": "",
        "location_id": default_location_id,
        "category_ids": default_category_ids,
        "current_step": 1,
    }
