"""Bestätigungsdialog zum Löschen für Admin-Seiten (Benutzer, Kategorien, Lagerorte; Issue #398).

Vorher dreimal gleich ausgeschrieben. Die fachliche Ablehnung kommt typisiert aus dem Service
und erscheint im Dialog (#379, #382); die Berechtigung wird zur Laufzeit geprüft (#381).
"""

from ...auth import Permission
from ...auth.decorators import with_permission_check
from .errors import show_service_error
from collections.abc import Callable
from nicegui import ui


def open_confirm_delete_dialog(
    *,
    title: str,
    question: str,
    permission: Permission,
    on_confirm: Callable[[], None],
    success_message: str,
    redirect: str,
) -> None:
    """Öffnet den Dialog; ``on_confirm`` führt das Löschen aus und wirft bei Ablehnung.

    Args:
        title: Dialogtitel, z.B. "Kategorie löschen".
        question: Rückfrage mit dem Namen des Objekts.
        permission: zur Laufzeit geprüfte Berechtigung.
        on_confirm: löscht über den Service; Ausnahmen landen als Meldung im Dialog.
        success_message: Benachrichtigung nach Erfolg.
        redirect: Ziel nach Erfolg (die Seite baut sich dort neu auf).
    """
    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-md"):
        ui.label(title).classes("text-h6 font-semibold mb-4 text-fern")
        ui.label(question).classes("mb-2")
        ui.label("Diese Aktion kann nicht rückgängig gemacht werden.").classes("text-sm text-red-600 mb-4")

        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(permission)
            def confirm_delete() -> None:
                try:
                    on_confirm()
                except Exception as e:
                    show_service_error(e, error_label)
                    return
                ui.notify(success_message, type="positive")
                dialog.close()
                ui.navigate.to(redirect)

            ui.button("Löschen", on_click=confirm_delete).classes("sp-btn-danger")

    dialog.open()
