"""Expiry Badge Component - Shows expiry status with color coding.

Displays a badge with:
- Red: critical (< 3 days before max or past max)
- Yellow: warning (past optimal but before max - 3 days)
- Green: ok (before optimal)

Shows remaining days until expiry.
"""

from ...services.expiry_calculator import get_days_until_expiry
from ...services.expiry_calculator import get_expiry_status
from ..theme.icons import create_icon
from datetime import date
from nicegui import ui
from typing import Any


# Color mapping for expiry status
STATUS_COLORS = {
    "critical": "bg-red-500 text-white",
    "warning": "bg-yellow-500 text-black",
    "ok": "bg-green-500 text-white",
}

# Tailwind text color classes for status
STATUS_TEXT_COLORS = {
    "critical": "text-red-500",
    "warning": "text-yellow-600",
    "ok": "text-green-500",
}

# Status icons mapping to custom SVG icons
STATUS_ICON_NAMES = {
    "critical": "status/critical",
    "warning": "status/warning",
    "ok": "status/ok",
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


def create_status_icon(
    status: str,
    size: str = "20px",
    classes: str = "",
) -> Any:
    """Create a status icon element using custom SVG icons.

    Uses the Solarpunk custom icons for status indicators.
    Color is controlled via CSS classes (text-red-500, etc.).

    Args:
        status: Expiry status ("critical", "warning", "ok")
        size: CSS size value (e.g., "20px", "1rem")
        classes: Additional CSS classes for styling

    Returns:
        NiceGUI html element containing the SVG icon
    """
    icon_name = STATUS_ICON_NAMES.get(status, "status/info")
    color_class = STATUS_TEXT_COLORS.get(status, "text-gray-500")
    return create_icon(icon_name, size=size, classes=f"{color_class} {classes}")


def get_status_text_color(status: str) -> str:
    """Get Tailwind text color class for given status.

    Args:
        status: Expiry status ("critical", "warning", "ok")

    Returns:
        Tailwind text color class
    """
    return STATUS_TEXT_COLORS.get(status, "text-gray-500")
