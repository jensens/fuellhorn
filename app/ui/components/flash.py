"""Flash-Nachrichten über einen Seitenwechsel hinweg (Issue #381).

Ein ``ui.notify`` direkt vor ``ui.navigate.to`` erreicht den Browser meist nicht
mehr. Die Quelle legt die Nachricht im Session-Storage ab, die Zielseite zeigt
sie beim Aufbau einmalig an.
"""

from nicegui import app
from nicegui import ui


FLASH_KEY = "flash"


def set_flash(message: str, type: str = "info") -> None:  # noqa: A002 - wie ui.notify
    """Merkt eine Nachricht für die nächste aufgebaute Seite vor."""
    app.storage.user[FLASH_KEY] = {"message": message, "type": type}


def show_flash() -> None:
    """Zeigt eine vorgemerkte Nachricht an und entfernt sie aus dem Storage."""
    flash = app.storage.user.get(FLASH_KEY)
    if not flash:
        return
    del app.storage.user[FLASH_KEY]
    ui.notify(flash.get("message", ""), type=flash.get("type", "info"))
