"""Unit tests for Save & Next flow logic (Phase 7, Issue #397: ohne nie gelesenes Datum)."""

from app.models.item import ItemType
from app.ui.smart_defaults import create_smart_defaults_dict
from app.ui.smart_defaults import get_default_category
from app.ui.smart_defaults import get_default_item_type
from app.ui.smart_defaults import get_default_location
from app.ui.smart_defaults import get_default_unit
from app.ui.smart_defaults import is_within_time_window
from datetime import datetime
from datetime import timedelta


# Test for Smart Defaults Storage Format


def test_create_smart_defaults_dict_contains_exactly_the_read_fields() -> None:
    """Gespeichert wird nur, was der Wizard auch liest; ``best_before_date`` wurde nie gelesen (#397)."""
    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FRESH,
        unit="g",
        location_id=1,
        category_id=1,
    )

    assert set(result) == {"timestamp", "item_type", "unit", "location_id", "category_id"}


def test_create_smart_defaults_dict_values() -> None:
    """Test that smart defaults dict contains correct values."""
    result = create_smart_defaults_dict(
        item_type=ItemType.HOMEMADE_FROZEN,
        unit="kg",
        location_id=5,
        category_id=3,
    )

    assert result["item_type"] == ItemType.HOMEMADE_FROZEN.value
    assert result["unit"] == "kg"
    assert result["location_id"] == 5
    assert result["category_id"] == 3


def test_create_smart_defaults_dict_timestamp_is_iso_format() -> None:
    """Test that timestamp is in ISO format."""
    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FROZEN,
        unit="ml",
        location_id=2,
        category_id=None,
    )

    # Should be parseable as ISO datetime
    parsed = datetime.fromisoformat(result["timestamp"])
    assert isinstance(parsed, datetime)
    # Should be recent (within last minute)
    assert (datetime.now() - parsed).total_seconds() < 60


def test_create_smart_defaults_with_none_category() -> None:
    """Test smart defaults with None category."""
    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FRESH,
        unit="Stück",
        location_id=1,
        category_id=None,
    )

    assert result["category_id"] is None


# Test for Time Window Logic


def test_is_within_time_window_recent() -> None:
    """Test that recent timestamp is within time window."""
    # 5 minutes ago
    recent = (datetime.now() - timedelta(minutes=5)).isoformat()
    assert is_within_time_window(recent, window_minutes=30) is True


def test_is_within_time_window_old() -> None:
    """Test that old timestamp is outside time window."""
    # 60 minutes ago
    old = (datetime.now() - timedelta(minutes=60)).isoformat()
    assert is_within_time_window(old, window_minutes=30) is False


def test_is_within_time_window_exactly_at_boundary() -> None:
    """Test timestamp exactly at window boundary."""
    # Exactly 30 minutes ago
    at_boundary = (datetime.now() - timedelta(minutes=30)).isoformat()
    # Should be just outside (>= window_minutes)
    assert is_within_time_window(at_boundary, window_minutes=30) is False


def test_is_within_time_window_just_inside() -> None:
    """Test timestamp just inside window boundary."""
    # 29 minutes ago
    just_inside = (datetime.now() - timedelta(minutes=29)).isoformat()
    assert is_within_time_window(just_inside, window_minutes=30) is True


def test_is_within_time_window_invalid_timestamp() -> None:
    """Test with invalid timestamp string."""
    assert is_within_time_window("invalid", window_minutes=30) is False
    assert is_within_time_window("", window_minutes=30) is False


def test_is_within_time_window_none_timestamp() -> None:
    """Test with None timestamp."""
    assert is_within_time_window(None, window_minutes=30) is False


# Test for Smart Defaults Loading Logic


def test_get_default_item_type_returns_last_when_within_window() -> None:
    """Test item type default returns last value within time window."""
    recent_timestamp = (datetime.now() - timedelta(minutes=10)).isoformat()
    last_entry = {
        "timestamp": recent_timestamp,
        "item_type": ItemType.HOMEMADE_FROZEN.value,
    }

    result = get_default_item_type(last_entry, window_minutes=30)
    assert result == ItemType.HOMEMADE_FROZEN


def test_get_default_item_type_returns_none_when_outside_window() -> None:
    """Test item type default returns None when outside time window."""
    old_timestamp = (datetime.now() - timedelta(minutes=60)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "item_type": ItemType.HOMEMADE_FROZEN.value,
    }

    result = get_default_item_type(last_entry, window_minutes=30)
    assert result is None


def test_get_default_item_type_honours_short_user_window() -> None:
    """Das Zeitfenster kommt aus den Preferences: 1 Minute Fenster, Eintrag 2 Minuten alt → kein Default (#397)."""
    last_entry = {
        "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat(),
        "item_type": ItemType.PURCHASED_FROZEN.value,
    }

    assert get_default_item_type(last_entry, window_minutes=1) is None
    assert get_default_item_type(last_entry, window_minutes=5) == ItemType.PURCHASED_FROZEN


def test_get_default_item_type_returns_none_when_no_entry() -> None:
    """Test item type default returns None when no last entry."""
    result = get_default_item_type(None, window_minutes=30)
    assert result is None


def test_get_default_unit_always_returns_last() -> None:
    """Test unit default always returns last value (no time window)."""
    # Even with old timestamp, unit should be returned
    old_timestamp = (datetime.now() - timedelta(hours=24)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "unit": "kg",
    }

    result = get_default_unit(last_entry)
    assert result == "kg"


def test_get_default_unit_returns_g_when_no_entry() -> None:
    """Test unit default returns 'g' when no last entry."""
    result = get_default_unit(None)
    assert result == "g"


def test_get_default_location_returns_last_when_within_window() -> None:
    """Lagerort-Default gilt innerhalb des Zeitfensters (Issue #385: vorher ohne Zeitfenster)."""
    recent_timestamp = (datetime.now() - timedelta(minutes=10)).isoformat()
    last_entry = {
        "timestamp": recent_timestamp,
        "location_id": 42,
    }

    result = get_default_location(last_entry, window_minutes=60)
    assert result == 42


def test_get_default_location_returns_none_when_outside_window() -> None:
    """Nach Ablauf des Zeitfensters wird kein alter Lagerort mehr vorbelegt (Issue #385)."""
    old_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "location_id": 42,
    }

    result = get_default_location(last_entry, window_minutes=60)
    assert result is None


def test_get_default_location_returns_none_when_no_entry() -> None:
    """Test location default returns None when no last entry."""
    result = get_default_location(None)
    assert result is None


def test_get_default_category_returns_last_when_within_window() -> None:
    """Test category default returns last value within time window."""
    recent_timestamp = (datetime.now() - timedelta(minutes=15)).isoformat()
    last_entry = {
        "timestamp": recent_timestamp,
        "category_id": 3,
    }

    result = get_default_category(last_entry, window_minutes=30)
    assert result == 3


def test_get_default_category_returns_none_when_outside_window() -> None:
    """Test category default returns None when outside time window."""
    old_timestamp = (datetime.now() - timedelta(minutes=60)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "category_id": 3,
    }

    result = get_default_category(last_entry, window_minutes=30)
    assert result is None


def test_get_default_category_returns_none_when_no_entry() -> None:
    """Test category default returns None when no last entry."""
    result = get_default_category(None, window_minutes=30)
    assert result is None
