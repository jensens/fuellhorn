"""Item Edit Page - Edit existing items."""

from ...auth import require_auth
from ...database import get_session
from ...models.item import ItemType
from ...services import category_service
from ...services import item_service
from ...services import item_types
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_date_field
from ..components import create_grouped_category_chip_group
from ..components import create_item_type_chip_group
from ..components import create_location_chip_group
from ..components import create_mobile_page_container
from ..components import create_unit_chip_group
from ..components.errors import show_service_error
from ..components.field_errors import FieldErrors
from ..theme.icons import create_icon
from ..validation import validate_step1
from ..validation import validate_step2
from ..validation import validate_step3
from datetime import date as date_type
from nicegui import ui
from typing import Any


FREEZE_DATE_TYPES = item_types.FREEZE_DATE_TYPES


def _date_label(item_type: ItemType) -> str:
    """Beschriftung von best_before_date je Artikel-Typ (MHD oder Herstellungsdatum, Issue #387).

    Für PURCHASED_THEN_FROZEN ist das Feld ausgeblendet: der Service spiegelt dort das Einfrierdatum.
    """
    label = item_types.get_best_before_input_label(item_type) or item_types.LABEL_PRODUCED
    return f"{label} *"


@ui.page("/items/{item_id}/edit")
@require_auth
def edit_item(item_id: int) -> None:
    """Edit-Seite fuer einen bestehenden Artikel."""
    # Load item from database
    try:
        with next(get_session()) as session:
            item = item_service.get_item(session, item_id)
            # Load related data
            grouped_categories = category_service.get_grouped_categories_for_item_type(session, item.item_type)
            # Der aktuelle Lagerort bleibt wählbar, auch wenn er inzwischen deaktiviert ist (#379)
            locations = location_service.get_locations_for_item_type(
                session, item.item_type, include_location_id=item.location_id
            )

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
    save_button: ui.button | None = None
    # Felder sind vorbelegt; jeder Fehler ist Folge einer Änderung und wird sofort gezeigt (Issue #396)
    field_errors = FieldErrors(reveal_all=True)

    def validation_errors() -> dict[str, str]:
        """Dieselben Regeln wie im Wizard (Issue #386): Trim, 2 Zeichen, Menge > 0, Einfrierdatum, Lagerort."""
        errors = validate_step1(
            form_data["product_name"], form_data["item_type"], form_data["quantity"], form_data["unit"]
        )
        errors.update(
            validate_step2(
                form_data["item_type"],
                form_data.get("best_before_date"),
                form_data.get("freeze_date"),
                form_data.get("category_id"),
            )
        )
        errors.update(validate_step3(form_data.get("location_id")))
        return errors

    def update_validation() -> None:
        """Feldmeldungen und Speichern-Button nach dem Stand der Eingaben (Issue #396)."""
        errors = validation_errors()
        field_errors.show(errors)
        if save_button is not None:
            save_button.set_enabled(not errors)

    def update_locations_for_item_type() -> None:
        """Update available locations when item type changes."""
        nonlocal locations
        with next(get_session()) as session:
            locations = location_service.get_locations_for_item_type(
                session, form_data["item_type"], include_location_id=item.location_id
            )
        # Lagerort verwerfen, der zum neuen Typ nicht passt (#385); die Chips zeigen ihn nicht mehr an
        if form_data.get("location_id") not in {loc.id for loc in locations}:
            form_data["location_id"] = None
        # Rebuild location chips
        location_container.clear()
        with location_container:
            create_location_chip_group(
                locations=locations,
                value=form_data.get("location_id"),
                on_change=on_location_change,
            )
        update_validation()

    def update_categories_for_item_type() -> None:
        """Update available categories when item type changes."""
        nonlocal grouped_categories
        with next(get_session()) as session:
            grouped_categories = category_service.get_grouped_categories_for_item_type(session, form_data["item_type"])
        # Kategorie verwerfen, die für den neuen Typ nicht angeboten wird (#385)
        if form_data.get("category_id") not in {c.id for _, cats in grouped_categories for c in cats}:
            form_data["category_id"] = None
        # Rebuild category chips
        category_container.clear()
        with category_container:
            create_grouped_category_chip_group(
                grouped_categories=grouped_categories,
                value=form_data.get("category_id"),
                on_change=on_category_change,
            )
        update_validation()

    def on_location_change(location_id: int) -> None:
        form_data["location_id"] = location_id
        update_validation()

    def save_item() -> None:
        """Save changes to database."""
        # Re-Validierung wie im Wizard: ein Klick kann den Server erreichen, bevor der
        # deaktivierte Button im Browser angekommen ist (Issue #386)
        errors = validation_errors()
        if errors:
            ui.notify(next(iter(errors.values())), type="warning")
            update_validation()
            return

        try:
            with next(get_session()) as session:
                # Nullable-Felder explizit übergeben: None leert sie (UNSET-Sentinel im Service)
                item_service.update_item(
                    session=session,
                    id=item_id,
                    product_name=form_data["product_name"].strip(),
                    quantity=form_data["quantity"],
                    unit=form_data["unit"],
                    best_before_date=form_data["best_before_date"],
                    freeze_date=form_data.get("freeze_date"),
                    location_id=form_data["location_id"],
                    category_id=form_data.get("category_id"),
                    item_type=form_data["item_type"],
                    notes=(form_data.get("notes") or "").strip() or None,
                )
            ui.notify(f"{form_data['product_name']} gespeichert!", type="positive")
            ui.navigate.to("/items")
        except Exception as e:
            show_service_error(e)

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
        product_name_input.on_value_change(lambda _: update_validation())
        field_errors.slot("product_name")

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")

        def on_item_type_change(value: ItemType) -> None:
            form_data["item_type"] = value
            update_locations_for_item_type()
            update_categories_for_item_type()
            # Einfrierdatum setzen bzw. leeren und Datumslabel anpassen (Issue #386)
            needs_freeze_date = value in FREEZE_DATE_TYPES
            freeze_date_section.set_visibility(needs_freeze_date)
            if needs_freeze_date:
                if form_data.get("freeze_date") is None:
                    freeze_date_field.set_value(date_type.today())
            else:
                freeze_date_field.set_value(None)
            date_label.set_text(_date_label(value))
            best_before_section.set_visibility(value != ItemType.PURCHASED_THEN_FROZEN)
            update_validation()

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
        quantity_input.on_value_change(lambda _: update_validation())
        field_errors.slot("quantity")

        # Unit
        ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")

        def on_unit_change(value: str) -> None:
            form_data["unit"] = value
            update_validation()

        create_unit_chip_group(
            value=form_data["unit"],
            on_change=on_unit_change,
        )
        field_errors.slot("unit")

        # Category (always required, filtered by item type)
        ui.label("Kategorie *").classes("text-sm font-medium mb-2 mt-4")

        def on_category_change(category_id: int) -> None:
            form_data["category_id"] = category_id
            update_validation()

        category_container = ui.element("div")
        with category_container:
            create_grouped_category_chip_group(
                grouped_categories=grouped_categories,
                value=form_data.get("category_id"),
                on_change=on_category_change,
            )
        field_errors.slot("category")  # außerhalb des Containers, der beim Typwechsel neu gebaut wird

        # best_before_date: MHD bzw. Herstellungsdatum; für PURCHASED_THEN_FROZEN ausgeblendet,
        # weil der Service dort das Einfrierdatum spiegelt (Issue #387)
        with ui.element("div").mark("edit-best-before-section") as best_before_section:
            best_before_section.set_visibility(form_data["item_type"] != ItemType.PURCHASED_THEN_FROZEN)
            # Best Before Date / Production Date (Label folgt dem Typ, siehe on_item_type_change)
            date_value = form_data.get("best_before_date") or date_type.today()
            form_data["best_before_date"] = date_value

            def on_best_before_change(value: date_type | None) -> None:
                form_data["best_before_date"] = value
                update_validation()

            best_before_field = create_date_field(
                label=_date_label(form_data["item_type"]),
                value=date_value,
                marker="edit-date-input",
                on_change=on_best_before_change,
            )
            date_label = best_before_field.label
            field_errors.slot("best_before")

        # Freeze Date (conditional)
        show_freeze_date = form_data["item_type"] in FREEZE_DATE_TYPES
        with ui.element("div").classes("mt-4") as freeze_date_section:
            freeze_date_section.set_visibility(show_freeze_date)
            freeze_date_value = form_data.get("freeze_date") or date_type.today()
            if show_freeze_date:
                form_data["freeze_date"] = freeze_date_value

            def on_freeze_date_change(value: date_type | None) -> None:
                form_data["freeze_date"] = value
                update_validation()

            freeze_date_field = create_date_field(
                label="Eingefroren am *",
                value=form_data.get("freeze_date"),
                marker="edit-freeze-date-input",
                on_change=on_freeze_date_change,
            )
            field_errors.slot("freeze_date")

        # Location
        ui.label("Lagerort *").classes("text-sm font-medium mb-1 mt-4")
        location_container = ui.element("div")
        with location_container:
            create_location_chip_group(
                locations=locations,
                value=form_data.get("location_id"),
                on_change=on_location_change,
            )
        field_errors.slot("location")

        # Notes (optional)
        ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
        notes_input = (
            ui.textarea(placeholder="z.B. je 12 Stück, 300g pro Packung", value=form_data["notes"])
            .classes("w-full")
            .props("outlined rows=2")
        )
        notes_input.bind_value(form_data, "notes")

        # Save Button
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            with (
                ui.button(on_click=save_item)
                .props("color=primary size=lg")
                .style("min-height: 48px")
                .mark("edit-save") as save_button
            ):
                with ui.row().classes("items-center gap-2"):
                    create_icon("actions/save", size="20px")
                    ui.label("Speichern")

        # Initial validation
        update_validation()

    # Bottom Navigation
    create_bottom_nav(current_page="items")
