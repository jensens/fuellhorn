"""Tests for new Min/Max expiry calculator logic.

Tests the new functions for calculating optimal and maximum expiry dates
based on CategoryShelfLife months_min and months_max values.
"""

from app.models import ItemType
from app.models.category_shelf_life import StorageType
from app.services import expiry_calculator
from datetime import date
from datetime import timedelta


class TestGetStorageTypeForItemType:
    """Tests for get_storage_type_for_item_type function."""

    def test_purchased_then_frozen_returns_frozen(self) -> None:
        """Test: PURCHASED_THEN_FROZEN returns StorageType.FROZEN."""
        result = expiry_calculator.get_storage_type_for_item_type(ItemType.PURCHASED_THEN_FROZEN)
        assert result == StorageType.FROZEN

    def test_homemade_frozen_returns_frozen(self) -> None:
        """Test: HOMEMADE_FROZEN returns StorageType.FROZEN."""
        result = expiry_calculator.get_storage_type_for_item_type(ItemType.HOMEMADE_FROZEN)
        assert result == StorageType.FROZEN

    def test_homemade_preserved_returns_ambient(self) -> None:
        """Test: HOMEMADE_PRESERVED returns StorageType.AMBIENT."""
        result = expiry_calculator.get_storage_type_for_item_type(ItemType.HOMEMADE_PRESERVED)
        assert result == StorageType.AMBIENT

    def test_purchased_fresh_returns_none(self) -> None:
        """Test: PURCHASED_FRESH returns None (uses MHD directly)."""
        result = expiry_calculator.get_storage_type_for_item_type(ItemType.PURCHASED_FRESH)
        assert result is None

    def test_purchased_frozen_returns_none(self) -> None:
        """Test: PURCHASED_FROZEN returns None (uses MHD directly)."""
        result = expiry_calculator.get_storage_type_for_item_type(ItemType.PURCHASED_FROZEN)
        assert result is None


class TestCalculateExpiryDates:
    """Tests for calculate_expiry_dates function."""

    def test_calculate_dates_basic(self) -> None:
        """Test basic expiry date calculation."""
        base_date = date(2024, 1, 15)
        months_min = 6
        months_max = 12

        optimal, maximum = expiry_calculator.calculate_expiry_dates(
            item_type=ItemType.HOMEMADE_FROZEN,
            base_date=base_date,
            months_min=months_min,
            months_max=months_max,
        )

        assert optimal == date(2024, 7, 15)  # +6 months
        assert maximum == date(2025, 1, 15)  # +12 months

    def test_calculate_dates_equal_min_max(self) -> None:
        """Test when min equals max."""
        base_date = date(2024, 3, 1)
        months_min = 9
        months_max = 9

        optimal, maximum = expiry_calculator.calculate_expiry_dates(
            item_type=ItemType.PURCHASED_THEN_FROZEN,
            base_date=base_date,
            months_min=months_min,
            months_max=months_max,
        )

        assert optimal == date(2024, 12, 1)  # +9 months
        assert maximum == date(2024, 12, 1)  # +9 months (same)

    def test_calculate_dates_end_of_month(self) -> None:
        """Test with end of month dates (edge case for month arithmetic)."""
        base_date = date(2024, 1, 31)
        months_min = 1
        months_max = 3

        optimal, maximum = expiry_calculator.calculate_expiry_dates(
            item_type=ItemType.HOMEMADE_PRESERVED,
            base_date=base_date,
            months_min=months_min,
            months_max=months_max,
        )

        # dateutil.relativedelta handles month-end properly
        assert optimal == date(2024, 2, 29)  # Feb 29 (leap year 2024)
        assert maximum == date(2024, 4, 30)  # Apr has 30 days

    def test_calculate_dates_across_year_boundary(self) -> None:
        """Test calculation across year boundary."""
        base_date = date(2024, 11, 15)
        months_min = 3
        months_max = 6

        optimal, maximum = expiry_calculator.calculate_expiry_dates(
            item_type=ItemType.HOMEMADE_FROZEN,
            base_date=base_date,
            months_min=months_min,
            months_max=months_max,
        )

        assert optimal == date(2025, 2, 15)  # +3 months, into 2025
        assert maximum == date(2025, 5, 15)  # +6 months


class TestGetExpiryStatusMinMax:
    """Tests for new get_expiry_status with optimal/max dates."""

    def test_status_ok_before_optimal(self) -> None:
        """Test: Status 'ok' when today < optimal_date."""
        optimal_date = date.today() + timedelta(days=30)
        max_date = date.today() + timedelta(days=60)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "ok"

    def test_status_warning_at_optimal(self) -> None:
        """Test: Status 'warning' when today == optimal_date."""
        optimal_date = date.today()
        max_date = date.today() + timedelta(days=30)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "warning"

    def test_status_warning_between_optimal_and_critical_zone(self) -> None:
        """Test: Status 'warning' when optimal <= today < max - 3 days."""
        optimal_date = date.today() - timedelta(days=5)
        max_date = date.today() + timedelta(days=10)  # max - 3 = 7 days from now

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "warning"

    def test_status_critical_at_max_minus_3(self) -> None:
        """Test: Status 'critical' when today >= max_date - 3 days."""
        optimal_date = date.today() - timedelta(days=20)
        max_date = date.today() + timedelta(days=3)  # Exactly 3 days

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "critical"

    def test_status_critical_at_max_minus_2(self) -> None:
        """Test: Status 'critical' when 2 days before max."""
        optimal_date = date.today() - timedelta(days=20)
        max_date = date.today() + timedelta(days=2)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "critical"

    def test_status_critical_at_max(self) -> None:
        """Test: Status 'critical' when today == max_date."""
        optimal_date = date.today() - timedelta(days=30)
        max_date = date.today()

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "critical"

    def test_status_critical_past_max(self) -> None:
        """Test: Status 'critical' when today > max_date."""
        optimal_date = date.today() - timedelta(days=60)
        max_date = date.today() - timedelta(days=10)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        assert status == "critical"

    def test_status_with_best_before_date_overrides(self) -> None:
        """Test: best_before_date takes precedence when provided."""
        optimal_date = date.today() + timedelta(days=30)  # Would be "ok"
        max_date = date.today() + timedelta(days=60)
        best_before = date.today() + timedelta(days=1)  # Very close, should be critical

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
            best_before_date=best_before,
        )

        # best_before_date is used for items with MHD - should check against it
        assert status == "critical"

    def test_status_with_none_optimal_uses_max_only(self) -> None:
        """Test: When optimal_date is None, use max_date only."""
        max_date = date.today() + timedelta(days=10)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=max_date,
        )

        # With only max_date, check if within critical zone
        assert status == "ok"

    def test_status_with_none_max_uses_optimal_only(self) -> None:
        """Test: When max_date is None, use optimal_date only."""
        optimal_date = date.today() + timedelta(days=5)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=None,
        )

        assert status == "ok"

    def test_status_only_best_before(self) -> None:
        """Test: When only best_before_date is provided."""
        best_before = date.today() + timedelta(days=2)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
        )

        # Uses old logic: < 3 days = critical
        assert status == "critical"

    def test_status_boundary_at_4_days_before_max(self) -> None:
        """Test: Exactly 4 days before max should be warning (not critical)."""
        optimal_date = date.today() - timedelta(days=10)
        max_date = date.today() + timedelta(days=4)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
        )

        # 4 days > 3 days, so should be warning not critical
        assert status == "warning"
