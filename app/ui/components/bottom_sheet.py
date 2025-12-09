"""Bottom Sheet Component - Mobile-first UI for Item Details.

Based on UI_KONZEPT.md Section 7: Bottom Sheet
- Slides up from bottom of screen
- Shows item details and actions
- Closable via X button or overlay click
- Mobile-optimized with 48px touch targets
"""

from ...database import get_session
from ...models.item import Item
from ...models.location import Location
from ...models.withdrawal import Withdrawal
from ...services import auth_service
from ...services import item_service
from ...services.expiry_calculator import get_expiry_status
from datetime import date
from nicegui import app
from nicegui import ui
from typing import Callable


def get_expiry_badge_classes(status: str) -> str:
    """Get CSS classes for expiry badge based on status.

    Args:
        status: One of "critical", "warning", or "ok"

    Returns:
        CSS class string for the badge
    """
    base_classes = "px-2 py-1 rounded-full text-xs font-semibold"

    if status == "critical":
        return f"{base_classes} bg-red-100 text-red-800"
    elif status == "warning":
        return f"{base_classes} bg-yellow-100 text-yellow-800"
    else:
        return f"{base_classes} bg-green-100 text-green-800"


def get_expiry_label(expiry_date: date) -> str:
    """Get human-readable expiry label.

    Args:
        expiry_date: The expiry date of the item

    Returns:
        Human-readable string like "In 2 Tagen" or "Abgelaufen"
    """
    days_until_expiry = (expiry_date - date.today()).days

    if days_until_expiry < 0:
        return "Abgelaufen"
    elif days_until_expiry == 0:
        return "Heute"
    elif days_until_expiry == 1:
        return "Morgen"
    elif days_until_expiry < 7:
        return f"In {days_until_expiry} Tagen"
    elif days_until_expiry < 30:
        weeks = days_until_expiry // 7
        return f"In {weeks} Woche{'n' if weeks > 1 else ''}"
    else:
        months = days_until_expiry // 30
        return f"In {months} Monat{'en' if months > 1 else ''}"


