"""Tests for expiry status calculation.

Tests the get_expiry_status function which determines
whether an item is critical (red), warning (yellow), or ok (green).
"""

from datetime import date, timedelta

from app.services import expiry_calculator


class TestGetExpiryStatus:
    """Tests for get_expiry_status function."""

    def test_expiry_status_critical_when_less_than_3_days(self) -> None:
        """Test: Status 'critical' when < 3 days until expiry."""
        expiry_date = date.today() + timedelta(days=2)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "critical"

    def test_expiry_status_critical_at_zero_days(self) -> None:
        """Test: Status 'critical' when expiry is today."""
        expiry_date = date.today()
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "critical"

    def test_expiry_status_critical_when_expired(self) -> None:
        """Test: Status 'critical' when already expired."""
        expiry_date = date.today() - timedelta(days=1)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "critical"

    def test_expiry_status_warning_at_3_days(self) -> None:
        """Test: Status 'warning' at exactly 3 days."""
        expiry_date = date.today() + timedelta(days=3)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "warning"

    def test_expiry_status_warning_at_6_days(self) -> None:
        """Test: Status 'warning' at 6 days (3-7 range)."""
        expiry_date = date.today() + timedelta(days=6)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "warning"

    def test_expiry_status_warning_at_7_days(self) -> None:
        """Test: Status 'warning' at exactly 7 days."""
        expiry_date = date.today() + timedelta(days=7)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "warning"

    def test_expiry_status_ok_at_8_days(self) -> None:
        """Test: Status 'ok' at 8 days (> 7 days)."""
        expiry_date = date.today() + timedelta(days=8)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "ok"

    def test_expiry_status_ok_at_30_days(self) -> None:
        """Test: Status 'ok' when many days remaining."""
        expiry_date = date.today() + timedelta(days=30)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "ok"


class TestGetDaysUntilExpiry:
    """Tests for get_days_until_expiry function."""

    def test_days_until_expiry_positive(self) -> None:
        """Test: Positive days when not expired."""
        expiry_date = date.today() + timedelta(days=5)
        days = expiry_calculator.get_days_until_expiry(expiry_date)
        assert days == 5

    def test_days_until_expiry_zero(self) -> None:
        """Test: Zero days when expiring today."""
        expiry_date = date.today()
        days = expiry_calculator.get_days_until_expiry(expiry_date)
        assert days == 0

    def test_days_until_expiry_negative(self) -> None:
        """Test: Negative days when already expired."""
        expiry_date = date.today() - timedelta(days=3)
        days = expiry_calculator.get_days_until_expiry(expiry_date)
        assert days == -3
