"""Unit Tests: Konvertierung zwischen deutschem Datumsstring und ``date`` (Issue #362).

Die Datumsfelder im Wizard und Edit-View zeigen ``DD.MM.YYYY``; ``form_data``
hält ``date``-Objekte. Die Konvertierung muss unvollständige und unmögliche
Eingaben tolerant als ``None`` behandeln, damit die Validierung greift.
"""

from app.ui.utils.date_utils import format_german_date
from app.ui.utils.date_utils import parse_german_date
from datetime import date


def test_parse_german_date_returns_date() -> None:
    """'15.01.2027' wird zu date(2027, 1, 15)."""
    assert parse_german_date("15.01.2027") == date(2027, 1, 15)


def test_parse_german_date_incomplete_input_returns_none() -> None:
    """Unvollständige Eingabe (Maske noch nicht ausgefüllt) ergibt None."""
    assert parse_german_date("15.01.2") is None


def test_parse_german_date_impossible_date_returns_none() -> None:
    """Ein unmögliches Datum wie der 31.02. ergibt None."""
    assert parse_german_date("31.02.2027") is None


def test_parse_german_date_none_returns_none() -> None:
    """None (Feld geleert) ergibt None."""
    assert parse_german_date(None) is None


def test_parse_german_date_empty_string_returns_none() -> None:
    """Leerer String ergibt None."""
    assert parse_german_date("") is None


def test_parse_german_date_passes_through_date_objects() -> None:
    """Ein bereits konvertiertes date-Objekt wird unverändert zurückgegeben."""
    assert parse_german_date(date(2027, 1, 15)) == date(2027, 1, 15)


def test_format_german_date_formats_date() -> None:
    """date(2027, 1, 15) wird zu '15.01.2027'."""
    assert format_german_date(date(2027, 1, 15)) == "15.01.2027"


def test_format_german_date_none_returns_empty_string() -> None:
    """None wird zu '' (leeres Eingabefeld)."""
    assert format_german_date(None) == ""
