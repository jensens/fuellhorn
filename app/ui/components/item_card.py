"""Unified Item Card Component - Mobile-First Card for displaying inventory items.

Based on Issue #173: Einheitliches Card-Design für Dashboard & Vorrat.
Same component used in both Dashboard and Vorrat views.

Card Structure (3-line version):
┌─────────────────────────────────────────────────────────┐
│ ▌ Name                                MHD      [ENTN.] │
│ ▌ Menge · [Item-Type Badge]           Morgen           │
│ ▌ 📍 Lagerort   [Kategorie]                            │
└─────────────────────────────────────────────────────────┘
  ↑ Status-Border (4px, colored by expiry status)
"""

from ...models.item import Item
from ...models.item import ItemType
from ...services import item_service
from ...services import location_service
from ..theme import ITEM_TYPE_COLORS
from ..theme import STATUS_COLORS
from ..theme import get_contrast_text_color
from datetime import date
from nicegui import ui
from sqlmodel import Session
from typing import Callable


# Item-Type Badge short labels (German)
ITEM_TYPE_SHORT_LABELS = {
    ItemType.PURCHASED_FRESH: "Frisch",
    ItemType.PURCHASED_FROZEN: "TK gekauft",
    ItemType.PURCHASED_THEN_FROZEN: "Eingefr.",
    ItemType.HOMEMADE_FROZEN: "Selbst eingefr.",
    ItemType.HOMEMADE_PRESERVED: "Eingemacht",
}


def get_status_color(status: str) -> str:
    """Get Tailwind color class for status."""
    return STATUS_COLORS.get(status, "gray-500")


def _format_expiry_display(expiry_date: date, item_type: ItemType) -> tuple[str, str]:
    """Calculate expiry display label and value.

    Returns:
        Tuple of (label, value) for display.
        Label is "MHD" or "Ablauf".
        Value is either date format or relative text.
    """
    today = date.today()
    days_until = (expiry_date - today).days

    # Frozen items always show date format
    is_frozen = item_type in (
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    )

    if is_frozen or days_until > 7:
        # Show date format: TT.MM.JJ
        return "MHD", expiry_date.strftime("%d.%m.%y")
    elif days_until < 0:
        return "Ablauf", "Abgelaufen"
    elif days_until == 0:
        return "Ablauf", "Heute"
    elif days_until == 1:
        return "Ablauf", "Morgen"
    else:
        return "Ablauf", f"in {days_until} Tagen"


def _calculate_status(days_until: int) -> str:
    """Calculate status based on days until expiry."""
    if days_until < 3:
        return "critical"
    elif days_until <= 7:
        return "warning"
    else:
        return "ok"


def create_item_card(
    item: Item,
    session: Session,
    on_click: Callable[[Item], None] | None = None,
    on_consume: Callable[[Item], None] | None = None,
) -> None:
    """Create a unified, mobile-optimized item card component.

    Used in both Dashboard and Vorrat views. Dashboard provides on_consume
    callback to show the consume button.

    Args:
        item: The item to display
        session: Database session for fetching related data
        on_click: Optional callback when card is clicked
        on_consume: Optional callback for consume button (shows button if provided)
    """
    # Get related data
    try:
        location = location_service.get_location(session, item.location_id)
        location_name = location.name
        location_color = location.color
    except ValueError:
        location_name = f"Lagerort {item.location_id}"
        location_color = None

    category = item_service.get_item_category(session, item.id)  # type: ignore[arg-type]

    # Get expiry info (optimal_date, max_date, best_before_date)
    optimal_date, max_date, mhd_date = item_service.get_item_expiry_info(
        session,
        item.id,  # type: ignore[arg-type]
    )

    # Determine effective expiry date
    if mhd_date is not None:
        effective_expiry = mhd_date
    elif optimal_date is not None:
        effective_expiry = optimal_date
    else:
        effective_expiry = item.best_before_date

    # Calculate status
    days_until = (effective_expiry - date.today()).days
    status = _calculate_status(days_until)
    status_color = get_status_color(status)

    # Get expiry display
    expiry_label, expiry_value = _format_expiry_display(effective_expiry, item.item_type)

    # Format quantity (remove decimal if whole number)
    qty = int(item.quantity) if item.quantity == int(item.quantity) else item.quantity

    # Get item type badge info
    type_label = ITEM_TYPE_SHORT_LABELS.get(item.item_type, str(item.item_type.value))
    type_color = ITEM_TYPE_COLORS.get(item.item_type, "#6B7280")

    # Create card with status border
    card_classes = f"w-full mb-2 border-l-4 border-{status_color}"

    with ui.card().classes(card_classes).style("min-height: 48px; padding: 12px;"):
        # Main grid: left content + right column (date + button)
        with ui.row().classes("w-full items-start justify-between gap-2"):
            # Left column: 3 lines of item info
            with ui.column().classes("flex-1 gap-0.5 min-w-0"):
                # Line 1: Product name (truncate on overflow)
                ui.label(item.product_name).classes("font-semibold text-base truncate w-full").style(
                    "line-height: 1.3;"
                )

                # Line 2: Quantity + Item-Type Badge
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"{qty} {item.unit}").classes("text-sm text-gray-700")

                    # Item-Type Badge with 15% opacity background, text in full color
                    ui.label(type_label).classes("text-xs px-2 py-0.5 rounded").style(
                        f"background-color: {type_color}26; color: {type_color}; font-weight: 500;"
                    )

                # Line 3: Location + Category
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    # Location with icon
                    location_style = ""
                    if location_color:
                        location_style = f"color: {location_color};"
                    ui.label(f"📍 {location_name}").classes("text-xs text-gray-600").style(location_style)

                    # Category badge (if exists)
                    if category:
                        cat_color = category.color or "#6B7280"
                        cat_text_color = get_contrast_text_color(cat_color)
                        ui.label(category.name).classes("text-xs px-2 py-0.5 rounded").style(
                            f"background-color: {cat_color}; color: {cat_text_color}; font-weight: 500;"
                        )

            # Right column: Expiry info + optional button
            with ui.column().classes("items-end gap-1 shrink-0"):
                # Expiry label (small, muted)
                ui.label(expiry_label).classes("text-xs text-gray-400")

                # Expiry value (bold, colored by status)
                ui.label(expiry_value).classes(f"text-sm font-bold text-{status_color}")

                # Consume button (if callback provided)
                if on_consume:
                    ui.button(
                        "Entn.",
                        on_click=lambda i=item: on_consume(i),
                    ).props("size=sm dense").classes("mt-1").style(
                        f"background-color: var(--q-{status_color.replace('-', '')}, #ef4444);"
                    )

        # Click handler for entire card (if provided)
        if on_click:
            # Make card clickable
            ui.card().on("click", lambda: on_click(item))
