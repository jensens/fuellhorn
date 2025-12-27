"""Tests for date utility functions.

Issue #248: Relative date formatting for recently added items.
"""

from app.ui.utils.date_utils import format_relative_date
from datetime import datetime
from datetime import timedelta


def test_format_relative_date_today() -> None:
    """Test that today's date shows 'Heute'."""
    now = datetime.now()
    assert format_relative_date(now) == "Heute"


def test_format_relative_date_yesterday() -> None:
    """Test that yesterday's date shows 'Gestern'."""
    yesterday = datetime.now() - timedelta(days=1)
    assert format_relative_date(yesterday) == "Gestern"


def test_format_relative_date_weekday_2_days_ago() -> None:
    """Test that 2 days ago shows weekday name."""
    two_days_ago = datetime.now() - timedelta(days=2)
    weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    expected = weekday_names[two_days_ago.weekday()]
    assert format_relative_date(two_days_ago) == expected


def test_format_relative_date_weekday_6_days_ago() -> None:
    """Test that 6 days ago shows weekday name."""
    six_days_ago = datetime.now() - timedelta(days=6)
    weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    expected = weekday_names[six_days_ago.weekday()]
    assert format_relative_date(six_days_ago) == expected


def test_format_relative_date_7_days_ago_shows_date() -> None:
    """Test that 7 days ago shows formatted date."""
    seven_days_ago = datetime.now() - timedelta(days=7)
    expected = seven_days_ago.strftime("%d.%m.")
    assert format_relative_date(seven_days_ago) == expected


def test_format_relative_date_older_shows_date() -> None:
    """Test that older dates show formatted date."""
    old_date = datetime.now() - timedelta(days=30)
    expected = old_date.strftime("%d.%m.")
    assert format_relative_date(old_date) == expected


def test_format_relative_date_future_shows_date() -> None:
    """Test that future dates show formatted date."""
    future = datetime.now() + timedelta(days=5)
    expected = future.strftime("%d.%m.")
    assert format_relative_date(future) == expected
