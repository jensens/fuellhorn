"""Nachpflegen: Liste der unvollständigen Artikel (Issue #463).

Unten im Keller zählt nur Name, Menge, Einheit und Typ. Oben im Warmen steht hier, was
noch fehlt. Eine eigene Seite statt eines Filters, damit man beim Ergänzen in der Liste
bleibt: Jede Zeile führt in die Bearbeiten-Ansicht und von dort wieder hierher zurück.
"""

from ...auth import require_auth
from ...database import get_session
from ...services import expiry_service
from ...services import location_service
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from ..theme.icons import create_icon
from ..utils.quantity import format_quantity
from nicegui import ui


ROUTE = "/items/incomplete"


# Route als Literal, damit der Konsistenztest sie im Quelltext findet (test_navigation_targets.py)
@ui.page("/items/incomplete")
@require_auth
def incomplete_items() -> None:
    """Artikel mit Lücken, zuletzt erfasste zuerst."""
    with next(get_session()) as session:
        entries = expiry_service.get_items_needing_completion(session)
        location_names = {location.id: location.name for location in location_service.get_all_locations(session)}

    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with ui.button(on_click=lambda: ui.navigate.to("/dashboard")).classes("sp-back-btn").props("flat round"):
                create_icon("actions/back", size="24px")
            ui.label(f"Nachpflegen ({len(entries)})").classes("sp-page-title")

    with create_mobile_page_container():
        if not entries:
            with ui.card().classes("sp-dashboard-card w-full").mark("incomplete-empty"):
                with ui.column().classes("w-full items-center py-8"):
                    create_icon("status/ok", size="48px")
                    ui.label("Nichts nachzupflegen").classes("text-lg text-charcoal font-medium")
                    ui.label("Alle Artikel haben Datum und Kategorie.").classes("text-sm text-stone text-center")
        else:
            ui.label("Antippen, um die fehlenden Angaben zu ergänzen.").classes("text-sm text-stone mb-3")

        for entry in entries:
            item = entry.item
            if item.id is None:
                continue
            with (
                ui.element("div")
                .classes("sp-admin-list-item w-full cursor-pointer")
                .mark(f"incomplete-item-{item.id}")
                .on(
                    "click",
                    lambda _, item_id=item.id: ui.navigate.to(f"/items/{item_id}/edit?back={ROUTE}"),
                )
            ):
                with ui.column().classes("gap-1 flex-1"):
                    ui.label(item.product_name).classes("font-medium text-lg text-charcoal")
                    details = [format_quantity(item.quantity, item.unit)]
                    location_name = location_names.get(item.location_id)
                    if location_name:
                        details.append(location_name)
                    ui.label(" · ".join(details)).classes("text-sm text-stone")
                    ui.label("Fehlt: " + ", ".join(entry.missing)).classes("text-xs sp-expiry-warning").mark(
                        f"incomplete-missing-{item.id}"
                    )
                create_icon("actions/edit", size="20px")

    create_bottom_nav(current_page="items")
