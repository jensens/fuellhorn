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
from ...models.location import LocationType
from ...services import expiry_service
from ...services import item_service
from ...services import location_service
from ...services.expiry_service import ExpiryView
from ..theme import ITEM_TYPE_COLORS
from ..theme import get_contrast_text_color
from ..theme.icons import create_icon
from ..utils.quantity import format_quantity
from .swipe_card import create_swipe_card
from datetime import date
from nicegui import ui
from sqlmodel import Session
from typing import Callable


# Location type to icon name mapping (Issue #197)
LOCATION_TYPE_ICONS: dict[LocationType, str] = {
    LocationType.FROZEN: "locations/freezer",
    LocationType.CHILLED: "locations/fridge",
    LocationType.AMBIENT: "locations/pantry",
}


def get_location_icon_name(location_type: LocationType) -> str:
    """Get the icon name for a location type.

    Args:
        location_type: The temperature zone of the storage location

    Returns:
        Icon name in format "category/icon-name" for use with create_icon()
    """
    return LOCATION_TYPE_ICONS.get(location_type, "locations/pantry")


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
    current = format_quantity(current_qty)
    initial = format_quantity(initial_qty)

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


def get_expiry_badge_class(status: str, days_until: int | None) -> str:
    """Map the service status to the badge CSS variant (presentation only, Issue #363).

    Badge variants:
    - expired: critical and the display date has passed (red gradient)
    - warning: critical, display date today or upcoming (orange gradient)
    - soon: warning, e.g. past the optimal date but before the maximum (gold gradient)
    - ok: ok (cream)
    - unknown: no expiry data available (grey)
    """
    if status == "unknown":
        return "unknown"
    if status == "critical":
        return "expired" if days_until is not None and days_until < 0 else "warning"
    if status == "warning":
        return "soon"
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
    on_partial_consume: Callable[[Item], None] | None = None,
    on_consume_all: Callable[[Item], None] | None = None,
    on_edit: Callable[[Item], None] | None = None,
    expiry_view: ExpiryView | None = None,
) -> None:
    """Create a unified, mobile-optimized item card component.

    Used in both Dashboard and Vorrat views. Dashboard provides on_consume
    callback to show the consume button.

    Swipe actions (Issue #214):
    - Swipe left: Teil (partial) + Alles (consume all)
    - Swipe right: Edit

    Args:
        item: The item to display
        session: Database session for fetching related data
        on_click: Optional callback when card is clicked
        on_consume: Optional callback for consume button (shows button if provided)
        on_partial_consume: Optional callback for swipe partial consume action
        on_consume_all: Optional callback for swipe consume all action
        on_edit: Optional callback for swipe edit action
        expiry_view: Precomputed expiry status (lists compute it in bulk); fetched if None
    """
    # Get related data
    try:
        location = location_service.get_location(session, item.location_id)
        location_name = location.name
        location_color = location.color
        location_type = location.location_type
    except ValueError:
        location_name = f"Lagerort {item.location_id}"
        location_color = None
        location_type = LocationType.AMBIENT  # Default fallback

    category = item_service.get_item_category(session, item.id)  # type: ignore[arg-type]

    # Expiry status comes exclusively from the service (Issue #363)
    view = expiry_view or expiry_service.get_item_expiry_view(session, item)
    status_css_class = get_status_css_class(view.status)
    if view.display_date is not None:
        days_until: int | None = (view.display_date - date.today()).days
        badge_text = get_expiry_badge_text(view.display_date, item.item_type)
    else:
        days_until = None
        badge_text = view.label
    badge_class = get_expiry_badge_class(view.status, days_until)

    # Get initial quantity and format display
    initial_qty = item_service.get_item_initial_quantity(session, item.id)  # type: ignore[arg-type]
    qty_display, has_withdrawals = _format_quantity_display(item.quantity, initial_qty, item.unit)

    # Get item type badge info
    type_label = ITEM_TYPE_SHORT_LABELS.get(item.item_type, str(item.item_type.value))
    type_color = ITEM_TYPE_COLORS.get(item.item_type, "#6B7280")

    # Create card with status border using Solarpunk theme classes
    card_classes = f"sp-item-card w-full {status_css_class}"

    # Check if swipe actions are enabled
    has_swipe = on_partial_consume or on_consume_all or on_edit

    def _create_card_content() -> None:
        """Create the card content (used inside swipe wrapper or standalone)."""
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
                    ui.label(item.product_name).mark(f"item-name-{item.id}").classes(
                        "font-semibold text-base truncate"
                    ).style("line-height: 1.3; flex: 1; min-width: 0;")

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
                    .style(
                        "grid-column: 2; grid-row: 2 / 4; display: flex; align-items: center; justify-content: center;"
                    )
                ):
                    # Round minus button for consume action (Issue #213)
                    if on_consume:
                        ui.button(
                            icon="remove",
                            on_click=lambda i=item: on_consume(i),
                        ).classes("sp-quick-action").props("round flat").mark(f"item-consume-{item.id}")

                # === FOOTER ZONE ===
                # Location with temperature icon (Issue #197)
                with (
                    ui.element("div")
                    .classes("card-footer")
                    .style("grid-column: 1; display: flex; align-items: center; gap: 6px;")
                ):
                    location_text_color = location_color or "var(--stone, #A39E93)"
                    # Temperature icon based on location type
                    icon_name = get_location_icon_name(location_type)
                    create_icon(icon_name, size="16px").style(f"color: {location_text_color};")
                    # Location name text
                    ui.label(location_name).style(f"font-size: 0.8rem; color: {location_text_color};")

            # Click handler for entire card (if provided)
            if on_click:
                # Make card clickable
                ui.card().on("click", lambda: on_click(item))

    # Render with or without swipe wrapper
    if has_swipe:
        create_swipe_card(
            content=_create_card_content,
            on_partial=lambda: on_partial_consume(item) if on_partial_consume else None,
            on_consume_all=lambda: on_consume_all(item) if on_consume_all else None,
            on_edit=lambda: on_edit(item) if on_edit else None,
            card_id=f"swipe-item-{item.id}",
        )
    else:
        _create_card_content()
