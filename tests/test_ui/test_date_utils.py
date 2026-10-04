"""Tests for date utility functions.

Issue #248: Relative date formatting for recently added items. Feste Bezugszeit per
freezegun (Issue #392): vorher rechneten die Erwartungen mit ``datetime.now()`` und
konnten um Mitternacht kippen.
"""

from app.ui.utils.date_utils import format_relative_date
from datetime import datetime
from freezegun import freeze_time
import pytest


TODAY = "2026-10-04 12:00:00"  # ein Sonntag


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2026, 10, 4, 8, 0), "Heute"),
        (datetime(2026, 10, 3, 23, 59), "Gestern"),
        (datetime(2026, 10, 2, 12, 0), "Fr"),  # vor 2 Tagen → Wochentag
        (datetime(2026, 9, 28, 12, 0), "Mo"),  # vor 6 Tagen → Wochentag
        (datetime(2026, 9, 27, 12, 0), "27.09."),  # vor 7 Tagen → Datum
        (datetime(2026, 9, 4, 12, 0), "04.09."),  # vor 30 Tagen → Datum
        (datetime(2026, 10, 9, 12, 0), "09.10."),  # Zukunft → Datum
    ],
)
def test_format_relative_date(value: datetime, expected: str) -> None:
    with freeze_time(TODAY):
        assert format_relative_date(value) == expected
