"""Datumsfeld mit Kalender-Popup für Wizard und Bearbeiten-Ansicht (Issue #346).

Vorher stand derselbe Block viermal im Code: Textfeld mit Maske, Kalender im
``append``-Slot und Bindung an ``form_data``. Statt der Bindung meldet das Feld
Änderungen über ``on_change``; getippte wie gepickte Werte laufen damit über
denselben Weg (Issue #362).
"""

from ...ui.theme.icons import create_icon
from ..utils.date_utils import format_german_date
from ..utils.date_utils import parse_german_date
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

    def set_value(self, value: date | None) -> None:
        """Setzt das Feld auf ein Datum; ``None`` leert es. Löst ``on_change`` aus."""
        self.input.value = format_german_date(value)


def create_date_field(
    *,
    label: str,
    value: date | None,
    marker: str,
    on_change: Callable[[date | None], None],
) -> DateField:
    """Beschriftung, Textfeld und Kalender-Popup für ein Datum.

    Args:
        label: Beschriftung über dem Feld, inklusive Pflichtfeld-Stern.
        value: vorbelegtes Datum oder ``None``.
        marker: Test-Marker des Eingabefeldes.
        on_change: wird bei jeder Änderung mit dem geparsten Datum gerufen;
            unvollständige oder unmögliche Eingaben ergeben ``None``.
    """
    label_element = ui.label(label).classes("text-sm font-medium mb-1 mt-4")

    with (
        ui.input(value=format_german_date(value))
        .classes("w-full")
        .props('outlined mask="##.##.####"')
        .style("max-width: 500px")
        .mark(marker) as date_input
    ):
        with date_input.add_slot("append"):
            with ui.element("div").classes("cursor-pointer"):
                create_icon("status/calendar", size="24px")
                with ui.menu() as date_menu:
                    date_picker = ui.date().bind_value(date_input).props('locale="de" mask="DD.MM.YYYY"')
                    date_picker.on_value_change(lambda _: date_menu.close())

    date_input.on_value_change(lambda event: on_change(parse_german_date(event.value)))

    return DateField(label=label_element, input=date_input)
