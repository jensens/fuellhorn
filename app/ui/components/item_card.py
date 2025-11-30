"""Item Card Component - Mobile-First Card for displaying inventory items.

Based on requirements from Issue #7 and #109:
- Card shows product name, quantity, unit
- Card shows location and categories
- Card shows expiry date(s) with status indicator:
  - For shelf-life items: Optimal + Max dates
  - For MHD items: Single best-before date
- Mobile-optimized (touch-friendly, min 48px height)
"""

from ...models.item import Item
from ...services import item_service
from ...services import location_service
from ...services.expiry_calculator import get_expiry_status_minmax
from datetime import date
from nicegui import ui
from sqlmodel import Session
from typing import Callable


# Status color mapping (Tailwind classes without prefix)
STATUS_COLORS = {
    "critical": "red-500",
    "warning": "orange-500",
    "ok": "green-500",
}

# Status icons
STATUS_ICONS = {
    "critical": "🔴",
    "warning": "🟡",
    "ok": "🟢",
}


def get_status_color(status: str) -> str:
    """Get Tailwind color class for status."""
    return STATUS_COLORS.get(status, "gray-500")


def get_status_icon(status: str) -> str:
    """Get status icon emoji."""
    return STATUS_ICONS.get(status, "⚪")


def _render_expiry_shelf_life(
    optimal_date: date,
    max_date: date,
    status: str,
    status_color: str,
) -> None:
    """Render expiry info for shelf-life items (two dates)."""
    with ui.column().classes("items-end gap-0"):
        # Optimal date
        ui.label("Optimal bis:").classes("text-xs text-gray-500")
        ui.label(optimal_date.strftime("%d.%m.%Y")).classes(f"text-sm font-medium text-{status_color}")
        # Max date
        ui.label("Max. bis:").classes("text-xs text-gray-500 mt-1")
        ui.label(max_date.strftime("%d.%m.%Y")).classes("text-xs text-gray-600")


def _render_expiry_mhd(
    best_before_date: date,
    status_color: str,
) -> None:
    """Render expiry info for MHD items (single date)."""
    with ui.column().classes("items-end gap-0"):
        ui.label("MHD:").classes("text-xs text-gray-500")
        ui.label(best_before_date.strftime("%d.%m.%Y")).classes(f"text-sm font-medium text-{status_color}")


def _render_expiry_fallback(
    expiry_date: date,
    status_color: str,
) -> None:
    """Render expiry info fallback (when no shelf life config)."""
    with ui.column().classes("items-end gap-0"):
        ui.label("Ablauf:").classes("text-xs text-gray-500")
        ui.label(expiry_date.strftime("%d.%m.%Y")).classes(f"text-sm font-medium text-{status_color}")


def create_item_card(
    item: Item,
    session: Session,
    on_click: Callable[[Item], None] | None = None,
) -> None:
    """Create a mobile-optimized item card component.

    Displays expiry info based on item type:
    - Shelf-life items (frozen/preserved): Shows optimal + max dates
    - MHD items (purchased fresh/frozen): Shows single best-before date

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

    category = item_service.get_item_category(session, item.id)  # type: ignore[arg-type]
    category_names = [category.name] if category else []

    # Get expiry info (optimal_date, max_date, best_before_date)
    optimal_date, max_date, best_before_date = item_service.get_item_expiry_info(
        session,
        item.id,  # type: ignore[arg-type]
    )

    # Calculate status based on the dates
    status = get_expiry_status_minmax(optimal_date, max_date, best_before_date)
    status_color = get_status_color(status)
    status_icon = get_status_icon(status)

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
            if optimal_date is not None and max_date is not None:
                # Shelf-life items: show two dates
                _render_expiry_shelf_life(optimal_date, max_date, status, status_color)
            elif best_before_date is not None:
                # MHD items: show single date
                _render_expiry_mhd(best_before_date, status_color)
            else:
                # Fallback: use item.best_before_date
                _render_expiry_fallback(item.best_before_date, status_color)

        # Click handler if provided
        if on_click:
            ui.card().on("click", lambda: on_click(item))
