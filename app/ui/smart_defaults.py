"""Smart Defaults logic for Item Capture Wizard.

This module handles the saving and loading of smart defaults
for the bulk capture workflow. When a user saves an item and
clicks "Speichern & Nächster", the relevant form values are
stored and used to pre-fill the next item entry.

Der letzte Eintrag liegt pro Nutzer in ``user.preferences`` (``preferences_service``),
nicht im Browser-Storage; die Zeitfenster kommen aus den Preferences
(Profil > System-Default > ``HARDCODED_DEFAULTS``: Typ 30, Kategorie 30, Lagerort 60 Minuten;
Einheit ohne Zeitfenster) – Issue #397.
"""

from ..models.item import ItemType
from datetime import datetime
from typing import Any


def create_smart_defaults_dict(
    item_type: ItemType,
    unit: str,
    location_id: int,
    category_id: int | None,
) -> dict[str, Any]:
    """Create the last-entry dictionary stored via ``preferences_service.save_last_item_entry``.

    Enthält nur, was der Wizard beim nächsten Aufruf liest (Issue #397).

    Args:
        item_type: The item type enum value.
        unit: The unit string (g, kg, ml, etc.).
        location_id: The location ID.
        category_id: Category ID (optional).
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "item_type": item_type.value,
        "unit": unit,
        "location_id": location_id,
        "category_id": category_id,
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


def get_default_location(
    last_entry: dict[str, Any] | None,
    window_minutes: int = 60,
) -> int | None:
    """Get the default location ID from last entry if within time window.

    Ob der Lagerort zum gewählten Artikel-Typ passt, entscheidet erst Schritt 3
    des Wizards (Issue #385): dort wird eine ID verworfen, die nicht unter den
    angebotenen Lagerorten ist.

    Args:
        last_entry: The last item entry from browser storage.
        window_minutes: Time window in minutes (default: 60).

    Returns:
        Location ID or None if not within window.
    """
    if not last_entry:
        return None

    timestamp = last_entry.get("timestamp")
    if not is_within_time_window(timestamp, window_minutes):
        return None

    return last_entry.get("location_id")


def get_default_category(
    last_entry: dict[str, Any] | None,
    window_minutes: int = 30,
) -> int | None:
    """Get the default category ID from last entry if within time window.

    Args:
        last_entry: The last item entry from browser storage.
        window_minutes: Time window in minutes (default: 30).

    Returns:
        Category ID or None if not within window.
    """
    if not last_entry:
        return None

    timestamp = last_entry.get("timestamp")
    if not is_within_time_window(timestamp, window_minutes):
        return None

    return last_entry.get("category_id")
