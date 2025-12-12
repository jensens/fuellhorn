"""Unified Item Card Component - Mobile-First Card for displaying inventory items.

Based on Issue #173 and #210: 3-Zonen-Struktur für Card Redesign.
Same component used in both Dashboard and Vorrat views.

Card Structure (3-zone layout):
┌─────────────────────────────────────────────────┐
│ HEADER: Name                    [Expiry Info]   │
├─────────────────────────────────────────────────┤
│ BODY:                                           │
│   Menge                                    [-]  │
│   [Tag: State] [Tag: Category]                  │
├─────────────────────────────────────────────────┤
│ FOOTER: 📍 Lagerort                             │
└─────────────────────────────────────────────────┘
  ↑ Status-Border (4px, colored by expiry status)
"""

from ...models.item import Item
from ...models.item import ItemType
from ...services import item_service
from ...services import location_service
from ..theme import ITEM_TYPE_COLORS
from ..theme import get_contrast_text_color
from datetime import date
from nicegui import ui
from sqlmodel import Session
from typing import Callable


def _format_quantity_display(
    current_qty: float,
    initial_qty: float,
    unit: str,
) -> tuple[str, bool]:
    """Format quantity display with optional initial quantity.

    Args:
        current_qty: Current item quantity
        initial_qty: Initial quantity (before withdrawals)
        unit: Unit string (e.g., "g", "Stück")

    Returns:
        Tuple of (formatted string, has_withdrawals bool)
    """
    # Format numbers: remove decimal if whole number
    current = int(current_qty) if current_qty == int(current_qty) else current_qty
    initial = int(initial_qty) if initial_qty == int(initial_qty) else initial_qty

    has_withdrawals = initial_qty > current_qty

    if has_withdrawals:
        return f"{current}/{initial} {unit}", True
    else:
        return f"{current} {unit}", False


def _calculate_progress_percentage(current_qty: float, initial_qty: float) -> int:
    """Calculate progress percentage (current/initial * 100).

    Args:
        current_qty: Current item quantity
        initial_qty: Initial quantity (before withdrawals)

    Returns:
        Integer percentage (0-100)
    """
    if initial_qty <= 0:
        return 100
    percentage = (current_qty / initial_qty) * 100
    return int(round(percentage))


def _get_progress_color(percentage: int) -> str:
    """Get Quasar color name based on fill percentage.

    Args:
        percentage: Fill percentage (0-100)

    Returns:
        Quasar color name: "positive" (green), "warning" (gold), or "negative" (coral)
    """
    if percentage > 66:
        return "positive"  # Fern green
    elif percentage > 33:
        return "warning"  # Gold
    return "negative"  # Coral


# Item-Type Badge short labels (German)
ITEM_TYPE_SHORT_LABELS = {
    ItemType.PURCHASED_FRESH: "Frisch",
    ItemType.PURCHASED_FROZEN: "TK gekauft",
    ItemType.PURCHASED_THEN_FROZEN: "Eingefr.",
    ItemType.HOMEMADE_FROZEN: "Selbst eingefr.",
    ItemType.HOMEMADE_PRESERVED: "Eingemacht",
}


def get_status_css_class(status: str) -> str:
    """Get CSS class suffix for status (warning, critical, or empty for ok)."""
    if status == "critical":
        return "status-critical"
    elif status == "warning":
        return "status-warning"
    return ""


def get_status_text_class(status: str) -> str:
    """Get CSS text color class for status."""
    if status == "critical":
        return "sp-expiry-critical"
    elif status == "warning":
        return "sp-expiry-warning"
    return "sp-expiry-ok"


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


def get_expiry_badge_class(days_until: int) -> str:
    """Get CSS class for expiry badge based on days until expiry.

    Badge variants:
    - expired: days < 0 (red gradient, white text)
    - warning: days = 0-1 (orange gradient, white text)
    - soon: days = 2-7 (gold gradient, dark text)
    - ok: days > 7 (cream background, stone text)
    """
    if days_until < 0:
        return "expired"
    elif days_until <= 1:
        return "warning"
    elif days_until <= 7:
        return "soon"
    else:
        return "ok"


