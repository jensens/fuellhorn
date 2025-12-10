"""Tests for expiry badge component."""

from app.ui.components.expiry_badge import STATUS_COLORS
from app.ui.components.expiry_badge import STATUS_ICON_NAMES
from app.ui.components.expiry_badge import STATUS_TEXT_COLORS
from app.ui.components.expiry_badge import _format_days_text
from app.ui.components.expiry_badge import get_status_text_color


class TestFormatDaysText:
    """Tests for _format_days_text function."""

    def test_negative_days_returns_abgelaufen(self) -> None:
        """Negative days should return 'Abgelaufen'."""
        assert _format_days_text(-1) == "Abgelaufen"
        assert _format_days_text(-5) == "Abgelaufen"
        assert _format_days_text(-100) == "Abgelaufen"

    def test_zero_days_returns_heute(self) -> None:
        """Zero days should return 'Heute'."""
        assert _format_days_text(0) == "Heute"

    def test_one_day_returns_singular(self) -> None:
        """One day should return '1 Tag' (singular)."""
        assert _format_days_text(1) == "1 Tag"

    def test_multiple_days_returns_plural(self) -> None:
        """Multiple days should return 'X Tage' (plural)."""
        assert _format_days_text(2) == "2 Tage"
        assert _format_days_text(5) == "5 Tage"
        assert _format_days_text(30) == "30 Tage"
        assert _format_days_text(365) == "365 Tage"


class TestGetStatusTextColor:
    """Tests for get_status_text_color function."""

    def test_critical_status(self) -> None:
        """Critical status should return red text color."""
        assert get_status_text_color("critical") == "text-red-500"

    def test_warning_status(self) -> None:
        """Warning status should return yellow text color."""
        assert get_status_text_color("warning") == "text-yellow-600"

    def test_ok_status(self) -> None:
        """OK status should return green text color."""
        assert get_status_text_color("ok") == "text-green-500"

    def test_unknown_status_returns_default(self) -> None:
        """Unknown status should return default gray color."""
        assert get_status_text_color("unknown") == "text-gray-500"
        assert get_status_text_color("") == "text-gray-500"
        assert get_status_text_color("invalid") == "text-gray-500"


class TestStatusColors:
    """Tests for STATUS_COLORS constant."""

    def test_has_all_statuses(self) -> None:
        """Should have color for all statuses."""
        assert "critical" in STATUS_COLORS
        assert "warning" in STATUS_COLORS
        assert "ok" in STATUS_COLORS

    def test_critical_has_red(self) -> None:
        """Critical should have red background."""
        assert "red" in STATUS_COLORS["critical"]

    def test_warning_has_yellow(self) -> None:
        """Warning should have yellow background."""
        assert "yellow" in STATUS_COLORS["warning"]

    def test_ok_has_green(self) -> None:
        """OK should have green background."""
        assert "green" in STATUS_COLORS["ok"]


class TestStatusTextColors:
    """Tests for STATUS_TEXT_COLORS constant."""

    def test_has_all_statuses(self) -> None:
        """Should have text color for all statuses."""
        assert "critical" in STATUS_TEXT_COLORS
        assert "warning" in STATUS_TEXT_COLORS
        assert "ok" in STATUS_TEXT_COLORS


class TestStatusIconNames:
    """Tests for STATUS_ICON_NAMES constant."""

    def test_has_all_statuses(self) -> None:
        """Should have icon name for all statuses."""
        assert "critical" in STATUS_ICON_NAMES
        assert "warning" in STATUS_ICON_NAMES
        assert "ok" in STATUS_ICON_NAMES

    def test_icon_names_have_status_prefix(self) -> None:
        """Icon names should have status/ prefix."""
        for name in STATUS_ICON_NAMES.values():
            assert name.startswith("status/")
