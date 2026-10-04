"""Date utility functions for the UI.

Issue #248: Relative date formatting for recently added items.
Issue #362: Conversion between German date strings (DD.MM.YYYY) and ``date``.
"""

from datetime import date
from datetime import datetime


# German weekday abbreviations (Monday = 0, Sunday = 6)
WEEKDAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

GERMAN_DATE_FORMAT = "%d.%m.%Y"
MONTH_FORMAT = "%m/%Y"


def parse_german_date(value: str | date | None) -> date | None:
    """Parse a German date string (DD.MM.YYYY) into a ``date``.

    Used as the ``forward`` converter when binding a date ``ui.input`` to form
    state: incomplete input (mask not yet filled), impossible dates and empty
    values yield ``None`` so that validation can reject them.

    Args:
        value: Input value; ``date`` objects pass through unchanged.

    Returns:
        The parsed date or ``None`` if the value is not a complete, valid date.
    """
    if value is None or isinstance(value, date):
        return value
    try:
        return datetime.strptime(value.strip(), GERMAN_DATE_FORMAT).date()
    except ValueError:
        return None


def format_german_date(value: date | None) -> str:
    """Format a ``date`` as German date string (DD.MM.YYYY); ``None`` becomes ``""``.

    Used as the ``backward`` converter when binding a date ``ui.input`` to form state.
    """
    if value is None:
        return ""
    return value.strftime(GERMAN_DATE_FORMAT)


def parse_date_input(value: str | date | None) -> tuple[date | None, bool]:
    """Liest ein Datum mit optionalem Tag (Issues #346, #347).

    Angenommen werden Tag, Monat und Jahr („15.03.2026“, „15/03/2026“) sowie Monat und Jahr
    („03/2026“, „03.2026“); Punkt und Schrägstrich sind gleichwertig, führende Nullen optional.
    Das Jahr muss vierstellig sein, weil „15.03.26“ zweideutig wäre.

    Returns:
        Datum und ob nur der Monat erfasst wurde. Unvollständige oder unmögliche Eingaben
        ergeben ``(None, False)``, damit die Validierung sie abweisen kann.
    """
    if value is None:
        return (None, False)
    if isinstance(value, date):
        return (value, False)
    parts = value.strip().replace("/", ".").split(".")
    if len(parts) not in (2, 3) or not all(part.strip().isdigit() for part in parts):
        return (None, False)
    numbers = [int(part) for part in parts]
    if len(str(numbers[-1])) != 4 or len(parts[-1].strip()) != 4:
        return (None, False)
    try:
        if len(numbers) == 2:
            month, year = numbers
            return (date(year, month, 1), True)
        day, month, year = numbers
        return (date(year, month, day), False)
    except ValueError:
        return (None, False)


def format_date_value(value: date | None, *, month_only: bool) -> str:
    """Zeigt ein Datum an: „15.03.2026“ tagesgenau, „03/2026“ monatsgenau, leer ohne Datum."""
    if value is None:
        return ""
    return value.strftime(MONTH_FORMAT if month_only else GERMAN_DATE_FORMAT)


def format_relative_date(dt: datetime) -> str:
    """Format a datetime as a relative date string (German).

    Returns:
        - "Heute" for today
        - "Gestern" for yesterday
        - Weekday abbreviation (Mo, Di, Mi, Do, Fr, Sa, So) for 2-6 days ago
        - Date format "DD.MM." for 7+ days ago or future dates

    Args:
        dt: The datetime to format

    Returns:
        Formatted date string
    """
    now = datetime.now()
    today = now.date()
    dt_date = dt.date()

    days_diff = (today - dt_date).days

    if days_diff == 0:
        return "Heute"
    elif days_diff == 1:
        return "Gestern"
    elif 2 <= days_diff <= 6:
        return WEEKDAY_NAMES[dt_date.weekday()]
    else:
        return dt_date.strftime("%d.%m.")
