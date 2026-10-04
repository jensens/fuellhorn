"""Schnellerfassung im Keller (Issue #463).

Vor der Truhe zählt Tempo, nicht Vollständigkeit: Den Lagerort wählt man einmal, dann
tippt man Name, Menge, Einheit und Typ und ist sofort beim nächsten Artikel. Die Ware
steht ja physisch da, also ist sie gleich im Bestand - mit Status "Keine Haltbarkeits-
daten". Datum und Kategorie ergänzt die Nachpflege-Liste oben im Warmen.
"""

from ...auth import Permission
from ...auth import require_auth
from ...auth.dependencies import AuthenticationError
from ...auth.dependencies import AuthorizationError
from ...auth.dependencies import require_permission
from ...database import get_session
from ...services import item_service
from ...services import item_types
from ...services import location_service
from ...services.errors import ServiceValidationError
from ..components import create_bottom_nav
from ..components import create_item_type_chip_group
from ..components import create_location_chip_group
from ..components import create_mobile_page_container
from ..components import create_unit_chip_group
from ..theme.icons import create_icon
from ..utils.quantity import format_quantity
from ..validation.wizard_validation import validate_step1
from nicegui import ui


ROUTE = "/items/quick"
COMPLETION_ROUTE = "/items/incomplete"
# Einheit und Menge sind vorbelegt, damit im Keller nur der Name getippt werden muss
DEFAULT_UNIT = "Stück"
DEFAULT_QUANTITY = 1.0


# Route als Literal, damit der Konsistenztest sie im Quelltext findet (test_navigation_targets.py)
@ui.page("/items/quick")
@require_auth
def quick_capture() -> None:
    """Lagerort einmal, dann Artikel um Artikel."""
    with next(get_session()) as session:
        locations = location_service.get_all_locations(session)
    location_types = {location.id: location.location_type for location in locations}

    form: dict = {
        "product_name": "",
        "quantity": DEFAULT_QUANTITY,
        "unit": DEFAULT_UNIT,
        "item_type": None,
        "location_id": None,
    }
    captured: list[str] = []

    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with ui.button(on_click=lambda: ui.navigate.to("/dashboard")).classes("sp-back-btn").props("flat round"):
                create_icon("actions/back", size="24px")
            ui.label("Schnellerfassung").classes("sp-page-title")

    def choose_location(location_id: int) -> None:
        """Lagerort bestimmt, welche Typen überhaupt infrage kommen."""
        form["location_id"] = location_id
        render_form.refresh()

    def capture() -> None:
        """Erfassen und das Formular für den nächsten Artikel frei machen."""
        errors = validate_step1(form["product_name"], form["item_type"], form["quantity"], form["unit"])
        if errors:
            ui.notify(next(iter(errors.values())), type="warning")
            return

        # Nutzer frisch aus der DB und Berechtigung zur Laufzeit prüfen, wie im Wizard (#381)
        try:
            acting_user = require_permission(Permission.ITEMS_WRITE)
        except AuthenticationError:
            ui.notify("Bitte neu anmelden", type="negative")
            ui.navigate.to("/login")
            return
        except AuthorizationError:
            ui.notify("Keine Berechtigung zum Erfassen", type="negative")
            return
        if acting_user.id is None:
            ui.notify("Bitte neu anmelden", type="negative")
            return

        try:
            with next(get_session()) as session:
                item = item_service.quick_create_item(
                    session,
                    product_name=form["product_name"],
                    quantity=form["quantity"],
                    unit=form["unit"],
                    item_type=form["item_type"],
                    location_id=form["location_id"],
                    created_by=acting_user.id,
                )
                entry = f"{format_quantity(item.quantity, item.unit)} {item.product_name}"
        except ServiceValidationError as error:
            ui.notify(str(error), type="negative")
            return

        captured.insert(0, entry)
        # Nur der Name wird frei; Ort, Menge, Einheit und Typ bleiben für den nächsten Artikel
        form["product_name"] = ""
        render_form.refresh()
        render_captured.refresh()

    @ui.refreshable
    def render_form() -> None:
        location_id = form["location_id"]
        if location_id is None:
            ui.label("Zuerst den Lagerort wählen.").classes("text-sm text-stone")
            return

        offered = item_types.get_item_types_for_location(location_types[location_id])
        if form["item_type"] not in offered:
            # Ein einziger passender Typ muss nicht angetippt werden
            form["item_type"] = offered[0] if len(offered) == 1 else None

        ui.label("Produktname *").classes("text-sm font-medium text-charcoal mb-1 mt-4")
        (
            ui.input(
                placeholder="z.B. Erbsen aus Garten",
                value=form["product_name"],
                on_change=lambda event: form.update(product_name=event.value),
            )
            .props("outlined autofocus")
            .classes("w-full")
            .mark("quick-name")
            # Mit offener Handytastatur liegt der Knopf außer Sicht: Enter erfasst direkt, danach
            # steht der Fokus (autofocus) wieder im leeren Namensfeld
            .on("keydown.enter", capture)
        )

        ui.label("Menge *").classes("text-sm font-medium text-charcoal mb-1 mt-4")
        # min=0 wie im Wizard: Bei min=0.01 und step=1 markiert der Browser die 1 als ungültig;
        # "größer als 0" prüft validate_step1
        (
            ui.number(
                value=form["quantity"],
                min=0,
                step=1,
                on_change=lambda event: form.update(quantity=event.value),
            )
            .props("outlined")
            .classes("w-full")
            .mark("quick-quantity")
        )

        ui.label("Einheit *").classes("text-sm font-medium text-charcoal mb-1 mt-4")
        create_unit_chip_group(value=form["unit"], on_change=lambda unit: form.update(unit=unit))

        ui.label("Typ *").classes("text-sm font-medium text-charcoal mb-1 mt-4")
        create_item_type_chip_group(
            value=form["item_type"],
            on_change=lambda item_type: form.update(item_type=item_type),
            available=offered,
        )

        ui.button("Erfassen und weiter", on_click=capture).classes("sp-btn-primary w-full mt-6").mark("quick-save")

    @ui.refreshable
    def render_captured() -> None:
        if not captured:
            return
        ui.label(f"Gerade erfasst ({len(captured)})").classes("sp-page-title text-base mb-3 mt-6")
        for index, entry in enumerate(captured):
            with ui.element("div").classes("sp-admin-list-item w-full").mark(f"quick-captured-{index}"):
                ui.label(entry).classes("text-charcoal")

    with create_mobile_page_container():
        if not locations:
            with ui.card().classes("sp-dashboard-card w-full").mark("quick-no-locations"):
                ui.label("Noch kein Lagerort angelegt.").classes("text-lg text-charcoal font-medium")
                ui.button("Lagerorte verwalten", on_click=lambda: ui.navigate.to("/admin/locations")).props(
                    "color=primary"
                )
            create_bottom_nav(current_page="add")
            return

        ui.label("Wo bist du?").classes("text-sm font-medium text-charcoal mb-1")
        create_location_chip_group(locations, value=None, on_change=choose_location)

        render_form()
        render_captured()

        ui.button("Erfassung beenden", on_click=lambda: ui.navigate.to(COMPLETION_ROUTE)).props(
            "flat color=primary"
        ).classes("w-full mt-6").mark("quick-finish")

    create_bottom_nav(current_page="add")
