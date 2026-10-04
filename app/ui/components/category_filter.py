"""Kompakter Kategorie-Filter: eine Zeile, Auswahl im Panel von unten (Issue #471).

Zugeklappt steht nur die Schaltfläche „Kategorien (n)“, darunter die gewählten
Kategorien als Chips (Tipp entfernt sie). Die Auswahl selbst liegt in einem Panel
von unten, gruppiert wie in der Kategorie-Auswahl beim Erfassen. Ein Gruppen-Chip
steht für die ganze Gruppe; das Auflösen in Kinder macht der Aufrufer (#395).
"""

from ...models.category import Category
from ..theme import Colors
from ..theme import get_contrast_text_color
from collections import defaultdict
from collections.abc import Callable
from collections.abc import Sequence
from nicegui import ui


LABEL = "Kategorien"
# Gruppen-Überschrift wie in der Kategorie-Auswahl beim Erfassen (category_chips.py)
HEADING_CLASSES = "text-xs font-bold uppercase tracking-wide text-stone-500 mt-1"


class CategoryFilter:
    """Mehrfachauswahl von Kategorien; meldet jede Änderung über ``on_change``."""

    def __init__(self, categories: Sequence[Category], on_change: Callable[[set[int]], None]) -> None:
        self._categories = [c for c in categories if c.id is not None]
        self._on_change = on_change
        self._selected: set[int] = set()
        self._colors = {c.id: c.color or Colors.DEFAULT_GRAY for c in self._categories if c.id is not None}
        self._sheet_chips: dict[int, ui.button] = {}

        self.button = (
            ui.button(LABEL, on_click=lambda: self.dialog.open())
            .props("flat no-caps icon-right=expand_more align=between")
            .classes("w-full min-h-[44px]")
            # wie die Auswahlfelder Lagerort/Artikel-Typ (.q-field--outlined im Theme)
            .style(
                "border: 2px solid var(--sp-sage-light); border-radius: var(--sp-radius-md); "
                "color: var(--sp-charcoal) !important; font-weight: 400;"
            )
            .mark("category-filter-open")
        )
        self._selected_row = ui.row().classes("w-full gap-2 flex-wrap")
        self.dialog = self._build_sheet()

    @property
    def selected(self) -> set[int]:
        return set(self._selected)

    def clear(self) -> None:
        """Auswahl leeren, ohne ``on_change`` auszulösen (z. B. vor „Filter zurücksetzen“)."""
        self._selected.clear()
        self._refresh()

    def _toggle(self, category_id: int) -> None:
        if category_id in self._selected:
            self._selected.remove(category_id)
        else:
            self._selected.add(category_id)
        self._changed()

    def _remove(self, category_id: int) -> None:
        self._selected.discard(category_id)
        self._changed()

    def _clear_and_notify(self) -> None:
        self.clear()
        self._on_change(self.selected)

    def _changed(self) -> None:
        self._refresh()
        self._on_change(self.selected)

    def _refresh(self) -> None:
        count = len(self._selected)
        self.button.set_text(f"{LABEL} ({count})" if count else LABEL)
        for category_id, chip in self._sheet_chips.items():
            self._style_sheet_chip(chip, category_id)
        self._selected_row.clear()
        with self._selected_row:
            for category in self._categories:
                if category.id in self._selected:
                    self._render_selected_chip(category)

    def _style_sheet_chip(self, chip: ui.button, category_id: int) -> None:
        color = self._colors[category_id]
        if category_id in self._selected:
            text_color = get_contrast_text_color(color)
            chip.style(
                f"background-color: {color} !important; border: 2px solid {color}; color: {text_color} !important;"
            )
        else:
            chip.style(
                f"background-color: {Colors.NEUTRAL_LIGHT} !important; border: 2px solid {color}; "
                f"color: {Colors.NEUTRAL_TEXT} !important;"
            )

    def _render_selected_chip(self, category: Category) -> None:
        assert category.id is not None
        category_id = category.id
        color = self._colors[category_id]
        (
            ui.button(category.name, on_click=lambda: self._remove(category_id))
            .props("flat no-caps icon-right=close")
            .classes("rounded-full px-3 min-h-[44px] text-sm")
            .style(
                f"background-color: {color} !important; border: 2px solid {color}; "
                f"color: {get_contrast_text_color(color)} !important;"
            )
            .mark(f"filter-selected-{category_id}")
        )

    def _render_sheet_chip(self, category: Category, *, is_group: bool = False) -> None:
        assert category.id is not None
        category_id = category.id
        # Die Gruppe steht als Überschrift darüber; ihr Chip heißt „Alle“ und wählt die ganze Gruppe
        text = "● Alle" if is_group else f"● {category.name}"
        chip = (
            ui.button(text, on_click=lambda: self._toggle(category_id))
            .classes("rounded-full px-4 min-h-[44px] text-sm" + (" font-semibold" if is_group else ""))
            .props("flat no-caps")
            .mark(f"filter-category-{category_id}")
        )
        self._sheet_chips[category_id] = chip
        self._style_sheet_chip(chip, category_id)

    def _build_sheet(self) -> ui.dialog:
        children_by_parent: dict[int, list[Category]] = defaultdict(list)
        for category in self._categories:
            if category.parent_id is not None:
                children_by_parent[category.parent_id].append(category)
        groups = [c for c in self._categories if c.id in children_by_parent]
        standalone = [c for c in self._categories if c.parent_id is None and c.id not in children_by_parent]

        dialog = ui.dialog().props("position=bottom").mark("category-filter-sheet")
        dialog.style("width: 100%; max-width: 800px;")
        with dialog, ui.card().classes("sp-bottom-sheet w-full p-0"):
            ui.element("div").classes("sp-bottom-sheet-handle")
            with ui.row().classes("sp-bottom-sheet-header w-full items-center justify-between"):
                ui.label(LABEL).classes("sp-bottom-sheet-title")
                with ui.row().classes("gap-1 items-center"):
                    ui.button("Alle abwählen", on_click=self._clear_and_notify).props("flat no-caps").classes(
                        "min-h-[44px]"
                    ).mark("category-filter-clear")
                    ui.button("Fertig", on_click=dialog.close).props("unelevated no-caps").classes("min-h-[44px]").mark(
                        "category-filter-done"
                    )
            with ui.column().classes("sp-bottom-sheet-body w-full gap-2").style("max-height: 70vh; overflow-y: auto;"):
                # Gruppiert wie im Wizard: Überschrift, dann „Alle“ und die Kategorien (#395)
                for group in groups:
                    assert group.id is not None
                    ui.label(group.name).classes(HEADING_CLASSES)
                    with ui.row().classes("w-full gap-2 flex-wrap items-center"):
                        self._render_sheet_chip(group, is_group=True)
                        for child in children_by_parent[group.id]:
                            self._render_sheet_chip(child)
                if standalone:
                    if groups:
                        ui.label("Sonstiges").classes(HEADING_CLASSES)
                    with ui.row().classes("w-full gap-2 flex-wrap"):
                        for category in standalone:
                            self._render_sheet_chip(category)
        return dialog


def create_category_filter(categories: Sequence[Category], on_change: Callable[[set[int]], None]) -> CategoryFilter:
    """Kompakten Kategorie-Filter anlegen (Schaltfläche, gewählte Chips, Panel)."""
    return CategoryFilter(categories, on_change)
