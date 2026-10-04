"""Datumsfeld mit Kalender-Popup für Wizard und Bearbeiten-Ansicht (Issue #346).

Vorher stand derselbe Block viermal im Code: Textfeld mit Maske, Kalender im
``append``-Slot und Bindung an ``form_data``. Statt der Bindung meldet das Feld
Änderungen über ``on_change``; getippte wie gepickte Werte laufen damit über
denselben Weg (Issue #362).
"""

from ...ui.theme.icons import create_icon
from ..utils.date_utils import format_date_value
from ..utils.date_utils import parse_date_input
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from nicegui import ui


@dataclass(frozen=True)
class DateField:
    """Die Elemente eines Datumsfeldes, soweit Aufrufer sie nachträglich ändern.

    ``label`` braucht die Bearbeiten-Ansicht, weil die Beschriftung dem Artikel-Typ folgt;
    ``input`` braucht sie, um das Einfrierdatum beim Typwechsel zu setzen oder zu leeren.
    """

    label: ui.label
    input: ui.input

    def set_value(self, value: date | None, *, month_only: bool = False) -> None:
        """Setzt das Feld auf ein Datum; ``None`` leert es. Löst ``on_change`` aus."""
        self.input.value = format_date_value(value, month_only=month_only)


def create_date_field(
    *,
    label: str,
    value: date | None,
    marker: str,
    on_change: Callable[[date | None, bool], None],
    month_only: bool = False,
) -> DateField:
    """Beschriftung, Textfeld und Kalender-Popup für ein Datum mit optionalem Tag.

    Args:
        label: Beschriftung über dem Feld, inklusive Pflichtfeld-Stern.
        value: vorbelegtes Datum oder ``None``.
        marker: Test-Marker des Eingabefeldes.
        on_change: wird bei jeder Änderung mit Datum und Monatsgenauigkeit gerufen;
            unvollständige oder unmögliche Eingaben ergeben ``(None, False)``.
        month_only: ob das vorbelegte Datum nur monatsgenau ist.
    """
    label_element = ui.label(label).classes("text-sm font-medium mb-1 mt-4")

    with (
        ui.input(value=format_date_value(value, month_only=month_only))
        .classes("w-full")
        # Ohne Maske, weil „03/2026“ kürzer ist als „15.03.2026“ (Issue #347)
        .props('outlined hint="TT.MM.JJJJ oder MM/JJJJ"')
        .style("max-width: 500px")
        .mark(marker) as date_input
    ):
        with date_input.add_slot("append"):
            with ui.element("div").classes("cursor-pointer"):
                create_icon("status/calendar", size="24px")
                with ui.menu() as date_menu:
                    date_picker = ui.date().bind_value(date_input).props('locale="de" mask="DD.MM.YYYY"')
                    date_picker.on_value_change(lambda _: date_menu.close())

    date_input.on_value_change(lambda event: on_change(*parse_date_input(event.value)))

    return DateField(label=label_element, input=date_input)
