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
from ...services import item_service
from .item_card import get_expiry_status
from datetime import date
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
    # Create dialog with bottom sheet styling
    dialog = ui.dialog().props("position=bottom full-width")

    with dialog:
        with ui.card().classes("w-full rounded-t-2xl p-0"):
            # Header with close button
            with ui.row().classes("w-full items-center justify-between p-4 border-b"):
                ui.label(item.product_name).classes("text-lg font-semibold")

                # Close button - 48x48px touch target
                with (
                    ui.button(icon="close", on_click=lambda: _close_sheet(dialog, on_close))
                    .props("flat round")
                    .classes("min-w-[48px] min-h-[48px]")
                ):
                    pass

            # Item details
            with ui.column().classes("w-full p-4 gap-4"):
                # Quantity and unit
                with ui.row().classes("items-center gap-2"):
                    ui.icon("scale", size="20px").classes("text-gray-500")
                    ui.label(f"{item.quantity} {item.unit}").classes("text-base")

                # Location
                with ui.row().classes("items-center gap-2"):
                    ui.icon("place", size="20px").classes("text-gray-500")
                    ui.label(location.name).classes("text-base")

                # Expiry date with status badge
                expiry_status = get_expiry_status(item.expiry_date)
                with ui.row().classes("items-center gap-2"):
                    ui.icon("event", size="20px").classes("text-gray-500")
                    ui.label(item.expiry_date.strftime("%d.%m.%Y")).classes("text-base")
                    ui.label(get_expiry_label(item.expiry_date)).classes(get_expiry_badge_classes(expiry_status))

                # Notes (if present)
                if item.notes:
                    with ui.row().classes("items-start gap-2"):
                        ui.icon("notes", size="20px").classes("text-gray-500 mt-1")
                        ui.label(item.notes).classes("text-base text-gray-600")

            # Action buttons
            with ui.row().classes("w-full p-4 gap-3 border-t"):
                # Consume button - marks item as fully consumed
                ui.button(
                    "Entnommen",
                    icon="check_circle",
                    on_click=lambda: _handle_consume(dialog, item, on_consume, on_close),
                ).classes("flex-1 min-h-[48px]").props("color=positive")

                # Withdraw button - partial withdrawal
                ui.button(
                    "Entnehmen",
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
                item_service.withdraw_partial(
                    session=session,
                    item_id=item.id,
                    withdraw_quantity=withdraw_qty,
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
    """Handle consume button click."""
    dialog.close()
    if on_consume:
        on_consume(item)
    if on_close:
        on_close()
