"""Unified Item Card Component - Mobile-First Card for displaying inventory items.

Based on Issue #173 and #210: 3-Zonen-Struktur für Card Redesign.
Same component used in both Dashboard and Vorrat views.

Card Structure (3-zone layout):
┌─────────────────────────────────────────────────┐
│ HEADER: Name                    [Expiry Badge]  │
├─────────────────────────────────────────────────┤
│ BODY:                                           │
│   Menge [Progress Bar]                          │
│   [Tag: State] [Tag: Category]                  │
├─────────────────────────────────────────────────┤
│ FOOTER: 📍 Lagerort                             │
└─────────────────────────────────────────────────┘
  ↑ Status-Border (4px, colored by expiry status)

Swipe Actions (Issue #214):
┌──────────────┬────────────────────────┬──────────────┬──────────────┐
│    Edit      │      Card Content      │    Teil      │    Alles     │
│   (blau)     │       (swipeable)      │   (gold)     │   (grün)     │
└──────────────┴────────────────────────┴──────────────┴──────────────┘
  Swipe →                                              ← Swipe
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


# Track if swipe JS has been added to avoid duplicates
_swipe_js_added = False


def _add_swipe_javascript() -> None:
    """Add JavaScript for bidirectional swipe gestures on item cards.

    This function adds event listeners for touch and mouse events to enable
    swiping on cards marked with data-swipeable attribute.

    Swipe behavior:
    - Swipe left (negative X): Shows consume actions (Teil/Alles)
    - Swipe right (positive X): Shows edit action
    - Threshold based snapping
    - Click outside to close
    """
    global _swipe_js_added
    if _swipe_js_added:
        return
    _swipe_js_added = True

    swipe_js = """
    (function() {
        // Only initialize once
        if (window._fuellhornSwipeInitialized) return;
        window._fuellhornSwipeInitialized = true;

        function initSwipeCards() {
            document.querySelectorAll('[data-swipeable]').forEach(card => {
                // Skip already initialized cards
                if (card._swipeInitialized) return;
                card._swipeInitialized = true;

                let startX = 0;
                let currentX = 0;
                let isDragging = false;

                const maxLeft = parseInt(card.dataset.maxLeft || '-160');
                const maxRight = parseInt(card.dataset.maxRight || '80');

                const onStart = (e) => {
                    // Don't start swipe if clicking a button
                    if (e.target.closest('button')) return;

                    isDragging = true;
                    startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
                    currentX = startX;
                    card.style.transition = 'none';
                    card.style.cursor = 'grabbing';
                };

                const onMove = (e) => {
                    if (!isDragging) return;
                    currentX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
                    const diff = currentX - startX;

                    // Clamp to max values
                    const translate = Math.max(maxLeft, Math.min(maxRight, diff));
                    card.style.transform = `translateX(${translate}px)`;
                };

                const onEnd = () => {
                    if (!isDragging) return;
                    isDragging = false;
                    card.style.cursor = 'grab';
                    card.style.transition = 'transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';

                    const diff = currentX - startX;

                    // Threshold-based snapping
                    if (diff < -80 && maxLeft < 0) {
                        // Swiped left enough -> show consume actions
                        card.style.transform = `translateX(${maxLeft}px)`;
                        card.dataset.swiped = 'left';
                    } else if (diff > 40 && maxRight > 0) {
                        // Swiped right enough -> show edit action
                        card.style.transform = `translateX(${maxRight}px)`;
                        card.dataset.swiped = 'right';
                    } else {
                        // Not enough swipe -> reset
                        card.style.transform = 'translateX(0)';
                        card.dataset.swiped = '';
                    }
                };

                // Mouse events
                card.addEventListener('mousedown', onStart);
                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onEnd);

                // Touch events
                card.addEventListener('touchstart', onStart, { passive: true });
                card.addEventListener('touchmove', onMove, { passive: true });
                card.addEventListener('touchend', onEnd);

                // Click outside to close
                document.addEventListener('click', (e) => {
                    if (card.dataset.swiped && !card.contains(e.target)) {
                        card.style.transition = 'transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                        card.style.transform = 'translateX(0)';
                        card.dataset.swiped = '';
                    }
                });
            });
        }

        // Initialize on DOM ready and after NiceGUI updates
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSwipeCards);
        } else {
            initSwipeCards();
        }

        // Re-initialize after page updates (NiceGUI dynamic content)
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    setTimeout(initSwipeCards, 100);
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    """

    ui.run_javascript(swipe_js)


def create_item_card(
    item: Item,
    session: Session,
    on_click: Callable[[Item], None] | None = None,
    on_consume: Callable[[Item], None] | None = None,
    on_partial_consume: Callable[[Item], None] | None = None,
    on_edit: Callable[[Item], None] | None = None,
) -> None:
    """Create a unified, mobile-optimized item card component with swipe actions.

    Used in both Dashboard and Vorrat views. Dashboard provides on_consume
    callback to show the consume button.

    Swipe Actions (Issue #214):
    - Swipe right: Shows "Edit" button (requires on_edit callback)
    - Swipe left: Shows "Teil" and "Alles" buttons (requires on_partial_consume/on_consume)

    Args:
        item: The item to display
        session: Database session for fetching related data
        on_click: Optional callback when card is clicked
        on_consume: Optional callback for full consume action
        on_partial_consume: Optional callback for partial consume action
        on_edit: Optional callback for edit action
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

    # Get expiry badge info (Issue #212)
    badge_class = get_expiry_badge_class(days_until)
    badge_text = get_expiry_badge_text(effective_expiry, item.item_type)

    # Get initial quantity and format display
    initial_qty = item_service.get_item_initial_quantity(session, item.id)  # type: ignore[arg-type]
    qty_display, has_withdrawals = _format_quantity_display(item.quantity, initial_qty, item.unit)

    # Get item type badge info
    type_label = ITEM_TYPE_SHORT_LABELS.get(item.item_type, str(item.item_type.value))
    type_color = ITEM_TYPE_COLORS.get(item.item_type, "#6B7280")

    # Determine if swipe actions should be enabled
    has_swipe_actions = on_edit or on_partial_consume or on_consume

    # Create card with status border using Solarpunk theme classes
    card_classes = f"sp-item-card w-full {status_css_class}"

    # Swipe container wrapper
    with (
        ui.element("div")
        .classes("sp-swipe-container")
        .style("position: relative; overflow: hidden; border-radius: var(--sp-radius-lg, 16px); margin-bottom: 8px;")
    ):
        # === SWIPE ACTIONS LEFT (Edit) - shown on swipe right ===
        if on_edit:
            with (
                ui.element("div")
                .classes("sp-swipe-actions-left")
                .style(
                    "position: absolute; top: 0; left: 0; bottom: 0; width: 80px; "
                    "display: flex; align-items: stretch; z-index: 1;"
                )
            ):
                ui.button(
                    "Edit",
                    icon="edit",
                    on_click=lambda i=item: on_edit(i),
                ).classes("sp-swipe-action-edit").style(
                    "flex: 1; border-radius: 0; "
                    "background: linear-gradient(135deg, #5BA3C6 0%, #87CEEB 100%); "
                    "color: white; display: flex; flex-direction: column; "
                    "align-items: center; justify-content: center; gap: 4px;"
                ).props("flat unelevated")

        # === SWIPE ACTIONS RIGHT (Teil/Alles) - shown on swipe left ===
        if on_partial_consume or on_consume:
            with (
                ui.element("div")
                .classes("sp-swipe-actions-right")
                .style(
                    "position: absolute; top: 0; right: 0; bottom: 0; width: 160px; "
                    "display: flex; align-items: stretch; z-index: 1;"
                )
            ):
                if on_partial_consume:
                    ui.button(
                        "Teil",
                        icon="add_circle_outline",
                        on_click=lambda i=item: on_partial_consume(i),
                    ).classes("sp-swipe-action-partial").style(
                        "flex: 1; border-radius: 0; "
                        "background: linear-gradient(135deg, #D4A853 0%, #E8C97B 100%); "
                        "color: white; display: flex; flex-direction: column; "
                        "align-items: center; justify-content: center; gap: 4px;"
                    ).props("flat unelevated")

                if on_consume:
                    ui.button(
                        "Alles",
                        icon="check",
                        on_click=lambda i=item: on_consume(i),
                    ).classes("sp-swipe-action-full").style(
                        "flex: 1; border-radius: 0; "
                        "background: linear-gradient(135deg, #4A7C59 0%, #5C7F5C 100%); "
                        "color: white; display: flex; flex-direction: column; "
                        "align-items: center; justify-content: center; gap: 4px;"
                    ).props("flat unelevated")

        # === CARD CONTENT (slideable) ===
        card_content_style = (
            "background: white; position: relative; z-index: 2; "
            "transition: transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94); "
            "touch-action: pan-y;"
        )
        if has_swipe_actions:
            card_content_style += " cursor: grab;"

        with ui.card().classes(card_classes).style(card_content_style) as card:
            # Add swipeable data attribute for JS
            if has_swipe_actions:
                card._props["data-swipeable"] = "true"
                # Calculate max swipe distances based on available actions
                max_left = -160 if (on_partial_consume or on_consume) else 0
                max_right = 80 if on_edit else 0
                card._props["data-max-left"] = str(max_left)
                card._props["data-max-right"] = str(max_right)

            # 3-Zone Grid Layout: header, body, footer
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
                # Name + Expiry Badge (spans full width)
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

                # Quick-Action Button zone (right side, spans body + footer rows)
                # Swipe actions replace quick action button when swipe callbacks present
                if not has_swipe_actions:
                    with (
                        ui.element("div")
                        .classes("quick-action-zone")
                        .style(
                            "grid-column: 2; grid-row: 2 / 4; "
                            "display: flex; align-items: center; justify-content: center;"
                        )
                    ):
                        pass  # Placeholder for non-swipe mode

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
                card.on("click", lambda: on_click(item))

    # Add swipe JavaScript if swipe actions are enabled
    if has_swipe_actions:
        _add_swipe_javascript()
