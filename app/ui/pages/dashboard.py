"""Dashboard - Main Page after Login."""

from ...auth import require_auth
from nicegui import ui


@ui.page("/dashboard")
@require_auth
def dashboard() -> None:
    """Dashboard - wird spaeter mit Inventar-Overview gefuellt."""
    with ui.column().classes("w-full p-4"):
        ui.label("Dashboard").classes("text-h4 mb-4")
        ui.label("Willkommen bei Fuellhorn!").classes("text-subtitle1")
        ui.label("Inventar-Uebersicht wird hier angezeigt.").classes("text-body2 text-gray-600 mt-4")
