"""Datumseingabe mit optionalem Tag: Parsen und Anzeigen (Issues #346, #347).

Das Feld nimmt „15.03.2026“ und „03/2026“ an. Fehlt der Tag, ist das Datum der 1. des
Monats und das Kennzeichen gesetzt; angezeigt wird dann „03/2026“.
"""

from app.ui.utils.date_utils import format_date_value
from app.ui.utils.date_utils import parse_date_input
from datetime import date
import pytest


class TestParseDateInput:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("15.03.2026", (date(2026, 3, 15), False)),
            ("15/03/2026", (date(2026, 3, 15), False)),
            ("1.3.2026", (date(2026, 3, 1), False)),
            ("03/2026", (date(2026, 3, 1), True)),
            ("03.2026", (date(2026, 3, 1), True)),
            ("3.2026", (date(2026, 3, 1), True)),
            ("12/2026", (date(2026, 12, 1), True)),
        ],
    )
    def test_accepted_forms(self, text: str, expected: tuple[date, bool]) -> None:
        assert parse_date_input(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "   ",
            "abc",
            "31.02.2026",  # Tag gibt es im Februar nicht
            "13/2026",  # Monat 13
            "00/2026",
            "2026",  # Jahr allein ist keine Monatsangabe
            "15.03",  # Jahr fehlt
            "15.03.26",  # zweistelliges Jahr ist zweideutig
        ],
    )
    def test_rejected_input_yields_no_date(self, text: str) -> None:
        assert parse_date_input(text) == (None, False)

    def test_date_objects_pass_through(self) -> None:
        assert parse_date_input(date(2026, 3, 15)) == (date(2026, 3, 15), False)
        assert parse_date_input(None) == (None, False)


class TestFormatDateValue:
    def test_day_precise_dates_keep_the_german_form(self) -> None:
        assert format_date_value(date(2026, 3, 15), month_only=False) == "15.03.2026"

    def test_month_only_dates_show_month_and_year(self) -> None:
        assert format_date_value(date(2026, 3, 1), month_only=True) == "03/2026"

    def test_missing_date_is_empty(self) -> None:
        assert format_date_value(None, month_only=False) == ""
        assert format_date_value(None, month_only=True) == ""

    @pytest.mark.parametrize(
        ("value", "month_only"),
        [(date(2026, 3, 15), False), (date(2026, 3, 1), True), (date(2026, 12, 1), True)],
    )
    def test_round_trip(self, value: date, month_only: bool) -> None:
        assert parse_date_input(format_date_value(value, month_only=month_only)) == (value, month_only)
