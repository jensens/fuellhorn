"""Tests for configurable expiry thresholds.

Issue #135: Die Schwellwerte in get_expiry_status_minmax() sollen konfigurierbar sein.
"""

from app.services import expiry_calculator
from app.services import preferences_service
from datetime import date
from datetime import timedelta


class TestConfigurableThresholds:
    """Tests for configurable critical_days and warning_days parameters."""

    def test_default_critical_threshold_is_3_days(self) -> None:
        """Test: Default critical threshold is 3 days (backwards compatible)."""
        # 3 days before best_before -> should be critical with default
        best_before = date.today() + timedelta(days=2)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
        )

        assert status == "critical"

    def test_default_warning_threshold_is_7_days(self) -> None:
        """Test: Default warning threshold is 7 days (backwards compatible)."""
        # 5 days before best_before -> should be warning with default (between 3 and 7)
        best_before = date.today() + timedelta(days=5)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
        )

        assert status == "warning"

    def test_custom_critical_threshold_best_before(self) -> None:
        """Test: Custom critical threshold with best_before_date."""
        # 4 days before best_before -> default would be warning, but critical_days=5 makes it critical
        best_before = date.today() + timedelta(days=4)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=5,
        )

        assert status == "critical"

    def test_custom_warning_threshold_best_before(self) -> None:
        """Test: Custom warning threshold with best_before_date."""
        # 12 days before best_before -> default would be ok, but warning_days=14 makes it warning
        best_before = date.today() + timedelta(days=12)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            warning_days=14,
        )

        assert status == "warning"

    def test_custom_thresholds_ok_status(self) -> None:
        """Test: Status ok with custom thresholds when days exceed warning_days."""
        # 20 days before best_before -> ok even with warning_days=14
        best_before = date.today() + timedelta(days=20)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=5,
            warning_days=14,
        )

        assert status == "ok"

    def test_custom_critical_threshold_with_max_date_only(self) -> None:
        """Test: Custom critical threshold with only max_date."""
        # 4 days before max -> default would be ok, but critical_days=5 makes it critical
        max_date = date.today() + timedelta(days=4)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=max_date,
            critical_days=5,
        )

        assert status == "critical"

    def test_custom_critical_threshold_with_optimal_and_max(self) -> None:
        """Test: Custom critical threshold with both optimal and max dates."""
        # 4 days before max, past optimal -> default would be warning, critical_days=5 makes it critical
        optimal_date = date.today() - timedelta(days=10)
        max_date = date.today() + timedelta(days=4)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=optimal_date,
            max_date=max_date,
            critical_days=5,
        )

        assert status == "critical"

    def test_boundary_exactly_at_critical_threshold(self) -> None:
        """Test: Boundary case - exactly at critical threshold."""
        # Exactly 5 days before best_before with critical_days=5 -> should be critical
        best_before = date.today() + timedelta(days=5)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=5,
        )

        # days_until < critical_days, so 5 < 5 is False -> should NOT be critical
        # This is the existing behavior: < not <=
        assert status == "warning"

    def test_boundary_one_day_before_critical_threshold(self) -> None:
        """Test: Boundary case - one day before critical threshold."""
        # 4 days before best_before with critical_days=5 -> should be critical
        best_before = date.today() + timedelta(days=4)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=5,
        )

        # 4 < 5 is True -> critical
        assert status == "critical"

    def test_boundary_exactly_at_warning_threshold(self) -> None:
        """Test: Boundary case - exactly at warning threshold."""
        # Exactly 10 days before best_before with warning_days=10 -> should be warning
        best_before = date.today() + timedelta(days=10)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=3,
            warning_days=10,
        )

        # days_until <= warning_days, so 10 <= 10 is True -> warning
        assert status == "warning"

    def test_boundary_one_day_after_warning_threshold(self) -> None:
        """Test: Boundary case - one day after warning threshold."""
        # 11 days before best_before with warning_days=10 -> should be ok
        best_before = date.today() + timedelta(days=11)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=3,
            warning_days=10,
        )

        # 11 <= 10 is False -> ok
        assert status == "ok"

    def test_zero_thresholds(self) -> None:
        """Test: Edge case with zero thresholds (always ok unless expired)."""
        best_before = date.today() + timedelta(days=1)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=0,
            warning_days=0,
        )

        # 1 < 0 is False, 1 <= 0 is False -> ok
        assert status == "ok"

    def test_same_critical_and_warning_threshold(self) -> None:
        """Test: Edge case where critical and warning thresholds are the same."""
        best_before = date.today() + timedelta(days=5)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=5,
            warning_days=5,
        )

        # critical_days is checked first with <, warning_days with <=
        # 5 < 5 is False -> not critical
        # 5 <= 5 is True -> warning
        assert status == "warning"

    def test_critical_larger_than_warning_works(self) -> None:
        """Test: Edge case where critical_days > warning_days (unusual but valid)."""
        # This is an unusual config but should still work correctly
        best_before = date.today() + timedelta(days=8)

        status = expiry_calculator.get_expiry_status_minmax(
            optimal_date=None,
            max_date=None,
            best_before_date=best_before,
            critical_days=10,
            warning_days=5,
        )

        # 8 < 10 is True -> critical (critical checked first)
        assert status == "critical"


class TestGetExpiryThresholds:
    """Tests for get_expiry_thresholds helper function."""

    def test_returns_defaults_when_no_settings(self, session) -> None:  # type: ignore[no-untyped-def]
        """Test: Returns default values when no settings in database."""
        critical_days, warning_days = preferences_service.get_expiry_thresholds(session)

        assert critical_days == 3
        assert warning_days == 7

    def test_returns_configured_values(self, session, test_admin) -> None:  # type: ignore[no-untyped-def]
        """Test: Returns configured values from database."""
        # Set custom values
        preferences_service.set_system_setting(session, "expiry_critical_days", "5", test_admin.id)
        preferences_service.set_system_setting(session, "expiry_warning_days", "14", test_admin.id)

        critical_days, warning_days = preferences_service.get_expiry_thresholds(session)

        assert critical_days == 5
        assert warning_days == 14

    def test_returns_partial_configured_values(self, session, test_admin) -> None:  # type: ignore[no-untyped-def]
        """Test: Returns mix of default and configured values."""
        # Only set critical_days
        preferences_service.set_system_setting(session, "expiry_critical_days", "10", test_admin.id)

        critical_days, warning_days = preferences_service.get_expiry_thresholds(session)

        assert critical_days == 10
        assert warning_days == 7  # Default
