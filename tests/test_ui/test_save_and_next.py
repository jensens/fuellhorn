"""Unit tests for Save & Next flow logic (Phase 7)."""

from app.models.freeze_time_config import ItemType
from datetime import datetime
from datetime import timedelta


# Test for Smart Defaults Storage Format


def test_create_smart_defaults_dict_contains_required_fields() -> None:
    """Test that smart defaults dict contains all required fields."""
    from app.ui.smart_defaults import create_smart_defaults_dict

    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FRESH,
        unit="g",
        location_id=1,
        category_id=1,
        best_before_date_str="25.11.2025",
    )

    assert "timestamp" in result
    assert "item_type" in result
    assert "unit" in result
    assert "location_id" in result
    assert "category_id" in result
    assert "best_before_date" in result


def test_create_smart_defaults_dict_values() -> None:
    """Test that smart defaults dict contains correct values."""
    from app.ui.smart_defaults import create_smart_defaults_dict

    result = create_smart_defaults_dict(
        item_type=ItemType.HOMEMADE_FROZEN,
        unit="kg",
        location_id=5,
        category_id=3,
        best_before_date_str="01.12.2025",
    )

    assert result["item_type"] == ItemType.HOMEMADE_FROZEN.value
    assert result["unit"] == "kg"
    assert result["location_id"] == 5
    assert result["category_id"] == 3
    assert result["best_before_date"] == "01.12.2025"


def test_create_smart_defaults_dict_timestamp_is_iso_format() -> None:
    """Test that timestamp is in ISO format."""
    from app.ui.smart_defaults import create_smart_defaults_dict

    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FROZEN,
        unit="ml",
        location_id=2,
        category_id=None,
        best_before_date_str="15.11.2025",
    )

    # Should be parseable as ISO datetime
    parsed = datetime.fromisoformat(result["timestamp"])
    assert isinstance(parsed, datetime)
    # Should be recent (within last minute)
    assert (datetime.now() - parsed).total_seconds() < 60


def test_create_smart_defaults_with_none_category() -> None:
    """Test smart defaults with None category."""
    from app.ui.smart_defaults import create_smart_defaults_dict

    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FRESH,
        unit="Stück",
        location_id=1,
        category_id=None,
        best_before_date_str="20.11.2025",
    )

    assert result["category_id"] is None


def test_create_smart_defaults_with_category() -> None:
    """Test smart defaults with a category ID."""
    from app.ui.smart_defaults import create_smart_defaults_dict

    result = create_smart_defaults_dict(
        item_type=ItemType.PURCHASED_FRESH,
        unit="l",
        location_id=3,
        category_id=5,
        best_before_date_str="10.11.2025",
    )

    assert result["category_id"] == 5


# Test for Time Window Logic


def test_is_within_time_window_recent() -> None:
    """Test that recent timestamp is within time window."""
    from app.ui.smart_defaults import is_within_time_window

    # 5 minutes ago
    recent = (datetime.now() - timedelta(minutes=5)).isoformat()
    assert is_within_time_window(recent, window_minutes=30) is True


def test_is_within_time_window_old() -> None:
    """Test that old timestamp is outside time window."""
    from app.ui.smart_defaults import is_within_time_window

    # 60 minutes ago
    old = (datetime.now() - timedelta(minutes=60)).isoformat()
    assert is_within_time_window(old, window_minutes=30) is False


def test_is_within_time_window_exactly_at_boundary() -> None:
    """Test timestamp exactly at window boundary."""
    from app.ui.smart_defaults import is_within_time_window

    # Exactly 30 minutes ago
    at_boundary = (datetime.now() - timedelta(minutes=30)).isoformat()
    # Should be just outside (>= window_minutes)
    assert is_within_time_window(at_boundary, window_minutes=30) is False


def test_is_within_time_window_just_inside() -> None:
    """Test timestamp just inside window boundary."""
    from app.ui.smart_defaults import is_within_time_window

    # 29 minutes ago
    just_inside = (datetime.now() - timedelta(minutes=29)).isoformat()
    assert is_within_time_window(just_inside, window_minutes=30) is True


def test_is_within_time_window_invalid_timestamp() -> None:
    """Test with invalid timestamp string."""
    from app.ui.smart_defaults import is_within_time_window

    assert is_within_time_window("invalid", window_minutes=30) is False
    assert is_within_time_window("", window_minutes=30) is False


def test_is_within_time_window_none_timestamp() -> None:
    """Test with None timestamp."""
    from app.ui.smart_defaults import is_within_time_window

    assert is_within_time_window(None, window_minutes=30) is False


# Test for Smart Defaults Loading Logic


def test_get_default_item_type_returns_last_when_within_window() -> None:
    """Test item type default returns last value within time window."""
    from app.ui.smart_defaults import get_default_item_type

    recent_timestamp = (datetime.now() - timedelta(minutes=10)).isoformat()
    last_entry = {
        "timestamp": recent_timestamp,
        "item_type": ItemType.HOMEMADE_FROZEN.value,
    }

    result = get_default_item_type(last_entry, window_minutes=30)
    assert result == ItemType.HOMEMADE_FROZEN


