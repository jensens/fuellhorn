"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import require_auth
from ...database import get_session
from ...models.freeze_time_config import ItemType
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..smart_defaults import create_smart_defaults_dict
from ..smart_defaults import get_default_categories
from ..smart_defaults import get_default_item_type
from ..smart_defaults import get_default_location
from ..smart_defaults import get_default_unit
from ..validation import is_step1_valid
from ..validation import is_step2_valid
from ..validation import is_step3_valid
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

    # Custom CSS for vertical toggle buttons
    ui.add_head_html("""
        <style>
            .q-btn-toggle--vertical .q-btn {
                width: 100%;
                justify-content: flex-start !important;
                margin-bottom: 8px;
            }
        </style>
    """)

    # Load smart defaults from browser storage
    last_entry = app.storage.browser.get(SMART_DEFAULTS_KEY)

    # Apply smart defaults with time windows
    default_item_type = get_default_item_type(last_entry, window_minutes=30)
    default_unit = get_default_unit(last_entry)
    default_location_id = get_default_location(last_entry)
    default_category_ids = get_default_categories(last_entry, window_minutes=30)

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
        "category_ids": default_category_ids.copy() if default_category_ids else [],
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
        next_button.props(remove="disabled" if is_valid else "", add="disabled" if not is_valid else "")

    def update_step2_validation() -> None:
        """Update Step 2 next button state based on validation."""
        is_valid = is_step2_valid(
            item_type=form_data["item_type"],
            best_before=form_data["best_before_date"],
            freeze_date=form_data.get("freeze_date"),
        )
        step2_next_button.props(remove="disabled" if is_valid else "", add="disabled" if not is_valid else "")

    def update_step3_validation() -> None:
        """Update Step 3 submit buttons state based on validation."""
        is_valid = is_step3_valid(
            location_id=form_data.get("location_id"),
            category_ids=form_data.get("category_ids"),
        )
        step3_submit_button.props(remove="disabled" if is_valid else "", add="disabled" if not is_valid else "")
        step3_save_next_button.props(remove="disabled" if is_valid else "", add="disabled" if not is_valid else "")

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
            item_type_toggle = (
                ui.toggle(
                    options={
                        ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                        ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                        ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                        ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                        ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
                    },
                    value=form_data["item_type"],
                )
                .classes("w-full q-btn-toggle--vertical")
                .props("no-caps")
                .style("flex-direction: column")
            )
            item_type_toggle.bind_value(form_data, "item_type")
            item_type_toggle.on("update:model-value", update_validation)

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
            unit_toggle = (
                ui.toggle(
                    options=["g", "kg", "ml", "l", "Stück", "Packung"],
                    value=form_data["unit"],
                )
                .classes("w-full")
                .props("no-caps")
            )
            unit_toggle.bind_value(form_data, "unit")
            unit_toggle.on("update:model-value", update_validation)

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
        # Clear and rebuild UI for Step 2
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 2 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 2: Date Information
            ui.label("Datumsangaben").classes("text-h6 font-semibold mb-3")

            # Summary from Step 1
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            }
            type_label = item_type_labels.get(form_data["item_type"], "")

            with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
                ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
                ui.label(
                    f"{form_data['product_name']} • {form_data['quantity']} {form_data['unit']} • {type_label}"
                ).classes("text-sm")

            # Best Before / Production Date (always shown)
            homemade_types = {ItemType.HOMEMADE_FROZEN, ItemType.HOMEMADE_PRESERVED}
            date_label = "Produktionsdatum" if form_data["item_type"] in homemade_types else "Einkaufsdatum"

            ui.label(f"{date_label} *").classes("text-sm font-medium mb-1")
            with (
                ui.input(value=form_data["best_before_date"].strftime("%d.%m.%Y"))
                .classes("w-full")
                .props('outlined mask="##.##.####"')
                .style("max-width: 500px") as best_before_input
            ):
                with best_before_input.add_slot("append"):
                    with ui.icon("event").classes("cursor-pointer"):
                        with ui.menu() as best_before_menu:
                            best_before_date_picker = ui.date().bind_value(best_before_input).props(
                                'locale="de" mask="DD.MM.YYYY"'
                            )

                            def on_best_before_change(e: Any) -> None:
                                best_before_menu.close()
                                # Update form_data when date changes
                                if e.value:
                                    # e.value is already a date object from ui.date
                                    form_data["best_before_date"] = e.value
                                update_step2_validation()

                            best_before_date_picker.on("update:model-value", on_best_before_change)
            best_before_input.on("blur", update_step2_validation)

            # Freeze Date (conditional - only for self-frozen types)
            # PURCHASED_FROZEN has MHD on package, no freeze_date needed
            frozen_types = {
                ItemType.PURCHASED_THEN_FROZEN,
                ItemType.HOMEMADE_FROZEN,
            }

            if form_data["item_type"] in frozen_types:
                ui.label("Einfrierdatum *").classes("text-sm font-medium mb-1 mt-4")
                freeze_date_value = form_data.get("freeze_date") or date_type.today()
                # Initialize form_data with default if not set (fixes #51)
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
                                freeze_date_picker = ui.date().bind_value(freeze_date_input).props(
                                    'locale="de" mask="DD.MM.YYYY"'
                                )

                                def on_freeze_date_change(e: Any) -> None:
                                    freeze_date_menu.close()
                                    # Update form_data when date changes
                                    if e.value:
                                        # e.value is already a date object from ui.date
                                        form_data["freeze_date"] = e.value
                                    update_step2_validation()

                                freeze_date_picker.on("update:model-value", on_freeze_date_change)
                freeze_date_input.on("blur", update_step2_validation)

            # Notes (optional)
            ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
            notes_input = ui.textarea(placeholder="z.B. blanchiert").classes("w-full").props("outlined")
            notes_input.bind_value(form_data, "notes")

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
        if not is_step2_valid(form_data["item_type"], form_data["best_before_date"], form_data.get("freeze_date")):
            ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
            return

        form_data["current_step"] = 3
        # Clear and rebuild UI for Step 3
        content_container.clear()
        with content_container:
            # Progress Indicator
            ui.label("Schritt 3 von 3").classes("text-sm text-gray-600 mb-4")

            # Step 3: Location & Categories
            ui.label("Lagerort & Kategorien").classes("text-h6 font-semibold mb-3")

            # Summary from Steps 1-2
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            }
            type_label = item_type_labels.get(form_data["item_type"], "")

            with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
                ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
                ui.label(
                    f"{form_data['product_name']} • {form_data['quantity']} {form_data['unit']} • {type_label}"
                ).classes("text-sm")

                # Date info
                best_before_str = form_data["best_before_date"].strftime("%d.%m.%Y")
                date_info = f"Datum: {best_before_str}"
                if form_data.get("freeze_date"):
                    freeze_str = form_data["freeze_date"].strftime("%d.%m.%Y")
                    date_info += f" • Eingefroren: {freeze_str}"
                ui.label(date_info).classes("text-sm")

            # Fetch locations and categories from database
            with next(get_session()) as session:
                locations = location_service.get_all_locations(session)
                categories = category_service.get_all_categories(session)

            # Location Selection (required)
            ui.label("Lagerort *").classes("text-sm font-medium mb-1")
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

            # Category Selection (optional multi-select)
            if categories:
                ui.label("Kategorien (optional)").classes("text-sm font-medium mb-1 mt-4")
                ui.label("Mehrfachauswahl möglich").classes("text-xs text-gray-600 mb-2")

                # Create checkbox group for categories
                for category in categories:
                    category_checkbox = ui.checkbox(category.name).classes("mb-2")

                    def make_toggle_handler(cat_id: int) -> Any:
                        def toggle_category(e: Any) -> None:
                            if e.value:
                                if cat_id not in form_data["category_ids"]:
                                    form_data["category_ids"].append(cat_id)
                            else:
                                if cat_id in form_data["category_ids"]:
                                    form_data["category_ids"].remove(cat_id)
                            update_step3_validation()

                        return toggle_category

                    category_checkbox.on("update:model-value", make_toggle_handler(category.id))  # type: ignore[arg-type]

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
            )
        )
        errors.update(
            validate_step3(
                form_data.get("location_id"),
                form_data.get("category_ids"),
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
                    freeze_date=form_data.get("freeze_date"),
                    quantity=form_data["quantity"],
                    unit=form_data["unit"],
                    item_type=form_data["item_type"],
                    location_id=form_data["location_id"],
                    created_by=user_id,
                    category_ids=form_data.get("category_ids"),
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
            category_ids=form_data.get("category_ids"),
            best_before_date_str=best_before_str,
        )
        app.storage.browser[SMART_DEFAULTS_KEY] = smart_defaults

        # Show success notification
        ui.notify(f"✅ {product_name} gespeichert!", type="positive")

        # Reset wizard with smart defaults and reload page
        ui.navigate.to("/items/add")

    # Header with title and close button
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Artikel erfassen").classes("text-h5 font-bold text-primary")
        ui.button(icon="close", on_click=lambda: ui.navigate.to("/dashboard")).props("flat round color=gray-7")

    # Main content container with max-width for desktop
    with ui.column().classes("w-full mx-auto").style("max-width: 800px"):
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
        item_type_toggle = (
            ui.toggle(
                options={
                    ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                    ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                    ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                    ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                    ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
                },
                value=form_data["item_type"],
            )
            .classes("w-full q-btn-toggle--vertical")
            .props("no-caps")
            .style("flex-direction: column")
        )
        item_type_toggle.bind_value(form_data, "item_type")
        item_type_toggle.on("update:model-value", update_validation)

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
        unit_toggle = (
            ui.toggle(
                options=["g", "kg", "ml", "l", "Stück", "Packung"],
                value=form_data["unit"],
            )
            .classes("w-full")
            .props("no-caps")
        )
        unit_toggle.bind_value(form_data, "unit")
        unit_toggle.on("update:model-value", update_validation)

        # Navigation
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            next_button = (
                ui.button("Weiter", icon="arrow_forward", on_click=show_step2)
                .props("color=primary size=lg disabled")
                .style("min-height: 48px")
            )

    # Bottom Navigation
    create_bottom_nav(current_page="add")
