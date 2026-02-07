"""Item Edit Page - Edit existing items."""

from ...auth import require_auth
from ...database import get_session
from ...models.item import ItemType
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_category_chip_group
from ..components import create_item_type_chip_group
from ..components import create_location_chip_group
from ..components import create_mobile_page_container
from ..components import create_unit_chip_group
from ..theme.icons import create_icon
from ..validation import requires_category
from datetime import date as date_type
from nicegui import ui
from typing import Any


@ui.page("/items/{item_id}/edit")
@require_auth
def edit_item(item_id: int) -> None:
    """Edit-Seite fuer einen bestehenden Artikel."""
    # Load item from database
    try:
        with next(get_session()) as session:
            item = item_service.get_item(session, item_id)
            # Load related data
            categories = category_service.get_all_categories(session)
            locations = location_service.get_locations_for_item_type(session, item.item_type)

            # Store item data for form
            form_data: dict[str, Any] = {
                "product_name": item.product_name,
                "item_type": item.item_type,
                "quantity": item.quantity,
                "unit": item.unit,
                "best_before_date": item.best_before_date,
                "freeze_date": item.freeze_date,
                "notes": item.notes or "",
                "location_id": item.location_id,
                "category_id": item.category_id,
            }
    except ValueError:
        # Item not found
        with ui.row().classes("sp-page-header w-full items-center justify-between"):
            ui.label("Fehler").classes("sp-page-title")
            with ui.button(on_click=lambda: ui.navigate.to("/items")).classes("sp-back-btn").props("flat round"):
                create_icon("actions/close", size="24px")

        container = create_mobile_page_container()
        with container:
            ui.label("Artikel nicht gefunden").classes("text-lg text-red-600 mb-4")
            ui.button("Zurueck zur Uebersicht", on_click=lambda: ui.navigate.to("/items")).props("color=primary")

        create_bottom_nav(current_page="items")
        return

    # References for validation
    save_button: Any = None

    def update_validation() -> None:
        """Update save button state based on validation."""
        is_valid = bool(
            form_data["product_name"]
            and form_data["item_type"]
            and form_data["quantity"]
            and form_data["quantity"] > 0
            and form_data["unit"]
            and form_data["location_id"]
        )
        # Check category requirement
        if requires_category(form_data["item_type"]) and not form_data.get("category_id"):
            is_valid = False

        if is_valid:
            save_button.props(remove="disabled")
        else:
            save_button.props(add="disabled")

    def update_locations_for_item_type() -> None:
        """Update available locations when item type changes."""
        nonlocal locations
        with next(get_session()) as session:
            locations = location_service.get_locations_for_item_type(session, form_data["item_type"])
        # Rebuild location chips
        location_container.clear()
        with location_container:
            create_location_chip_group(
                locations=locations,
                value=form_data.get("location_id"),
                on_change=on_location_change,
            )
        update_validation()

    def on_location_change(location_id: int) -> None:
        form_data["location_id"] = location_id
        update_validation()

    def save_item() -> None:
        """Save changes to database."""
        try:
            with next(get_session()) as session:
                item_service.update_item(
                    session=session,
                    id=item_id,
                    product_name=form_data["product_name"],
                    quantity=form_data["quantity"],
                    unit=form_data["unit"],
                    best_before_date=form_data["best_before_date"],
                    freeze_date=form_data.get("freeze_date"),
                    location_id=form_data["location_id"],
                    category_id=form_data.get("category_id"),
                    item_type=form_data["item_type"],
                    notes=form_data.get("notes") or None,
                )
            ui.notify(f"{form_data['product_name']} gespeichert!", type="positive")
            ui.navigate.to("/items")
        except Exception as e:
            ui.notify(f"Fehler beim Speichern: {str(e)}", type="negative")

    # Header with title and close button (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        ui.label("Artikel bearbeiten").classes("sp-page-title")
        with (
            ui.button(on_click=lambda: ui.navigate.to("/items"))
            .classes("sp-back-btn")
            .props("flat round")
            .mark("edit-close")
        ):
            create_icon("actions/close", size="24px")

    # Main content container
    content_container = create_mobile_page_container()
    with content_container:
        # Product Name
        ui.label("Produktname *").classes("text-sm font-medium mb-1")
        product_name_input = (
            ui.input(placeholder="z.B. Tomaten aus Garten", value=form_data["product_name"])
            .classes("w-full")
            .props("outlined")
        )
        product_name_input.bind_value(form_data, "product_name")
        product_name_input.on("blur", update_validation)

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")

        def on_item_type_change(value: ItemType) -> None:
            form_data["item_type"] = value
            update_locations_for_item_type()
            # Update category label based on item type
            category_label.set_text("Kategorie *" if requires_category(value) else "Kategorie (optional)")
            # Show/hide freeze date based on item type
            freeze_date_section.set_visibility(
                value
                in {
                    ItemType.PURCHASED_THEN_FROZEN,
                    ItemType.HOMEMADE_FROZEN,
                }
            )
            update_validation()

        create_item_type_chip_group(
            value=form_data["item_type"],
            on_change=on_item_type_change,
        )

        # Quantity
        ui.label("Menge *").classes("text-sm font-medium mb-1 mt-4")
        quantity_input = (
            ui.number(
                placeholder="z.B. 500",
                min=0,
                step=1,
                value=form_data["quantity"],
            )
            .classes("w-full")
            .props("outlined clearable")
        )
        quantity_input.bind_value(form_data, "quantity")
        quantity_input.on("blur", update_validation)

        # Unit
        ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")

        def on_unit_change(value: str) -> None:
            form_data["unit"] = value
            update_validation()

        create_unit_chip_group(
            value=form_data["unit"],
            on_change=on_unit_change,
        )

        # Category (always visible, required/optional based on item type)
        needs_category = requires_category(form_data["item_type"])
        with ui.element("div").classes("mt-4"):
            category_label = ui.label("Kategorie *" if needs_category else "Kategorie (optional)").classes(
                "text-sm font-medium mb-2"
            )

            def on_category_change(category_id: int) -> None:
                form_data["category_id"] = category_id
                update_validation()

            create_category_chip_group(
                categories=categories,
                value=form_data.get("category_id"),
                on_change=on_category_change,
            )

        # Best Before Date / Production Date
        item_type = form_data["item_type"]
        if item_type in {ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN}:
            date_label = "Mindesthaltbarkeitsdatum *"
        elif item_type == ItemType.PURCHASED_THEN_FROZEN:
            date_label = "Einkaufsdatum *"
        else:
            date_label = "Produktionsdatum *"

        ui.label(date_label).classes("text-sm font-medium mb-1 mt-4")
        date_value = form_data.get("best_before_date") or date_type.today()
        form_data["best_before_date"] = date_value

        with (
            ui.input(value=date_value.strftime("%d.%m.%Y"))
            .classes("w-full")
            .props('outlined mask="##.##.####"')
            .style("max-width: 500px") as date_input
        ):
            with date_input.add_slot("append"):
                with ui.element("div").classes("cursor-pointer"):
                    create_icon("status/calendar", size="24px")
                    with ui.menu() as date_menu:
                        date_picker = ui.date().bind_value(date_input).props('locale="de" mask="DD.MM.YYYY"')

                        def on_date_change(e: Any) -> None:
                            date_menu.close()
                            if e.value:
                                form_data["best_before_date"] = e.value
                            update_validation()

                        date_picker.on("update:model-value", on_date_change)

        # Freeze Date (conditional)
        show_freeze_date = form_data["item_type"] in {
            ItemType.PURCHASED_THEN_FROZEN,
            ItemType.HOMEMADE_FROZEN,
        }
        with ui.element("div").classes("mt-4") as freeze_date_section:
            freeze_date_section.set_visibility(show_freeze_date)
            ui.label("Einfrierdatum *").classes("text-sm font-medium mb-1")
            freeze_date_value = form_data.get("freeze_date") or date_type.today()
            if show_freeze_date:
                form_data["freeze_date"] = freeze_date_value

            with (
                ui.input(value=freeze_date_value.strftime("%d.%m.%Y") if freeze_date_value else "")
                .classes("w-full")
                .props('outlined mask="##.##.####"')
                .style("max-width: 500px") as freeze_date_input
            ):
                with freeze_date_input.add_slot("append"):
                    with ui.element("div").classes("cursor-pointer"):
                        create_icon("status/calendar", size="24px")
                        with ui.menu() as freeze_date_menu:
                            freeze_date_picker = (
                                ui.date().bind_value(freeze_date_input).props('locale="de" mask="DD.MM.YYYY"')
                            )

                            def on_freeze_date_change(e: Any) -> None:
                                freeze_date_menu.close()
                                if e.value:
                                    form_data["freeze_date"] = e.value
                                update_validation()

                            freeze_date_picker.on("update:model-value", on_freeze_date_change)

        # Location
        ui.label("Lagerort *").classes("text-sm font-medium mb-1 mt-4")
        location_container = ui.element("div")
        with location_container:
            create_location_chip_group(
                locations=locations,
                value=form_data.get("location_id"),
                on_change=on_location_change,
            )

        # Notes (optional)
        ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
        notes_input = (
            ui.textarea(placeholder="z.B. je 12 Stueck, 300g pro Packung", value=form_data["notes"])
            .classes("w-full")
            .props("outlined rows=2")
        )
        notes_input.bind_value(form_data, "notes")

        # Save Button
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            with ui.button(on_click=save_item).props("color=primary size=lg").style("min-height: 48px") as save_button:
                with ui.row().classes("items-center gap-2"):
                    create_icon("actions/save", size="20px")
                    ui.label("Speichern")

        # Initial validation
        update_validation()

    # Bottom Navigation
    create_bottom_nav(current_page="items")
