"""Test page for Bottom Sheet component.

This page is only used for UI testing and should not be accessible in production.
"""

from ...database import get_session
from ...models.item import Item
from ...models.location import Location
from ..components.bottom_sheet import create_bottom_sheet
from nicegui import ui


@ui.page("/test/bottom-sheet/{item_id}")
def test_bottom_sheet_page(item_id: int) -> None:
    """Test page that renders a bottom sheet for an item.

    Args:
        item_id: The ID of the item to display in the bottom sheet
    """
    # Get item and location from database
    with next(get_session()) as session:
        item = session.get(Item, item_id)
        if not item:
            ui.label("Item nicht gefunden")
            return

        location = session.get(Location, item.location_id)
        if not location:
            ui.label("Lagerort nicht gefunden")
            return

        # Create detached copies to use outside session
        item_data = Item(
            id=item.id,
            product_name=item.product_name,
            item_type=item.item_type,
            quantity=item.quantity,
            unit=item.unit,
            location_id=item.location_id,
            best_before_date=item.best_before_date,
            freeze_date=item.freeze_date,
            expiry_date=item.expiry_date,
            notes=item.notes,
            is_consumed=item.is_consumed,
            created_at=item.created_at,
            created_by=item.created_by,
        )

        location_data = Location(
            id=location.id,
            name=location.name,
            location_type=location.location_type,
            description=location.description,
            is_active=location.is_active,
            created_at=location.created_at,
            created_by=location.created_by,
        )

    # Create and automatically open the bottom sheet
    sheet = create_bottom_sheet(
        item=item_data,
        location=location_data,
        on_close=lambda: ui.notify("Bottom Sheet geschlossen"),
        on_withdraw=lambda i: ui.notify(f"Entnehmen: {i.product_name}"),
        on_edit=lambda i: ui.notify(f"Bearbeiten: {i.product_name}"),
        on_consume=lambda i: ui.notify(f"Entnommen: {i.product_name}"),
    )

    # Automatically open the sheet for testing
    sheet.open()
