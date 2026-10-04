"""Typisierte Service-Fehler mit deutschen Meldungen für die UI (Issue #382).

Alle Fehler sind ``ValueError``-Unterklassen, damit bestehende Aufrufer, die
``ValueError`` fangen, weiter funktionieren. Die Meldung ist so formuliert, dass
die UI sie unverändert anzeigen kann.
"""


class ServiceError(ValueError):
    """Fachlicher Fehler, dessen Meldung dem Nutzer gezeigt werden darf."""


class ServiceValidationError(ServiceError):
    """Ungültige Eingabe (Format, Bereich, Kombination)."""


class DuplicateNameError(ServiceError):
    """Ein eindeutiges Feld (Name, Benutzername, E-Mail) ist bereits vergeben."""

    def __init__(self, field: str, value: str, label: str) -> None:
        self.field = field
        self.value = value
        self.label = label
        super().__init__(f"{label} '{value}' ist bereits vorhanden")
