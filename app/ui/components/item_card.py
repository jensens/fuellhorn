"""Item Card Component - Mobile-First Card for displaying inventory items.

Based on requirements from Issue #7:
- Card shows product name, quantity, unit
- Card shows location and categories
- Card shows expiry date with status indicator
- Mobile-optimized (touch-friendly, min 48px height)
"""

from ...models.item import Item
from ...services import item_service
from ...services import location_service
from datetime import date
from nicegui import ui
from sqlmodel import Session
from typing import Callable


def get_expiry_status(expiry_date: date) -> str:
    """Get expiry status based on days until expiry.

    Args:
        expiry_date: The expiry date to check

    Returns:
        Status string: "critical" (< 3 days), "warning" (< 7 days), "ok" (>= 7 days)
    """
    days_until_expiry = (expiry_date - date.today()).days

    if days_until_expiry < 3:
        return "critical"
    elif days_until_expiry < 7:
        return "warning"
    else:
        return "ok"


def get_status_color(status: str) -> str:
    """Get Tailwind color class for status.

    Args:
        status: The expiry status

    Returns:
        Tailwind color class (e.g., "red-500")
    """
    colors = {
        "critical": "red-500",
        "warning": "orange-500",
        "ok": "green-500",
    }
    return colors.get(status, "gray-500")


def get_status_icon(status: str) -> str:
    """Get status icon emoji.

    Args:
        status: The expiry status

    Returns:
        Emoji icon for the status
    """
    icons = {
        "critical": "🔴",
        "warning": "🟡",
        "ok": "🟢",
    }
    return icons.get(status, "⚪")


def format_expiry_text(expiry_date: date) -> str:
    """Format expiry date as human-readable text.

    Args:
        expiry_date: The expiry date

    Returns:
        Formatted expiry text
    """
    days_until_expiry = (expiry_date - date.today()).days

    if days_until_expiry < 0:
        return "Abgelaufen"
    elif days_until_expiry == 0:
        return "Heute"
    elif days_until_expiry == 1:
        return "Morgen"
    else:
        return f"in {days_until_expiry} Tagen"


def create_item_card(
    item: Item,
    session: Session,
    on_click: Callable[[Item], None] | None = None,
) -> None:
    """Create a mobile-optimized item card component.

    Args:
        item: The item to display
        session: Database session for fetching related data
        on_click: Optional callback when card is clicked
    """
    # Get related data
    try:
        location = location_service.get_location(session, item.location_id)
        location_name = location.name
    except ValueError:
        location_name = f"Lagerort {item.location_id}"

    categories = item_service.get_item_categories(session, item.id)  # type: ignore[arg-type]
    category_names = [cat.name for cat in categories]

    # Calculate expiry status
    status = get_expiry_status(item.expiry_date)
    status_color = get_status_color(status)
    status_icon = get_status_icon(status)
    expiry_text = format_expiry_text(item.expiry_date)

    # Create card with status border
    card_classes = f"w-full mb-2 border-l-4 border-{status_color}"

    with ui.card().classes(card_classes).style("min-height: 48px"):
        # Main content row
        with ui.row().classes("w-full items-start justify-between"):
            # Left column: Item details
            with ui.column().classes("flex-1 gap-1"):
                # Product name with status icon
                ui.label(f"{status_icon} {item.product_name}").classes("font-medium text-base")

                # Quantity and unit (format without decimal places if whole number)
                qty = int(item.quantity) if item.quantity == int(item.quantity) else item.quantity
                ui.label(f"{qty} {item.unit}").classes("text-sm text-gray-700")

                # Location
                ui.label(f"📍 {location_name}").classes("text-xs text-gray-600")

                # Categories (if any)
                if category_names:
                    with ui.row().classes("gap-1 flex-wrap"):
                        for cat_name in category_names:
                            ui.badge(cat_name).props("outline color=primary")

            # Right column: Expiry info
            with ui.column().classes("items-end gap-1"):
                ui.label("Ablauf:").classes("text-xs text-gray-500")
                ui.label(expiry_text).classes(f"text-sm font-medium text-{status_color}")
                ui.label(item.expiry_date.strftime("%d.%m.%Y")).classes("text-xs text-gray-500")

        # Click handler if provided
        if on_click:
            ui.card().on("click", lambda: on_click(item))
