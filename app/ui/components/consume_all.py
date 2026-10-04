"""Bestätigte Komplett-Entnahme ("Alles entnehmen") für Swipe-Aktionen (Issue #367).

Gemeinsam für Vorratsliste und Dashboard: Rückfrage, Buchung mit dem aktuellen
Nutzer (Withdrawal-Eintrag) und verständliche Meldung, wenn der Artikel inzwischen
nicht mehr existiert.
"""

from ...auth.dependencies import AuthenticationError
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.item import Item
from ...services import item_service
from ...services.errors import ServiceError
from ..utils.quantity import format_quantity
from collections.abc import Callable
from nicegui import ui


def confirm_consume_all(item: Item, on_done: Callable[[], None]) -> None:
    """Fragt nach und bucht den Artikel dann als komplett entnommen.

    Args:
        item: Der Artikel (Zustand zum Zeitpunkt des Renderns).
        on_done: Wird nach erfolgreicher Buchung oder nach einem Fehler aufgerufen,
            damit die Seite ihren Zustand neu lädt.
    """
    dialog = ui.dialog()
    with dialog, ui.card().classes("p-4 min-w-[300px]"):
        ui.label("Alles entnehmen?").classes("text-lg font-semibold mb-2")
        ui.label(
            f"{item.product_name}: {format_quantity(item.quantity, item.unit)} werden als entnommen gebucht."
        ).classes("text-sm text-stone mb-4")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat").mark("consume-all-cancel")
            ui.button("Entnehmen", on_click=lambda: _consume(dialog, item, on_done)).props("color=positive").mark(
                "consume-all-confirm"
            )
    dialog.open()


def _consume(dialog: ui.dialog, item: Item, on_done: Callable[[], None]) -> None:
    dialog.close()
    if item.id is None:
        ui.notify("Artikel-ID nicht gefunden", type="negative")
        return

    try:
        user = get_current_user(require_auth=True)
    except AuthenticationError:
        ui.notify("Bitte neu anmelden", type="negative")
        ui.navigate.to("/login")
        return
    assert user is not None and user.id is not None

    try:
        with next(get_session()) as session:
            item_service.mark_item_consumed(session, item.id, user.id, expected_quantity=item.quantity)
    except ServiceError as e:
        # bereits entnommen oder Bestand inzwischen geändert (Issue #394)
        ui.notify(str(e), type="warning")
        on_done()
        return
    except ValueError:
        ui.notify(f"{item.product_name} ist nicht mehr vorhanden", type="negative")
        on_done()
        return

    ui.notify(f"{item.product_name} komplett entnommen", type="positive")
    on_done()
