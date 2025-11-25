"""Expiry Badge Component - Shows expiry status with color coding.

Displays a badge with:
- Red: < 3 days (critical)
- Yellow: 3-7 days (warning)
- Green: > 7 days (ok)

Shows remaining days until expiry.
"""

from ...services.expiry_calculator import get_days_until_expiry
from ...services.expiry_calculator import get_expiry_status
from datetime import date
from nicegui import ui


# Color mapping for expiry status
STATUS_COLORS = {
    "critical": "bg-red-500 text-white",
    "warning": "bg-yellow-500 text-black",
    "ok": "bg-green-500 text-white",
}


def _format_days_text(days: int) -> str:
    """Format the days text for display.

    Args:
        days: Number of days until expiry (can be negative)

    Returns:
        Formatted text like "5 Tage", "1 Tag", "Heute", or "Abgelaufen"
    """
    if days < 0:
        return "Abgelaufen"
    elif days == 0:
        return "Heute"
    elif days == 1:
        return "1 Tag"
    else:
        return f"{days} Tage"


def create_expiry_badge(expiry_date: date) -> ui.badge:
    """Create an expiry status badge.

    Displays a colored badge showing the expiry status:
    - Red (critical): < 3 days until expiry
    - Yellow (warning): 3-7 days until expiry
    - Green (ok): > 7 days until expiry

    The badge shows the number of days remaining.

    Args:
        expiry_date: The expiry date of the item

    Returns:
        NiceGUI badge element
    """
    days = get_days_until_expiry(expiry_date)
    status = get_expiry_status(expiry_date)
    text = _format_days_text(days)
    color_classes = STATUS_COLORS[status]

    return ui.badge(text).classes(f"{color_classes} px-2 py-1 rounded-full text-xs font-medium")
