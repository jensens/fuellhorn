"""Typisierte Service-Fehler mit deutschen Meldungen für die UI (Issue #382).

Alle Fehler sind ``ValueError``-Unterklassen, damit bestehende Aufrufer, die
``ValueError`` fangen, weiter funktionieren. Die Meldung ist so formuliert, dass
die UI sie unverändert anzeigen kann.
"""


class ServiceError(ValueError):
    """Fachlicher Fehler, dessen Meldung dem Nutzer gezeigt werden darf."""


class ServiceValidationError(ServiceError):
    """Ungültige Eingabe (Format, Bereich, Kombination)."""


class StaleStockError(ServiceError):
    """Der Bestand hat sich seit dem Lesen geändert (zwei Nutzer, ein Artikel; Issue #394)."""

    def __init__(self, message: str = "Bestand hat sich geändert, bitte neu laden.") -> None:
        super().__init__(message)


class AlreadyConsumedError(ServiceError):
    """Der Artikel ist bereits vollständig entnommen (Issue #394)."""

    def __init__(self, product_name: str) -> None:
        super().__init__(f"'{product_name}' ist bereits vollständig entnommen.")


class DuplicateNameError(ServiceError):
    """Ein eindeutiges Feld (Name, Benutzername, E-Mail) ist bereits vergeben."""

    def __init__(self, field: str, value: str, label: str) -> None:
        self.field = field
        self.value = value
        self.label = label
        super().__init__(f"{label} '{value}' ist bereits vorhanden")