def get_expiry_badge_text(expiry_date: date, item_type: ItemType) -> str:
    """Get display text for expiry badge.

    Args:
        expiry_date: The expiry/best-before date
        item_type: Type of item (frozen items always show date format)

    Returns:
        Badge text: "Abgelaufen", "Heute", "Morgen", "in X Tagen", or date format
    """
    today = date.today()
    days_until = (expiry_date - today).days

    # Frozen items always show date format
    is_frozen = item_type in (
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    )

    if is_frozen:
        return expiry_date.strftime("%d.%m.%y")

    # Non-frozen items show relative text for near dates
    if days_until < 0:
        return "Abgelaufen"
    elif days_until == 0:
        return "Heute"
    elif days_until == 1:
        return "Morgen"
    elif days_until <= 7:
        return f"in {days_until} Tagen"
    else:
        return expiry_date.strftime("%d.%m.%y")


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
    status_css_class = get_status_css_class(status)

    # Get expiry badge info
    badge_class = get_expiry_badge_class(days_until)
    badge_text = get_expiry_badge_text(effective_expiry, item.item_type)

    # Get initial quantity and format display
    initial_qty = item_service.get_item_initial_quantity(session, item.id)  # type: ignore[arg-type]
    qty_display, has_withdrawals = _format_quantity_display(item.quantity, initial_qty, item.unit)

    # Get item type badge info
    type_label = ITEM_TYPE_SHORT_LABELS.get(item.item_type, str(item.item_type.value))
    type_color = ITEM_TYPE_COLORS.get(item.item_type, "#6B7280")

    # Create card with status border using Solarpunk theme classes
    card_classes = f"sp-item-card w-full {status_css_class}"

    with ui.card().classes(card_classes):
        # 3-Zone Grid Layout: header, body, footer
        # Grid: 2 columns (content + action), 3 rows (header, body, footer)
        with (
            ui.element("div")
            .classes("card-content")
            .style(
                "display: grid; "
                "grid-template-columns: 1fr auto; "
                "grid-template-rows: auto auto auto; "
                "gap: 8px 16px; "
                "width: 100%;"
            )
        ):
            # === HEADER ZONE ===
            # Name + Expiry (spans full width)
            with (
                ui.element("div")
                .classes("card-header")
                .style(
                    "grid-column: 1 / -1; "
                    "display: flex; "
                    "align-items: flex-start; "
                    "justify-content: space-between; "
                    "gap: 12px;"
                )
            ):
                # Product name (truncate on overflow)
                ui.label(item.product_name).classes("font-semibold text-base truncate").style(
                    "line-height: 1.3; flex: 1; min-width: 0;"
                )

                # Expiry badge (color-coded, Issue #212)
                ui.label(badge_text).classes(f"expiry-badge {badge_class}")

            # === BODY ZONE ===
            # Quantity + Progress Bar + Tags (left side)
            with (
                ui.element("div")
                .classes("card-body")
                .style("grid-column: 1; display: flex; flex-direction: column; gap: 8px;")
            ):
                # Amount section: Quantity + Progress bar (if partial withdrawal)
                with ui.row().classes("items-center gap-3 w-full"):
                    # Quantity display
                    qty_classes = "text-sm text-gray-700"
                    if has_withdrawals:
                        qty_classes = "text-sm text-amber-700"
                    ui.label(qty_display).classes(qty_classes).style("font-weight: 600; min-width: 70px;")

                    # Progress bar (only shown when partial withdrawal exists)
                    if has_withdrawals:
                        percentage = _calculate_progress_percentage(item.quantity, initial_qty)
                        progress_color = _get_progress_color(percentage)
                        # Quasar linear progress with aria-label for accessibility
                        ui.linear_progress(
                            value=percentage / 100,
                            color=progress_color,
                            size="8px",
                            show_value=False,
                        ).props(f'aria-label="Restmenge: {percentage}%" rounded').classes("flex-1").style(
                            "border-radius: 10px;"
                        )
                        # Show percentage text for accessibility
                        ui.label(f"{percentage}%").classes("text-xs text-stone").style("min-width: 35px;")

                # Tags: Item-Type + Category
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    # Item-Type Badge with 15% opacity background
                    ui.label(type_label).classes("text-xs px-2 py-0.5 rounded").style(
                        f"background-color: {type_color}26; color: {type_color}; font-weight: 500;"
                    )

                    # Category badge (if exists)
                    if category:
                        cat_color = category.color or "#6B7280"
                        cat_text_color = get_contrast_text_color(cat_color)
                        ui.label(category.name).classes("text-xs px-2 py-0.5 rounded").style(
                            f"background-color: {cat_color}; color: {cat_text_color}; font-weight: 500;"
                        )

            # Quick-Action Button (right side, spans body + footer rows)
            with (
                ui.element("div")
                .classes("quick-action-zone")
                .style("grid-column: 2; grid-row: 2 / 4; display: flex; align-items: center; justify-content: center;")
            ):
                # Round minus button for consume action (Issue #213)
                if on_consume:
                    ui.button(
                        icon="remove",
                        on_click=lambda i=item: on_consume(i),
                    ).classes("sp-quick-action").props("round flat")

            # === FOOTER ZONE ===
            # Location only
            with (
                ui.element("div")
                .classes("card-footer")
                .style("grid-column: 1; display: flex; align-items: center; gap: 6px;")
            ):
                location_style = "font-size: 0.8rem; color: var(--stone, #A39E93);"
                if location_color:
                    location_style = f"font-size: 0.8rem; color: {location_color};"
                ui.label(f"📍 {location_name}").style(location_style)

        # Click handler for entire card (if provided)
        if on_click:
            # Make card clickable
            ui.card().on("click", lambda: on_click(item))
