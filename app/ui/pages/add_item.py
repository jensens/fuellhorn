"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import require_auth
from ...database import get_session
from ...models.freeze_time_config import ItemType
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_category_chip_group
from ..components import create_item_type_chip_group
from ..components import create_mobile_page_container
from ..components import create_unit_chip_group
from ..smart_defaults import create_smart_defaults_dict
from ..smart_defaults import get_default_category
from ..smart_defaults import get_default_item_type
from ..smart_defaults import get_default_location
from ..smart_defaults import get_default_unit
from ..validation import is_step1_valid
from ..validation import is_step2_valid
from ..validation import is_step3_valid
from ..validation import requires_category
from ..validation import validate_step1
from ..validation import validate_step2
from ..validation import validate_step3
from datetime import date as date_type
from nicegui import app
from nicegui import ui
from typing import Any


# Browser storage key for smart defaults
SMART_DEFAULTS_KEY = "last_item_entry"


@ui.page("/items/add")
@require_auth
def add_item() -> None:
    """3-Schritt-Wizard für schnelle Artikel-Erfassung."""
    # Load smart defaults from user storage
    last_entry = app.storage.user.get(SMART_DEFAULTS_KEY)

    # Apply smart defaults with time windows
    default_item_type = get_default_item_type(last_entry, window_minutes=30)
    default_unit = get_default_unit(last_entry)
    default_location_id = get_default_location(last_entry)
    default_category_id = get_default_category(last_entry, window_minutes=30)

    # Form state with smart defaults applied
    form_data: dict[str, Any] = {
        "product_name": "",
        "item_type": default_item_type,
        "quantity": None,
        "unit": default_unit,
        "best_before_date": date_type.today(),
        "freeze_date": None,
        "notes": "",
        "location_id": default_location_id,
        "category_id": default_category_id,
        "current_step": 1,
    }

    # Button references (will be assigned when created)
    next_button: Any = None
    step2_next_button: Any = None
    step3_submit_button: Any = None
    step3_save_next_button: Any = None

    def update_validation() -> None:
        """Update next button state based on validation."""
        is_valid = is_step1_valid(
            product_name=form_data["product_name"],
            item_type=form_data["item_type"],
            quantity=form_data["quantity"],
            unit=form_data["unit"],
        )
        if is_valid:
            next_button.props(remove="disabled")
        else:
            next_button.props(add="disabled")

    def update_step2_validation() -> None:
        """Update Step 2 next button state based on validation."""
        is_valid = is_step2_valid(
            item_type=form_data["item_type"],
            best_before=form_data["best_before_date"],
            freeze_date=form_data.get("freeze_date"),
            category_id=form_data.get("category_id"),
        )
        if is_valid:
            step2_next_button.props(remove="disabled")
        else:
            step2_next_button.props(add="disabled")

    def update_step3_validation() -> None:
        """Update Step 3 submit buttons state based on validation."""
        is_valid = is_step3_valid(
            location_id=form_data.get("location_id"),
        )
        if is_valid:
            step3_submit_button.props(remove="disabled")
            step3_save_next_button.props(remove="disabled")
        else:
            step3_submit_button.props(add="disabled")
            step3_save_next_button.props(add="disabled")

    def show_step1() -> None:
        """Navigate back to Step 1 (preserves form data)."""
        nonlocal next_button
        form_data["current_step"] = 1
        # Clear and rebuild UI for Step 1 (like show_step2 and show_step3)
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 1 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 1: Basic Information
            ui.label("Basisinformationen").classes("text-h6 font-semibold mb-3")

            # Product Name
            ui.label("Produktname *").classes("text-sm font-medium mb-1")
            product_name_input = (
                ui.input(placeholder="z.B. Tomaten aus Garten", value=form_data["product_name"])
                .classes("w-full")
                .props("outlined autofocus")
            )
            product_name_input.bind_value(form_data, "product_name")
            product_name_input.on("blur", update_validation)

            # Item Type
            ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")

            def on_item_type_change(value: ItemType) -> None:
                form_data["item_type"] = value
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

            # Notes (optional)
            ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
            notes_input = (
                ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung").classes("w-full").props("outlined rows=2")
            )
            notes_input.bind_value(form_data, "notes")

            # Navigation
            with ui.row().classes("w-full justify-end mt-6 gap-2"):
                next_button = (
                    ui.button("Weiter", icon="arrow_forward", on_click=show_step2)
                    .props("color=primary size=lg disabled")
                    .style("min-height: 48px")
                )

            # Initial validation to set button state
            update_validation()

    def show_step2() -> None:
        """Navigate to Step 2."""
        if not is_step1_valid(
            form_data["product_name"], form_data["item_type"], form_data["quantity"], form_data["unit"]
        ):
            ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
            return

        form_data["current_step"] = 2
        item_type = form_data["item_type"]
        needs_category = requires_category(item_type)

        # Clear and rebuild UI for Step 2
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 2 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 2: Shelf Life Information
            ui.label("Haltbarkeit").classes("text-h6 font-semibold mb-3")

            # Summary from Step 1
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            }
            type_label = item_type_labels.get(item_type, "")

            with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
                ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
                ui.label(
                    f"{form_data['product_name']} • {form_data['quantity']} {form_data['unit']} • {type_label}"
                ).classes("text-sm")

            # Category Chips (only for types that need shelf life from DB)
            if needs_category:
                with next(get_session()) as session:
                    categories = category_service.get_all_categories(session)

                ui.label("Kategorie *").classes("text-sm font-medium mb-2")
                ui.label("Bestimmt die Haltbarkeit").classes("text-xs text-gray-600 mb-2")

                def on_category_change(category_id: int) -> None:
                    form_data["category_id"] = category_id
                    update_step2_validation()

                create_category_chip_group(
                    categories=categories,
                    value=form_data.get("category_id"),
                    on_change=on_category_change,
                )

            # Date field - different label based on item type
            if item_type in {ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN}:
                # MHD from package
                date_label = "Mindesthaltbarkeitsdatum"
                date_field = "best_before_date"
            elif item_type == ItemType.PURCHASED_THEN_FROZEN:
                # Freeze date for items bought fresh then frozen
                date_label = "Einfrierdatum"
                date_field = "freeze_date"
                # Initialize freeze_date with today if not set
                if form_data.get("freeze_date") is None:
                    form_data["freeze_date"] = date_type.today()
            else:
                # Production date for homemade items
                date_label = "Produktionsdatum"
                date_field = "best_before_date"

            ui.label(f"{date_label} *").classes("text-sm font-medium mb-1 mt-4")
            date_value = form_data.get(date_field) or date_type.today()
            form_data[date_field] = date_value  # Ensure it's set

            with (
                ui.input(value=date_value.strftime("%d.%m.%Y"))
                .classes("w-full")
                .props('outlined mask="##.##.####"')
                .style("max-width: 500px") as date_input
            ):
                with date_input.add_slot("append"):
                    with ui.icon("event").classes("cursor-pointer"):
                        with ui.menu() as date_menu:
                            date_picker = ui.date().bind_value(date_input).props('locale="de" mask="DD.MM.YYYY"')

                            def on_date_change(e: Any, field: str = date_field) -> None:
                                date_menu.close()
                                if e.value:
                                    form_data[field] = e.value
                                update_step2_validation()

                            date_picker.on("update:model-value", on_date_change)
            date_input.on("blur", update_step2_validation)

            # Additional freeze date for homemade_frozen
            if item_type == ItemType.HOMEMADE_FROZEN:
                ui.label("Einfrierdatum *").classes("text-sm font-medium mb-1 mt-4")
                freeze_date_value = form_data.get("freeze_date") or date_type.today()
                form_data["freeze_date"] = freeze_date_value
                with (
                    ui.input(value=freeze_date_value.strftime("%d.%m.%Y"))
                    .classes("w-full")
                    .props('outlined mask="##.##.####"')
                    .style("max-width: 500px") as freeze_date_input
                ):
                    with freeze_date_input.add_slot("append"):
                        with ui.icon("event").classes("cursor-pointer"):
                            with ui.menu() as freeze_date_menu:
                                freeze_date_picker = (
                                    ui.date().bind_value(freeze_date_input).props('locale="de" mask="DD.MM.YYYY"')
                                )

                                def on_freeze_date_change(e: Any) -> None:
                                    freeze_date_menu.close()
                                    if e.value:
                                        form_data["freeze_date"] = e.value
                                    update_step2_validation()

                                freeze_date_picker.on("update:model-value", on_freeze_date_change)
                freeze_date_input.on("blur", update_step2_validation)

            # Navigation
            with ui.row().classes("w-full justify-between mt-6 gap-2"):
                ui.button("Zurück", icon="arrow_back", on_click=show_step1).props("flat color=gray-7 size=lg").style(
                    "min-height: 48px"
                )

                nonlocal step2_next_button
                step2_next_button = (
                    ui.button("Weiter", icon="arrow_forward", on_click=lambda: show_step3())
                    .props("color=primary size=lg disabled")
                    .style("min-height: 48px")
                )
                # Initial validation
                update_step2_validation()

    def show_step3() -> None:
        """Navigate to Step 3."""
        if not is_step2_valid(
            form_data["item_type"],
            form_data["best_before_date"],
            form_data.get("freeze_date"),
            form_data.get("category_id"),
        ):
            ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
            return

        form_data["current_step"] = 3
        item_type = form_data["item_type"]

        # Clear and rebuild UI for Step 3
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 3 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 3: Location & Notes
            ui.label("Lagerort & Notizen").classes("text-h6 font-semibold mb-3")

            # Summary from Steps 1-2
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            }
            type_label = item_type_labels.get(item_type, "")

            # Get category name for summary if selected
            category_name = None
            if form_data.get("category_id"):
                with next(get_session()) as session:
                    category = category_service.get_category(session, form_data["category_id"])
                    if category:
                        category_name = category.name

            with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
                ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
                summary_parts = [
                    form_data["product_name"],
                    f"{form_data['quantity']} {form_data['unit']}",
                    type_label,
                ]
                if category_name:
                    summary_parts.append(category_name)
                ui.label(" • ".join(summary_parts)).classes("text-sm")

                # Date info
                best_before_str = form_data["best_before_date"].strftime("%d.%m.%Y")
                date_info = f"Datum: {best_before_str}"
                if form_data.get("freeze_date"):
                    freeze_str = form_data["freeze_date"].strftime("%d.%m.%Y")
                    date_info += f" • Eingefroren: {freeze_str}"
                ui.label(date_info).classes("text-sm")

            # Fetch locations filtered by item type
            with next(get_session()) as session:
                locations = location_service.get_locations_for_item_type(session, item_type)

            # Location Selection (required)
            ui.label("Lagerort *").classes("text-sm font-medium mb-1")

            if not locations:
                # Show warning when no matching locations exist
                if item_type in {
                    ItemType.PURCHASED_FROZEN,
                    ItemType.PURCHASED_THEN_FROZEN,
                    ItemType.HOMEMADE_FROZEN,
                }:
                    warning_msg = "Kein Tiefkühl-Lagerort vorhanden. Bitte zuerst einen anlegen."
                else:
                    warning_msg = "Kein passender Lagerort (Keller/Kühlschrank) vorhanden."
                ui.label(warning_msg).classes("text-sm text-red-600 mb-2")

            location_options = {loc.id: loc.name for loc in locations}
            location_select = (
                ui.select(
                    options=location_options,
                    value=form_data.get("location_id"),
                )
                .classes("w-full")
                .props("outlined")
            )
            location_select.bind_value(form_data, "location_id")
            location_select.on("update:model-value", update_step3_validation)

            # Notes (optional)
            ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
            notes_input = (
                ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung").classes("w-full").props("outlined rows=2")
            )
            notes_input.bind_value(form_data, "notes")

            # Navigation
            with ui.row().classes("w-full justify-between mt-6 gap-2"):
                ui.button("Zurück", icon="arrow_back", on_click=show_step2).props("flat color=gray-7 size=lg").style(
                    "min-height: 48px"
                )

                nonlocal step3_submit_button
                step3_submit_button = (
                    ui.button("Speichern", icon="save", on_click=save_item)
                    .props("color=primary size=lg disabled")
                    .style("min-height: 48px")
                )

            # "Speichern & Nächster" Button (most important for bulk capture!)
            with ui.row().classes("w-full justify-center mt-4"):
                nonlocal step3_save_next_button
                step3_save_next_button = (
                    ui.button("Speichern & Nächster", icon="playlist_add", on_click=save_and_next)
                    .props("color=secondary size=lg disabled")
                    .style("min-height: 48px; width: 100%")
                )

            # Initial validation
            update_step3_validation()

    def save_item_to_db() -> bool:
        """Save item to database. Returns True on success, False on failure."""
        # Final validation across all steps
        errors = {}
        errors.update(
            validate_step1(
                form_data["product_name"],
                form_data["item_type"],
                form_data["quantity"],
                form_data["unit"],
            )
        )
        errors.update(
            validate_step2(
                form_data["item_type"],
                form_data["best_before_date"],
                form_data.get("freeze_date"),
                form_data.get("category_id"),
            )
        )
        errors.update(
            validate_step3(
                form_data.get("location_id"),
            )
        )

        if errors:
            ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
            return False

        # Get current user from session
        user_id = app.storage.user.get("user_id")

        if not user_id:
            ui.notify("Keine Berechtigung - bitte neu anmelden", type="negative")
            ui.navigate.to("/login")
            return False

        # Save to database
        try:
            with next(get_session()) as session:
                item_service.create_item(
                    session=session,
                    product_name=form_data["product_name"],
                    best_before_date=form_data["best_before_date"],
                    quantity=form_data["quantity"],
                    unit=form_data["unit"],
                    item_type=form_data["item_type"],
                    location_id=form_data["location_id"],
                    created_by=user_id,
                    category_id=form_data["category_id"],
                    freeze_date=form_data.get("freeze_date"),
                    notes=form_data.get("notes"),
                )
            return True
        except Exception as e:
            ui.notify(f"Fehler beim Speichern: {str(e)}", type="negative")
            return False

    def save_item() -> None:
        """Save item to database and navigate to dashboard."""
        if save_item_to_db():
            ui.notify(f"✅ {form_data['product_name']} gespeichert!", type="positive")
            ui.navigate.to("/dashboard")

    def save_and_next() -> None:
        """Save item and prepare wizard for next entry with smart defaults."""
        product_name = form_data["product_name"]

        if not save_item_to_db():
            return

        # Store smart defaults in browser storage
        best_before_str = form_data["best_before_date"].strftime("%d.%m.%Y")
        smart_defaults = create_smart_defaults_dict(
            item_type=form_data["item_type"],
            unit=form_data["unit"],
            location_id=form_data["location_id"],
            category_id=form_data.get("category_id"),
            best_before_date_str=best_before_str,
        )
        app.storage.user[SMART_DEFAULTS_KEY] = smart_defaults

        # Show success notification
        ui.notify(f"✅ {product_name} gespeichert!", type="positive")

        # Reset wizard with smart defaults and reload page
        ui.navigate.to("/items/add")

    # Header with title and close button
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Artikel erfassen").classes("text-h5 font-bold text-primary")
        ui.button(icon="close", on_click=lambda: ui.navigate.to("/dashboard")).props("flat round color=gray-7")

    # Main content container (max-width handled by create_mobile_page_container)
    content_container = create_mobile_page_container()
    with content_container:
        # Progress Indicator
        ui.label("Schritt 1 von 3").classes("text-sm text-gray-600 mb-4")

        # Step 1: Basic Information
        ui.label("Basisinformationen").classes("text-h6 font-semibold mb-3")

        # Product Name
        ui.label("Produktname *").classes("text-sm font-medium mb-1")
        product_name_input = (
            ui.input(placeholder="z.B. Tomaten aus Garten").classes("w-full").props("outlined autofocus")
        )
        product_name_input.bind_value(form_data, "product_name")
        product_name_input.on("blur", update_validation)

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")

        def on_item_type_change(value: ItemType) -> None:
            form_data["item_type"] = value
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

        # Notes (optional)
        ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
        notes_input = (
            ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung").classes("w-full").props("outlined rows=2")
        )
        notes_input.bind_value(form_data, "notes")

        # Navigation
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            next_button = (
                ui.button("Weiter", icon="arrow_forward", on_click=show_step2)
                .props("color=primary size=lg disabled")
                .style("min-height: 48px")
            )

        # Initial validation to set button state based on smart defaults
        update_validation()

    # Bottom Navigation
    create_bottom_nav(current_page="add")