def create_bottom_sheet(
    item: Item,
    location: Location,
    on_close: Callable[[], None] | None = None,
    on_withdraw: Callable[[Item], None] | None = None,
    on_edit: Callable[[Item], None] | None = None,
    on_consume: Callable[[Item], None] | None = None,
) -> ui.dialog:
    """Create a bottom sheet dialog for item details.

    Args:
        item: The item to display details for
        location: The location where the item is stored
        on_close: Optional callback when sheet is closed
        on_withdraw: Optional callback when withdraw button is clicked
        on_edit: Optional callback when edit button is clicked
        on_consume: Optional callback when consume button is clicked

    Returns:
        The dialog element that can be opened with .open()
    """
    # Create dialog with bottom sheet styling (max-width for larger screens)
    dialog = ui.dialog().props("position=bottom").classes("bottom-sheet-dialog")
    dialog.style("width: 100%; max-width: 800px;")

    with dialog:
        with ui.card().classes("sp-bottom-sheet w-full p-0"):
            # Handle bar for visual grab affordance
            ui.element("div").classes("sp-bottom-sheet-handle")

            # Header with close button
            with ui.row().classes("sp-bottom-sheet-header w-full items-center justify-between"):
                ui.label(item.product_name).classes("sp-bottom-sheet-title")

                # Close button - uses theme styling
                ui.button(
                    icon="close",
                    on_click=lambda: _close_sheet(dialog, on_close),
                ).classes("sp-bottom-sheet-close").props("flat round")

            # Item details body
            with ui.column().classes("sp-bottom-sheet-body w-full"):
                # Quantity and unit
                with ui.row().classes("sp-info-row"):
                    ui.icon("scale", size="20px").classes("text-fern")
                    with ui.column().classes("gap-0"):
                        ui.label("Menge").classes("sp-info-label")
                        ui.label(f"{item.quantity} {item.unit}").classes("sp-info-value")

                # Location
                with ui.row().classes("sp-info-row"):
                    ui.icon("place", size="20px").classes("text-fern")
                    with ui.column().classes("gap-0"):
                        ui.label("Lagerort").classes("sp-info-label")
                        ui.label(location.name).classes("sp-info-value")

                # Expiry date with status badge (using best_before_date as fallback)
                expiry_status = get_expiry_status(item.best_before_date)
                with ui.row().classes("sp-info-row"):
                    ui.icon("event", size="20px").classes("text-fern")
                    with ui.column().classes("gap-0"):
                        ui.label("Haltbarkeit").classes("sp-info-label")
                        with ui.row().classes("items-center gap-2"):
                            ui.label(item.best_before_date.strftime("%d.%m.%Y")).classes("sp-info-value")
                            ui.label(get_expiry_label(item.best_before_date)).classes(
                                get_expiry_badge_classes(expiry_status)
                            )

                # Notes (if present)
                if item.notes:
                    with ui.row().classes("sp-info-row"):
                        ui.icon("notes", size="20px").classes("text-fern")
                        with ui.column().classes("gap-0"):
                            ui.label("Notizen").classes("sp-info-label")
                            ui.label(item.notes).classes("sp-info-value text-stone")

                # Withdrawal history (if any)
                if item.id is not None:
                    withdrawals = _get_withdrawal_history_with_users(item.id)
                    if withdrawals:
                        with ui.row().classes("sp-info-row"):
                            ui.icon("history", size="20px").classes("text-fern")
                            with ui.column().classes("gap-0 w-full"):
                                ui.label("Entnahme-Historie").classes("sp-info-label")
                                for withdrawal, username in withdrawals:
                                    _render_withdrawal_entry(withdrawal, username, item.unit)

            # Action buttons
            with ui.row().classes("w-full p-4 gap-3 border-t"):
                # Consume button - marks item as fully consumed
                ui.button(
                    "Alles entnehmen",
                    icon="check_circle",
                    on_click=lambda: _handle_consume(dialog, item, on_consume, on_close),
                ).classes("flex-1 min-h-[48px]").props("color=positive")

                # Withdraw button - partial withdrawal
                ui.button(
                    "Teilentnahme",
                    icon="remove_circle_outline",
                    on_click=lambda: _handle_withdraw(dialog, item, on_withdraw, on_close),
                ).classes("flex-1 min-h-[48px]").props("color=primary outline")

                # Edit button - secondary action
                ui.button(
                    "Bearbeiten",
                    icon="edit",
                    on_click=lambda: _handle_edit(dialog, item, on_edit, on_close),
                ).classes("flex-1 min-h-[48px]").props("color=secondary outline")

            # Close text for accessibility (screen readers and testing)
            ui.label("Schließen").classes("sr-only")

    return dialog


def _close_sheet(
    dialog: ui.dialog,
    on_close: Callable[[], None] | None,
) -> None:
    """Close the bottom sheet and call callback."""
    dialog.close()
    if on_close:
        on_close()


