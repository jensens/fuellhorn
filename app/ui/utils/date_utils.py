"""Date utility functions for the UI.

Issue #248: Relative date formatting for recently added items.
"""

from datetime import datetime


# German weekday abbreviations (Monday = 0, Sunday = 6)
WEEKDAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


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