def test_get_default_item_type_returns_none_when_outside_window() -> None:
    """Test item type default returns None when outside time window."""
    from app.ui.smart_defaults import get_default_item_type

    old_timestamp = (datetime.now() - timedelta(minutes=60)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "item_type": ItemType.HOMEMADE_FROZEN.value,
    }

    result = get_default_item_type(last_entry, window_minutes=30)
    assert result is None


def test_get_default_item_type_returns_none_when_no_entry() -> None:
    """Test item type default returns None when no last entry."""
    from app.ui.smart_defaults import get_default_item_type

    result = get_default_item_type(None, window_minutes=30)
    assert result is None


def test_get_default_unit_always_returns_last() -> None:
    """Test unit default always returns last value (no time window)."""
    from app.ui.smart_defaults import get_default_unit

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
    from app.ui.smart_defaults import get_default_unit

    result = get_default_unit(None)
    assert result == "g"


def test_get_default_location_always_returns_last() -> None:
    """Test location default always returns last value."""
    from app.ui.smart_defaults import get_default_location

    # Even with old timestamp, location should be returned
    old_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "location_id": 42,
    }

    result = get_default_location(last_entry)
    assert result == 42


def test_get_default_location_returns_none_when_no_entry() -> None:
    """Test location default returns None when no last entry."""
    from app.ui.smart_defaults import get_default_location

    result = get_default_location(None)
    assert result is None


def test_get_default_category_returns_last_when_within_window() -> None:
    """Test category default returns last value within time window."""
    from app.ui.smart_defaults import get_default_category

    recent_timestamp = (datetime.now() - timedelta(minutes=15)).isoformat()
    last_entry = {
        "timestamp": recent_timestamp,
        "category_id": 3,
    }

    result = get_default_category(last_entry, window_minutes=30)
    assert result == 3


def test_get_default_category_returns_none_when_outside_window() -> None:
    """Test category default returns None when outside time window."""
    from app.ui.smart_defaults import get_default_category

    old_timestamp = (datetime.now() - timedelta(minutes=60)).isoformat()
    last_entry = {
        "timestamp": old_timestamp,
        "category_id": 3,
    }

    result = get_default_category(last_entry, window_minutes=30)
    assert result is None


def test_get_default_category_returns_none_when_no_entry() -> None:
    """Test category default returns None when no last entry."""
    from app.ui.smart_defaults import get_default_category

    result = get_default_category(None, window_minutes=30)
    assert result is None


# Test for Form Reset Logic


def test_get_reset_form_data_contains_all_fields() -> None:
    """Test reset form data contains all required fields."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=None,
        default_unit="g",
        default_location_id=None,
        default_category_id=None,
    )

    assert "product_name" in result
    assert "item_type" in result
    assert "quantity" in result
    assert "unit" in result
    assert "best_before_date" in result
    assert "freeze_date" in result
    assert "notes" in result
    assert "location_id" in result
    assert "category_id" in result
    assert "current_step" in result


def test_get_reset_form_data_clears_product_name() -> None:
    """Test reset form data clears product name."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=ItemType.PURCHASED_FRESH,
        default_unit="kg",
        default_location_id=5,
        default_category_id=1,
    )

    assert result["product_name"] == ""


def test_get_reset_form_data_clears_quantity() -> None:
    """Test reset form data clears quantity."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=ItemType.PURCHASED_FRESH,
        default_unit="kg",
        default_location_id=5,
        default_category_id=1,
    )

    assert result["quantity"] is None


def test_get_reset_form_data_applies_smart_defaults() -> None:
    """Test reset form data applies smart defaults."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=ItemType.HOMEMADE_FROZEN,
        default_unit="kg",
        default_location_id=3,
        default_category_id=1,
    )

    assert result["item_type"] == ItemType.HOMEMADE_FROZEN
    assert result["unit"] == "kg"
    assert result["location_id"] == 3
    assert result["category_id"] == 1


def test_get_reset_form_data_resets_to_step_1() -> None:
    """Test reset form data sets step to 1."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=None,
        default_unit="g",
        default_location_id=None,
        default_category_id=None,
    )

    assert result["current_step"] == 1


def test_get_reset_form_data_clears_notes() -> None:
    """Test reset form data clears notes."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=None,
        default_unit="g",
        default_location_id=None,
        default_category_id=None,
    )

    assert result["notes"] == ""


def test_get_reset_form_data_clears_freeze_date() -> None:
    """Test reset form data clears freeze date."""
    from app.ui.smart_defaults import get_reset_form_data

    result = get_reset_form_data(
        default_item_type=None,
        default_unit="g",
        default_location_id=None,
        default_category_id=None,
    )

    assert result["freeze_date"] is None
