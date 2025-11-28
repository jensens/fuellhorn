"""Demo page for Chip components.

This page allows interactive testing of the chip components in the browser.
Temporary page - can be removed after integration into add_item.py.
"""

from ...models.item import ItemType
from ..components import create_item_type_chip_group
from ..components import create_unit_chip_group
from ..components import get_item_type_label
from nicegui import ui


@ui.page("/demo/chips")
def demo_chips() -> None:
    """Demo page for chip components."""
    # State for displaying current selections
    selected_item_type: list[ItemType | None] = [ItemType.PURCHASED_FRESH]
    selected_unit: list[str | None] = ["g"]

    with ui.column().classes("w-full max-w-md mx-auto p-4 gap-8"):
        ui.label("Chip Components Demo").classes("text-h4 font-bold text-primary")
        ui.label("Temporäre Demo-Seite für visuelle Tests").classes("text-gray-600")

        ui.separator()

        # ItemType Chips Demo
        ui.label("Artikel-Typ Chips").classes("text-h6 font-semibold")
        ui.label("Mit Ring-Dot Indikator (Radio-Button-artig)").classes("text-sm text-gray-500 mb-2")

        item_type_value_label = ui.label(
            f"Ausgewählt: {get_item_type_label(selected_item_type[0]) if selected_item_type[0] else 'Keine Auswahl'}"
        ).classes("text-sm font-medium mb-2")

        def on_item_type_change(value: ItemType) -> None:
            selected_item_type[0] = value
            item_type_value_label.set_text(f"Ausgewählt: {get_item_type_label(value)}")

        create_item_type_chip_group(
            value=selected_item_type[0],
            on_change=on_item_type_change,
        )

        ui.separator()

        # Unit Chips Demo
        ui.label("Einheit Chips").classes("text-h6 font-semibold")
        ui.label("Kompakt ohne Indikator (nur Farbwechsel)").classes("text-sm text-gray-500 mb-2")

        unit_value_label = ui.label(f"Ausgewählt: {selected_unit[0] or 'Keine Auswahl'}").classes(
            "text-sm font-medium mb-2"
        )

        def on_unit_change(value: str) -> None:
            selected_unit[0] = value
            unit_value_label.set_text(f"Ausgewählt: {value}")

        create_unit_chip_group(
            value=selected_unit[0],
            on_change=on_unit_change,
        )

        ui.separator()

        # Without initial selection
        ui.label("Ohne initiale Auswahl").classes("text-h6 font-semibold mt-4")

        ui.label("ItemType Chips (keine Vorauswahl):").classes("text-sm text-gray-500 mb-2")
        create_item_type_chip_group(on_change=lambda v: ui.notify(f"ItemType: {get_item_type_label(v)}"))

        ui.label("Unit Chips (keine Vorauswahl):").classes("text-sm text-gray-500 mb-2 mt-4")
        create_unit_chip_group(on_change=lambda v: ui.notify(f"Unit: {v}"))

        ui.separator()

        # Link back to dashboard
        ui.link("← Zurück zum Dashboard", "/").classes("text-primary")
