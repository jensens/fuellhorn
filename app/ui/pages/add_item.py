"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import require_auth
from ...models.freeze_time_config import ItemType
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from nicegui import ui


@ui.page("/items/add")
@require_auth
def add_item() -> None:
    """3-Schritt-Wizard für schnelle Artikel-Erfassung."""

    # Header with title and close button
    with ui.row().classes(
        "w-full items-center justify-between p-4 bg-white border-b border-gray-200"
    ):
        ui.label("Artikel erfassen").classes("text-h5 font-bold text-primary")
        ui.button(icon="close", on_click=lambda: ui.navigate.to("/dashboard")).props(
            "flat round color=gray-7"
        )

    # Main content
    with create_mobile_page_container():
        # Progress Indicator
        ui.label("Schritt 1 von 3").classes("text-sm text-gray-600 mb-4")

        # Step 1: Basic Information
        ui.label("Basisinformationen").classes("text-h6 font-semibold mb-3")

        # Product Name
        ui.label("Produktname *").classes("text-sm font-medium mb-1")
        ui.input(placeholder="z.B. Tomaten aus Garten").classes("w-full").props(
            "outlined autofocus"
        )

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")
        ui.radio(
            options={
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            },
            value=None,
        ).classes("w-full").props("size=lg")  # 48x48px touch targets

        # Quantity
        ui.label("Menge *").classes("text-sm font-medium mb-1 mt-4")
        ui.number(
            placeholder="0",
            min=0,
            step=1,
        ).classes("w-full").props("outlined")

        # Unit
        ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")
        ui.select(
            options=["g", "kg", "ml", "L", "Stück", "Packung"],
            value="g",
        ).classes("w-full").props("outlined")

        # Navigation
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            ui.button("Weiter", icon="arrow_forward").props(
                "color=primary size=lg disabled"
            ).style("min-height: 48px")

    # Bottom Navigation
    create_bottom_nav(current_page="add")
