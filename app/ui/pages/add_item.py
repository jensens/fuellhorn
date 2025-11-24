"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import require_auth
from ...models.freeze_time_config import ItemType
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..validation import is_step1_valid
from nicegui import ui
from typing import Any


@ui.page("/items/add")
@require_auth
def add_item() -> None:
    """3-Schritt-Wizard für schnelle Artikel-Erfassung."""

    # Form state
    form_data: dict[str, Any] = {
        "product_name": "",
        "item_type": None,
        "quantity": 0.0,
        "unit": "g",
        "current_step": 1,
    }

    def update_validation() -> None:
        """Update next button state based on validation."""
        is_valid = is_step1_valid(
            product_name=form_data["product_name"],
            item_type=form_data["item_type"],
            quantity=form_data["quantity"],
        )
        next_button.props(remove="disabled" if is_valid else "", add="disabled" if not is_valid else "")

    def show_step2() -> None:
        """Navigate to Step 2."""
        if not is_step1_valid(
            form_data["product_name"], form_data["item_type"], form_data["quantity"]
        ):
            ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
            return

        form_data["current_step"] = 2
        # Clear and rebuild UI for Step 2
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 2 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 2: Date Information
            ui.label("Datumsangaben").classes("text-h6 font-semibold mb-3")

            # Summary from Step 1
            with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
                ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
                ui.label(
                    f"{form_data['product_name']} • {form_data['quantity']} {form_data['unit']}"
                ).classes("text-sm")

            # Placeholder for Step 2 fields (Phase 4)
            ui.label("Datumsfelder folgen in Phase 4").classes("text-sm text-gray-500")

            # Navigation
            with ui.row().classes("w-full justify-between mt-6 gap-2"):
                ui.button("Zurück", icon="arrow_back", on_click=lambda: ui.navigate.to("/items/add")).props(
                    "flat color=gray-7 size=lg"
                ).style("min-height: 48px")
                ui.button("Weiter", icon="arrow_forward").props(
                    "color=primary size=lg disabled"
                ).style("min-height: 48px")

    # Header with title and close button
    with ui.row().classes(
        "w-full items-center justify-between p-4 bg-white border-b border-gray-200"
    ):
        ui.label("Artikel erfassen").classes("text-h5 font-bold text-primary")
        ui.button(icon="close", on_click=lambda: ui.navigate.to("/dashboard")).props(
            "flat round color=gray-7"
        )

    # Main content container
    content_container = create_mobile_page_container()
    with content_container:
        # Progress Indicator
        ui.label("Schritt 1 von 3").classes("text-sm text-gray-600 mb-4")

        # Step 1: Basic Information
        ui.label("Basisinformationen").classes("text-h6 font-semibold mb-3")

        # Product Name
        ui.label("Produktname *").classes("text-sm font-medium mb-1")
        product_name_input = ui.input(placeholder="z.B. Tomaten aus Garten").classes(
            "w-full"
        ).props("outlined autofocus")
        product_name_input.bind_value(form_data, "product_name")
        product_name_input.on("blur", update_validation)

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")
        item_type_radio = ui.radio(
            options={
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            },
            value=None,
        ).classes("w-full").props("size=lg")  # 48x48px touch targets
        item_type_radio.bind_value(form_data, "item_type")
        item_type_radio.on("update:model-value", update_validation)

        # Quantity
        ui.label("Menge *").classes("text-sm font-medium mb-1 mt-4")
        quantity_input = ui.number(
            placeholder="0",
            min=0,
            step=1,
        ).classes("w-full").props("outlined")
        quantity_input.bind_value(form_data, "quantity")
        quantity_input.on("blur", update_validation)

        # Unit
        ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")
        unit_select = ui.select(
            options=["g", "kg", "ml", "L", "Stück", "Packung"],
            value="g",
        ).classes("w-full").props("outlined")
        unit_select.bind_value(form_data, "unit")

        # Navigation
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            next_button = ui.button(
                "Weiter", icon="arrow_forward", on_click=show_step2
            ).props("color=primary size=lg disabled").style("min-height: 48px")

    # Bottom Navigation
    create_bottom_nav(current_page="add")
