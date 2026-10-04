"""Datumsfeld mit gestufter Auswahl für Wizard und Bearbeiten-Ansicht (Issues #346, #347).

Vorher stand derselbe Block viermal im Code: Textfeld mit Maske, Monatskalender im
``append``-Slot und Bindung an ``form_data``. Der Kalender zwang zum Durchklicken der
Monate, was bei Herstellungsdaten mehrere Jahre zurück mühsam war.

Jetzt gibt es ein Bauteil: Das Textfeld nimmt „15.03.2026“ und „03/2026“ an, die Auswahl
zeigt Jahre, Monate und Tage direkt und erlaubt, den Tag offen zu lassen. Statt einer
Bindung meldet das Feld Datum und Genauigkeit über ``on_change``; getippte wie gewählte
Werte laufen damit über denselben Weg (Issue #362).
"""

from ...ui.theme.icons import create_icon
from ..utils.date_utils import format_date_value
from ..utils.date_utils import parse_date_input
from calendar import monthrange
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from nicegui import ui


MONTH_NAMES = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
# Fenster der angezeigten Jahre und Schrittweite der Pfeile
YEARS_BEFORE = 2
YEARS_AFTER = 2
YEAR_STEP = 5


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


def _option_button(text: str, *, active: bool, on_click: Callable[[], None], marker: str) -> None:
    """Auswahlknopf der gestuften Datumsauswahl; mindestens 44 px für Finger (Issue #399)."""
    (
        ui.button(text, on_click=on_click)
        .props("flat dense no-caps")
        .classes("min-w-[44px] min-h-[44px] text-charcoal" + (" bg-oat" if active else ""))
        .mark(marker)
    )


def _build_picker(date_input: ui.input, menu: ui.menu, *, marker: str, initial: date | None) -> None:
    """Jahr, Monat und Tag zur direkten Auswahl; „ohne Tag“ übernimmt den Monat (Issues #346, #347)."""
    start = initial or date.today()
    state = {"year": start.year, "month": start.month}

    container = ui.column().classes("gap-2 p-3").style("min-width: 320px")

    def take(value: date, *, month_only: bool) -> None:
        date_input.value = format_date_value(value, month_only=month_only)
        menu.close()

    def choose(key: str, value: int) -> None:
        state[key] = value
        render()

    def shift_years(offset: int) -> None:
        state["year"] += offset
        render()

    def render() -> None:
        container.clear()
        with container:
            with ui.row().classes("items-center gap-1 flex-nowrap"):
                ui.button(icon="chevron_left", on_click=lambda: shift_years(-YEAR_STEP)).props("flat dense").mark(
                    f"{marker}-year-earlier"
                )
                for year in range(state["year"] - YEARS_BEFORE, state["year"] + YEARS_AFTER + 1):
                    _option_button(
                        str(year),
                        active=year == state["year"],
                        on_click=lambda y=year: choose("year", y),
                        marker=f"{marker}-year-{year}",
                    )
                ui.button(icon="chevron_right", on_click=lambda: shift_years(YEAR_STEP)).props("flat dense").mark(
                    f"{marker}-year-later"
                )

            with ui.row().classes("flex-wrap gap-1"):
                for index, name in enumerate(MONTH_NAMES, start=1):
                    _option_button(
                        name,
                        active=index == state["month"],
                        on_click=lambda m=index: choose("month", m),
                        marker=f"{marker}-month-{index}",
                    )

            with ui.row().classes("flex-wrap gap-1"):
                for day in range(1, monthrange(state["year"], state["month"])[1] + 1):
                    _option_button(
                        str(day),
                        active=initial is not None
                        and (initial.year, initial.month, initial.day) == (state["year"], state["month"], day),
                        on_click=lambda d=day: take(date(state["year"], state["month"], d), month_only=False),
                        marker=f"{marker}-day-{day}",
                    )

            ui.button(
                "ohne Tag übernehmen",
                on_click=lambda: take(date(state["year"], state["month"], 1), month_only=True),
            ).props("flat no-caps").classes("w-full text-fern").mark(f"{marker}-month-only")

    render()


def create_date_field(
    *,
    label: str,
    value: date | None,
    marker: str,
    on_change: Callable[[date | None, bool], None],
    month_only: bool = False,
) -> DateField:
    """Beschriftung, Textfeld und gestufte Auswahl für ein Datum mit optionalem Tag.

    Args:
        label: Beschriftung über dem Feld, inklusive Pflichtfeld-Stern.
        value: vorbelegtes Datum oder ``None``.
        marker: Test-Marker des Eingabefeldes; die Auswahl nutzt ``<marker>-picker-…``.
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
                    _build_picker(date_input, date_menu, marker=f"{marker}-picker", initial=value)

    date_input.on_value_change(lambda event: on_change(*parse_date_input(event.value)))

    return DateField(label=label_element, input=date_input)
