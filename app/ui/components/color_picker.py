"""Farbwähler mit Vorschau für Admin-Dialoge (Kategorien, Lagerorte; Issue #398).

Vorher viermal gleich ausgeschrieben; Marker ``color-input`` und ``color-preview`` bleiben.
"""

from nicegui import ui


NEUTRAL_PREVIEW = "#E5E7EB"


def create_color_picker(value: str | None = None) -> ui.color_input:
    """``ui.color_input`` mit Vorschau-Kästchen, das der Auswahl folgt.

    Args:
        value: vorbelegte Farbe (Hex) oder ``None``.

    Returns:
        Das Eingabefeld; ``.value`` ist leer oder die gewählte Farbe.
    """
    initial = value or ""
    with ui.row().classes("w-full items-center gap-2 mb-4"):
        color_input = ui.color_input(label="Farbe", value=initial).classes("flex-1").mark("color-input")
        preview = (
            ui.element("div")
            .classes("w-10 h-10 rounded-lg border-2 border-gray-300")
            .style(f"background-color: {initial or NEUTRAL_PREVIEW}")
            .mark("color-preview")
        )
        color_input.on_value_change(lambda e: preview.style(f"background-color: {e.value or NEUTRAL_PREVIEW}"))
    return color_input
