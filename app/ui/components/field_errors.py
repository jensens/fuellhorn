"""Eine Fehlerzeile pro Formularfeld (Issue #396).

Die ``validate_*``-Funktionen liefern Texte; vorher wurden sie nur auf Wahrheitswert geprüft
und der Nutzer sah bloß einen deaktivierten Button.
"""

from nicegui import ui


class FieldErrors:
    """Zeigt die Meldung aus ``validate_*`` direkt unter dem jeweiligen Feld.

    Beim Öffnen eines leeren Formulars wäre jede Pflichtfeld-Meldung Rauschen. Deshalb erscheint
    eine Meldung erst, wenn das Feld berührt wurde (``touch``) oder der Nutzer trotz Fehlern
    weiter wollte (``show(..., force=True)``); danach bleiben alle Meldungen sichtbar.
    Mit ``reveal_all=True`` (Edit-View, Felder vorbelegt) wird jede Meldung sofort gezeigt.
    """

    def __init__(self, *, reveal_all: bool = False) -> None:
        self._labels: dict[str, ui.label] = {}
        self._touched: set[str] = set()
        self._revealed = reveal_all

    def slot(self, field: str) -> ui.label:
        """Legt die (zunächst leere, unsichtbare) Fehlerzeile für ``field`` an der aktuellen Stelle an."""
        label = ui.label("").classes("text-xs sp-expiry-critical mt-1").mark(f"error-{field}")
        label.set_visibility(False)
        self._labels[field] = label
        return label

    def touch(self, field: str) -> None:
        """Das Feld wurde geändert; seine Meldung darf ab jetzt erscheinen."""
        self._touched.add(field)

    def show(self, errors: dict[str, str], *, force: bool = False) -> None:
        """Aktualisiert alle Fehlerzeilen; ``force`` gibt auch unberührte Felder frei."""
        if force:
            self._revealed = True
        for field, label in self._labels.items():
            message = errors.get(field)
            visible = message is not None and (self._revealed or field in self._touched)
            label.set_text(message if visible and message is not None else "")
            label.set_visibility(visible)
