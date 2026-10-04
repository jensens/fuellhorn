"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import Permission
from ...auth import require_auth
from ...auth.dependencies import AuthenticationError
from ...auth.dependencies import AuthorizationError
from ...auth.dependencies import get_current_user
from ...auth.dependencies import get_current_user_id
from ...auth.dependencies import require_permission
from ...database import get_session
from ...models.item import ItemType
from ...models.user import User
from ...services import category_service
from ...services import item_service
from ...services import location_service
from ...services import preferences_service
from ..components import create_bottom_nav
from ..components import create_grouped_category_chip_group
from ..components import create_item_type_chip_group
from ..components import create_location_chip_group
from ..components import create_mobile_page_container
from ..components import create_unit_chip_group
from ..components.errors import show_service_error
from ..components.field_errors import FieldErrors
from ..smart_defaults import create_smart_defaults_dict
from ..smart_defaults import get_default_category
from ..smart_defaults import get_default_item_type
from ..smart_defaults import get_default_location
from ..smart_defaults import get_default_unit
from ..theme.icons import create_icon
from ..utils.date_utils import format_german_date
from ..utils.date_utils import parse_german_date
from ..utils.quantity import format_quantity
from ..validation import validate_step1
from ..validation import validate_step2
from ..validation import validate_step3
from collections.abc import Callable
from datetime import date as date_type
from nicegui import ui
from typing import Any


