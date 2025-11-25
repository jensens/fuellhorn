"""UI Tests for Expiry Badge Component.

Tests the expiry_badge component which displays
a colored badge showing expiry status (red/yellow/green).

Note: These tests use unit test approach for the component logic
since NiceGUI UI elements require a running context.
"""

from app.ui.components.expiry_badge import _format_days_text


class TestFormatDaysText:
    """Tests for _format_days_text helper function."""

    def test_format_days_text_expired(self) -> None:
        """Test: Shows 'Abgelaufen' for expired items."""
        assert _format_days_text(-1) == "Abgelaufen"
        assert _format_days_text(-5) == "Abgelaufen"

    def test_format_days_text_today(self) -> None:
        """Test: Shows 'Heute' for items expiring today."""
        assert _format_days_text(0) == "Heute"

    def test_format_days_text_one_day(self) -> None:
        """Test: Shows singular 'Tag' for 1 day."""
        assert _format_days_text(1) == "1 Tag"

    def test_format_days_text_multiple_days(self) -> None:
        """Test: Shows plural 'Tage' for multiple days."""
        assert _format_days_text(2) == "2 Tage"
        assert _format_days_text(5) == "5 Tage"
        assert _format_days_text(10) == "10 Tage"