def _handle_withdraw(
    dialog: ui.dialog,
    item: Item,
    on_withdraw: Callable[[Item], None] | None,
    on_close: Callable[[], None] | None,
) -> None:
    """Handle withdraw button click - shows quantity input dialog."""
    # Create the withdrawal dialog
    withdraw_dialog = ui.dialog().props("persistent")

    # State for validation error message
    error_label: ui.label | None = None

    def confirm_withdrawal() -> None:
        """Validate and perform partial withdrawal."""
        nonlocal error_label

        # Get the input value
        try:
            withdraw_qty = float(quantity_input.value) if quantity_input.value else 0
        except (ValueError, TypeError):
            withdraw_qty = 0

        # Validation: must be positive
        if withdraw_qty <= 0:
            if error_label:
                error_label.set_text("Bitte eine gültige Menge eingeben")
                error_label.set_visibility(True)
            return

        # Validation: not more than available
        if withdraw_qty > item.quantity:
            if error_label:
                error_label.set_text(f"Nicht mehr als {int(item.quantity)} verfügbar")
                error_label.set_visibility(True)
            return

        # Perform the withdrawal
        try:
            if item.id is None:
                if error_label:
                    error_label.set_text("Item-ID nicht gefunden")
                    error_label.set_visibility(True)
                return

            with next(get_session()) as session:
                user_id = app.storage.user.get("user_id")
                item_service.withdraw_partial(
                    session=session,
                    item_id=item.id,
                    withdraw_quantity=withdraw_qty,
                    user_id=user_id,
                )

            # Show success notification
            ui.notify(f"{int(withdraw_qty)} {item.unit} entnommen", type="positive")

            # Close both dialogs
            withdraw_dialog.close()
            dialog.close()

            # Call callbacks
            if on_withdraw:
                on_withdraw(item)
            if on_close:
                on_close()

        except ValueError as e:
            if error_label:
                error_label.set_text(str(e))
                error_label.set_visibility(True)

    def cancel_withdrawal() -> None:
        """Cancel the withdrawal dialog."""
        withdraw_dialog.close()

    with withdraw_dialog:
        with ui.card().classes("p-4 min-w-[300px]"):
            # Title
            ui.label("Menge entnehmen").classes("text-lg font-semibold mb-2")

            # Available quantity info
            ui.label(f"Verfügbar: {int(item.quantity)} {item.unit}").classes("text-sm text-gray-600 mb-4")

            # Quantity input
            quantity_input = (
                ui.number(
                    label="Entnahmemenge",
                    min=1,
                    max=item.quantity,
                    step=1,
                    value=item.quantity,
                )
                .classes("w-full mb-2")
                .props("outlined")
            )

            # Error message (hidden by default)
            error_label = ui.label("").classes("text-red-600 text-sm mb-2")
            error_label.set_visibility(False)

            # Buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Abbrechen", on_click=cancel_withdrawal).props("flat")
                ui.button("Bestätigen", on_click=confirm_withdrawal).props("color=primary")

    # Open the withdrawal dialog
    withdraw_dialog.open()


def _handle_edit(
    dialog: ui.dialog,
    item: Item,
    on_edit: Callable[[Item], None] | None,
    on_close: Callable[[], None] | None,
) -> None:
    """Handle edit button click."""
    dialog.close()
    if on_edit:
        on_edit(item)
    if on_close:
        on_close()


def _handle_consume(
    dialog: ui.dialog,
    item: Item,
    on_consume: Callable[[Item], None] | None,
    on_close: Callable[[], None] | None,
) -> None:
    """Handle consume button click - marks item as fully consumed."""
    if item.id is None:
        ui.notify("Item-ID nicht gefunden", type="negative")
        return

    try:
        with next(get_session()) as session:
            user_id = app.storage.user.get("user_id")
            item_service.mark_item_consumed(session, item.id, user_id)

        ui.notify(f"{item.product_name} vollständig entnommen", type="positive")

        dialog.close()
        if on_consume:
            on_consume(item)
        if on_close:
            on_close()

    except ValueError as e:
        ui.notify(str(e), type="negative")


def _get_withdrawal_history_with_users(item_id: int) -> list[tuple[Withdrawal, str]]:
    """Get withdrawal history with usernames.

    Args:
        item_id: The item ID to get history for

    Returns:
        List of (Withdrawal, username) tuples, sorted newest first
    """
    result: list[tuple[Withdrawal, str]] = []

    with next(get_session()) as session:
        withdrawals = item_service.get_withdrawal_history(session, item_id)

        # Reverse to show newest first (service returns oldest first)
        for withdrawal in reversed(withdrawals):
            try:
                user = auth_service.get_user(session, withdrawal.withdrawn_by)
                username = user.username
            except ValueError:
                username = "Unbekannt"

            result.append((withdrawal, username))

    return result


def _render_withdrawal_entry(withdrawal: Withdrawal, username: str, unit: str) -> None:
    """Render a single withdrawal entry in the history.

    Args:
        withdrawal: The withdrawal record
        username: The username who made the withdrawal
        unit: The unit of measurement
    """
    with ui.row().classes("w-full items-center gap-2 py-1"):
        # Format date as DD.MM.YYYY HH:MM
        date_str = withdrawal.withdrawn_at.strftime("%d.%m.%Y %H:%M")

        # Format quantity (integer if whole number)
        qty = withdrawal.quantity
        qty_str = str(int(qty)) if qty == int(qty) else str(qty)

        ui.label(f"{date_str}").classes("text-sm text-stone")
        ui.label(f"{qty_str} {unit}").classes("text-sm font-medium")
        ui.label(f"({username})").classes("text-sm text-stone")