def _load_smart_default_inputs() -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Zeitfenster (Profil > System > Default) und letzter Eintrag des Nutzers aus der DB (Issue #397).

    Ohne Request-Cache: nach „Speichern & Nächster“ müssen die frisch gespeicherten Defaults sichtbar sein.
    """
    current_user = get_current_user(require_auth=True, use_cache=False)
    assert current_user is not None
    with next(get_session()) as session:
        windows = preferences_service.get_all_user_preferences(session, current_user)
        return windows, preferences_service.get_last_item_entry(session, current_user)


def _store_last_entry(smart_defaults: dict[str, Any]) -> None:
    """Letzten Eintrag pro Nutzer in der DB ablegen, nicht im Browser-Storage (Issue #397)."""
    with next(get_session()) as session:
        user = session.get(User, get_current_user_id())
        if user is not None:
            preferences_service.save_last_item_entry(session, user, smart_defaults)


@ui.page("/items/add")
@require_auth
def add_item() -> None:
    """3-Schritt-Wizard für schnelle Artikel-Erfassung."""
    windows, last_entry = _load_smart_default_inputs()

    default_item_type = get_default_item_type(last_entry, window_minutes=int(windows["item_type_time_window"]))
    default_unit = get_default_unit(last_entry)
    default_location_id = get_default_location(last_entry, window_minutes=int(windows["location_time_window"]))
    default_category_id = get_default_category(last_entry, window_minutes=int(windows["category_time_window"]))

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
    }

    # Button references (will be assigned when created)
    next_button: Any = None
    step2_next_button: Any = None
    step3_submit_button: Any = None
    step3_save_next_button: Any = None

    # Eine Fehlerzeile pro Feld; jeder Schritt-Aufbau erzeugt seine eigene Instanz (Issue #396)
    field_errors = FieldErrors()

    def touched(field: str, update: Callable[[], None]) -> None:
        """Feld wurde geändert: Meldung freigeben und Validierung aktualisieren."""
        field_errors.touch(field)
        update()

    def update_validation() -> None:
        """Feldmeldungen und Weiter-Button nach dem Stand der Eingaben (Issue #396)."""
        errors = validate_step1(
            product_name=form_data["product_name"],
            item_type=form_data["item_type"],
            quantity=form_data["quantity"],
            unit=form_data["unit"],
        )
        field_errors.show(errors)
        if not errors:
            next_button.props(remove="disabled")
        else:
            next_button.props(add="disabled")

    def update_step2_validation() -> None:
        """Feldmeldungen und Weiter-Button für Schritt 2."""
        errors = validate_step2(
            item_type=form_data["item_type"],
            best_before=form_data["best_before_date"],
            freeze_date=form_data.get("freeze_date"),
            category_id=form_data.get("category_id"),
        )
        field_errors.show(errors)
        if not errors:
            step2_next_button.props(remove="disabled")
        else:
            step2_next_button.props(add="disabled")

    def update_step3_validation() -> None:
        """Feldmeldungen und Speichern-Buttons für Schritt 3."""
        errors = validate_step3(
            location_id=form_data.get("location_id"),
        )
        field_errors.show(errors)
        if not errors:
            step3_submit_button.props(remove="disabled")
            step3_save_next_button.props(remove="disabled")
        else:
            step3_submit_button.props(add="disabled")
            step3_save_next_button.props(add="disabled")

    def show_step1() -> None:
        """Navigate back to Step 1 (preserves form data)."""
        nonlocal next_button, field_errors
        field_errors = FieldErrors()
        # Clear and rebuild UI for Step 1 (like show_step2 and show_step3)
        content_container.clear()
        with content_container:
            # Progress Indicator (Solarpunk theme)
            ui.label("Schritt 1 von 3").classes("text-sm text-stone mb-4")

            # Step 1: Basic Information
            ui.label("Basisinformationen").classes("sp-page-title text-base mb-3")

            # Product Name
            ui.label("Produktname *").classes("text-sm font-medium mb-1")
            product_name_input = (
                ui.input(placeholder="z.B. Tomaten aus Garten", value=form_data["product_name"])
                .classes("w-full")
                .props("outlined autofocus")
            )
            product_name_input.bind_value(form_data, "product_name")
            # Bei jeder Eingabe statt erst beim Verlassen des Feldes (Issue #396)
            product_name_input.on_value_change(lambda _: touched("product_name", update_validation))
            field_errors.slot("product_name")

            # Item Type
            ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")

            def on_item_type_change(value: ItemType) -> None:
                form_data["item_type"] = value
                touched("item_type", update_validation)

            create_item_type_chip_group(
                value=form_data["item_type"],
                on_change=on_item_type_change,
            )
            field_errors.slot("item_type")

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
            quantity_input.on_value_change(lambda _: touched("quantity", update_validation))
            field_errors.slot("quantity")

            # Unit
            ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")

            def on_unit_change(value: str) -> None:
                form_data["unit"] = value
                touched("unit", update_validation)

            create_unit_chip_group(
                value=form_data["unit"],
                on_change=on_unit_change,
            )
            field_errors.slot("unit")

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
                    .mark("wizard-next")
                )

            # Initial validation to set button state
            update_validation()

    def show_step2() -> None:
        """Navigate to Step 2."""
        nonlocal field_errors
        errors = validate_step1(
            form_data["product_name"], form_data["item_type"], form_data["quantity"], form_data["unit"]
        )
        if errors:
            # Der Klick kann den Server vor dem deaktivierten Button erreichen: alle Meldungen zeigen (#396)
            field_errors.show(errors, force=True)
            ui.notify(next(iter(errors.values())), type="warning")
            return

        field_errors = FieldErrors()
        item_type = form_data["item_type"]

        # Clear and rebuild UI for Step 2
        content_container.clear()
        with content_container:
            # Progress Indicator (Solarpunk theme)
            ui.label("Schritt 2 von 3").classes("text-sm text-stone mb-4")

            # Step 2: Shelf Life Information
            ui.label("Haltbarkeit").classes("sp-page-title text-base mb-3")

            # Summary from Step 1 (Solarpunk summary box)
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            }
            type_label = item_type_labels.get(item_type, "")

            with ui.element("div").classes("sp-summary-box w-full mb-4"):
                ui.label("Zusammenfassung:").classes("sp-summary-title")
                quantity_text = format_quantity(form_data["quantity"], form_data["unit"])
                ui.label(f"{form_data['product_name']} • {quantity_text} • {type_label}").classes("sp-summary-content")

            # Category Chips (always required, filtered by item type)
            with next(get_session()) as session:
                grouped_categories = category_service.get_grouped_categories_for_item_type(session, item_type)
            # Smart-Default oder frühere Wahl verwerfen, wenn sie für diesen Typ nicht angeboten wird (#385)
            offered_category_ids = {c.id for _, cats in grouped_categories for c in cats}
            if form_data.get("category_id") not in offered_category_ids:
                form_data["category_id"] = None

            ui.label("Kategorie *").classes("text-sm font-medium mb-2")

            def on_category_change(category_id: int) -> None:
                form_data["category_id"] = category_id
                touched("category", update_step2_validation)

            create_grouped_category_chip_group(
                grouped_categories=grouped_categories,
                value=form_data.get("category_id"),
                on_change=on_category_change,
            )
            field_errors.slot("category")

            # Date field - different label based on item type (Beschriftung wie Bottom-Sheet/Edit, #387)
            if item_type in {ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN}:
                # MHD from package
                date_label = "Mindesthaltbarkeitsdatum (MHD)"
                date_field = "best_before_date"
            elif item_type == ItemType.PURCHASED_THEN_FROZEN:
                # Einziges Datum: Einfrierdatum; best_before_date spiegelt es im Service (#387)
                date_label = "Eingefroren am"
                date_field = "freeze_date"
                # Initialize freeze_date with today if not set
                if form_data.get("freeze_date") is None:
                    form_data["freeze_date"] = date_type.today()
            else:
                # Production date for homemade items
                date_label = "Hergestellt am"
                date_field = "best_before_date"

            date_error_field = "freeze_date" if date_field == "freeze_date" else "best_before"
            ui.label(f"{date_label} *").classes("text-sm font-medium mb-1 mt-4")
            date_value = form_data.get(date_field) or date_type.today()
            form_data[date_field] = date_value  # Ensure it's set

            with (
                ui.input(value=format_german_date(date_value))
                .classes("w-full")
                .props('outlined mask="##.##.####"')
                .style("max-width: 500px")
                .mark("wizard-date-input") as date_input
            ):
                with date_input.add_slot("append"):
                    with ui.element("div").classes("cursor-pointer"):
                        create_icon("status/calendar", size="24px")
                        with ui.menu() as date_menu:
                            date_picker = ui.date().bind_value(date_input).props('locale="de" mask="DD.MM.YYYY"')
                            date_picker.on_value_change(lambda _: date_menu.close())
            # Typed or picked dates reach form_data only through this binding (Issue #362)
            date_input.bind_value(form_data, date_field, forward=parse_german_date, backward=format_german_date)
            date_input.on_value_change(lambda _: touched(date_error_field, update_step2_validation))
            field_errors.slot(date_error_field)

            # Additional freeze date for homemade_frozen
            if item_type == ItemType.HOMEMADE_FROZEN:
                ui.label("Eingefroren am *").classes("text-sm font-medium mb-1 mt-4")
                freeze_date_value = form_data.get("freeze_date") or date_type.today()
                form_data["freeze_date"] = freeze_date_value
                with (
                    ui.input(value=format_german_date(freeze_date_value))
                    .classes("w-full")
                    .props('outlined mask="##.##.####"')
                    .style("max-width: 500px")
                    .mark("wizard-freeze-date-input") as freeze_date_input
                ):
                    with freeze_date_input.add_slot("append"):
                        with ui.element("div").classes("cursor-pointer"):
                            create_icon("status/calendar", size="24px")
                            with ui.menu() as freeze_date_menu:
                                freeze_date_picker = (
                                    ui.date().bind_value(freeze_date_input).props('locale="de" mask="DD.MM.YYYY"')
                                )
                                freeze_date_picker.on_value_change(lambda _: freeze_date_menu.close())
                freeze_date_input.bind_value(
                    form_data, "freeze_date", forward=parse_german_date, backward=format_german_date
                )
                freeze_date_input.on_value_change(lambda _: touched("freeze_date", update_step2_validation))
                field_errors.slot("freeze_date")

            # Notes (optional)
            ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
            notes_input = (
                ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung").classes("w-full").props("outlined rows=2")
            )
            notes_input.bind_value(form_data, "notes")

            # Navigation
            with ui.row().classes("w-full justify-between mt-6 gap-2"):
                with (
                    ui.button(on_click=show_step1)
                    .props("flat color=gray-7 size=lg")
                    .style("min-height: 48px")
                    .mark("wizard-back")
                ):
                    with ui.row().classes("items-center gap-2"):
                        create_icon("actions/back", size="20px")
                        ui.label("Zurück")

                nonlocal step2_next_button
                step2_next_button = (
                    ui.button("Weiter", icon="arrow_forward", on_click=lambda: show_step3())
                    .props("color=primary size=lg disabled")
                    .style("min-height: 48px")
                    .mark("wizard-next")
                )
                # Initial validation
                update_step2_validation()

    def show_step3() -> None:
        """Navigate to Step 3."""
        nonlocal field_errors
        errors = validate_step2(
            form_data["item_type"],
            form_data["best_before_date"],
            form_data.get("freeze_date"),
            form_data.get("category_id"),
        )
        if errors:
            field_errors.show(errors, force=True)
            ui.notify(next(iter(errors.values())), type="warning")
            return

        field_errors = FieldErrors()
        item_type = form_data["item_type"]

        # Clear and rebuild UI for Step 3
        content_container.clear()
        with content_container:
            # Progress Indicator (Solarpunk theme)
            ui.label("Schritt 3 von 3").classes("text-sm text-stone mb-4")

            # Step 3: Location & Notes
            ui.label("Lagerort & Notizen").classes("sp-page-title text-base mb-3")

            # Summary from Steps 1-2 (Solarpunk summary box)
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

            with ui.element("div").classes("sp-summary-box w-full mb-4"):
                ui.label("Zusammenfassung:").classes("sp-summary-title")
                summary_parts = [
                    form_data["product_name"],
                    format_quantity(form_data["quantity"], form_data["unit"]),
                    type_label,
                ]
                if category_name:
                    summary_parts.append(category_name)
                ui.label(" • ".join(summary_parts)).classes("sp-summary-content")

                # Date info: nur die wirklich erfassten Daten, beschriftet wie im Bottom-Sheet (#387)
                date_parts: list[str] = []
                if item_type in {ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN}:
                    date_parts.append(f"MHD: {form_data['best_before_date'].strftime('%d.%m.%Y')}")
                elif item_type != ItemType.PURCHASED_THEN_FROZEN:
                    date_parts.append(f"Hergestellt: {form_data['best_before_date'].strftime('%d.%m.%Y')}")
                if form_data.get("freeze_date"):
                    date_parts.append(f"Eingefroren: {form_data['freeze_date'].strftime('%d.%m.%Y')}")
                ui.label(" • ".join(date_parts)).classes("sp-summary-content")

            # Fetch locations filtered by item type
            with next(get_session()) as session:
                locations = location_service.get_locations_for_item_type(session, item_type)
            # Smart-Default oder frühere Wahl verwerfen, wenn der Lagerort nicht zum Typ passt (#385):
            # sonst war Speichern aktiv, obwohl kein Chip gewählt war, und TK-Ware zog Frisches in die Truhe
            if form_data.get("location_id") not in {loc.id for loc in locations}:
                form_data["location_id"] = None

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
                ui.label(warning_msg).classes("text-sm sp-expiry-critical mb-2")

            def on_location_change(location_id: int) -> None:
                form_data["location_id"] = location_id
                touched("location", update_step3_validation)

            create_location_chip_group(
                locations=locations,
                value=form_data.get("location_id"),
                on_change=on_location_change,
            )
            field_errors.slot("location")

            # Notes (optional)
            ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
            notes_input = (
                ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung").classes("w-full").props("outlined rows=2")
            )
            notes_input.bind_value(form_data, "notes")

            # Navigation
            with ui.row().classes("w-full justify-between mt-6 gap-2"):
                with (
                    ui.button(on_click=show_step2)
                    .props("flat color=gray-7 size=lg")
                    .style("min-height: 48px")
                    .mark("wizard-back")
                ):
                    with ui.row().classes("items-center gap-2"):
                        create_icon("actions/back", size="20px")
                        ui.label("Zurück")

                nonlocal step3_submit_button
                with (
                    ui.button(on_click=save_item)
                    .props("color=primary size=lg disabled")
                    .style("min-height: 48px")
                    .mark("wizard-save") as step3_submit_button
                ):
                    with ui.row().classes("items-center gap-2"):
                        create_icon("actions/save", size="20px")
                        ui.label("Speichern")

            # "Speichern & Nächster" Button (most important for bulk capture!)
            with ui.row().classes("w-full justify-center mt-4"):
                nonlocal step3_save_next_button
                step3_save_next_button = (
                    ui.button("Speichern & Nächster", icon="playlist_add", on_click=save_and_next)
                    .props("color=secondary size=lg disabled")
                    .style("min-height: 48px; width: 100%")
                    .mark("wizard-save-next")
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
            field_errors.show(errors, force=True)
            ui.notify(next(iter(errors.values())), type="warning")
            return False

        # Nutzer frisch aus der DB und Berechtigung zur Laufzeit prüfen (#381)
        try:
            acting_user = require_permission(Permission.ITEMS_WRITE)
        except AuthenticationError:
            ui.notify("Bitte neu anmelden", type="negative")
            ui.navigate.to("/login")
            return False
        except AuthorizationError:
            ui.notify("Keine Berechtigung zum Erfassen", type="negative")
            return False
        user_id = acting_user.id
        if user_id is None:
            ui.notify("Bitte neu anmelden", type="negative")
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
            show_service_error(e)
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

        smart_defaults = create_smart_defaults_dict(
            item_type=form_data["item_type"],
            unit=form_data["unit"],
            location_id=form_data["location_id"],
            category_id=form_data.get("category_id"),
        )
        _store_last_entry(smart_defaults)

        # Show success notification
        ui.notify(f"✅ {product_name} gespeichert!", type="positive")

        # Reset wizard with smart defaults and reload page
        ui.navigate.to("/items/add")

    # Header with title and close button (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        ui.label("Artikel erfassen").classes("sp-page-title")
        with (
            ui.button(on_click=lambda: ui.navigate.to("/dashboard"))
            .classes("sp-back-btn")
            .props("flat round")
            .mark("wizard-close")
        ):
            create_icon("actions/close", size="24px")

    # Main content container (max-width handled by create_mobile_page_container);
    # Schritt 1 wird genau wie beim Zurück-Navigieren aufgebaut (eine Quelle, Issue #396)
    content_container = create_mobile_page_container()
    show_step1()

    # Bottom Navigation
    create_bottom_nav(current_page="add")
