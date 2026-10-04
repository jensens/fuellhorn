"""Einheitliche Fehleranzeige in Dialogen und Seiten (Issue #382).

Bekannte, fachliche Fehler (``ValueError``-Familie der Services, Auth-Fehler)
tragen deutsche Meldungen und werden angezeigt. Alles andere (``IntegrityError``,
``OperationalError``, Programmierfehler) landet mit Traceback im Log, der Nutzer
sieht eine generische Meldung ohne SQL oder Parameter.
"""

from ...auth.dependencies import AuthenticationError
from ...auth.dependencies import AuthorizationError
from ...services.auth_service import UserNotFoundError
import logging
from nicegui import ui


logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Die Aktion ist fehlgeschlagen. Details stehen im Server-Log."

KNOWN_ERRORS: tuple[type[Exception], ...] = (ValueError, AuthenticationError, AuthorizationError, UserNotFoundError)


def service_error_message(exc: Exception) -> str:
    """Liefert die anzeigbare Meldung; unbekannte Fehler werden geloggt und generisch gemeldet."""
    if isinstance(exc, KNOWN_ERRORS):
        return str(exc)
    logger.error("Unerwarteter Fehler in einer UI-Aktion", exc_info=exc)
    return GENERIC_ERROR_MESSAGE


def show_service_error(exc: Exception, error_label: ui.label | None = None) -> None:
    """Zeigt die Meldung im Dialog-Label oder als Notification."""
    message = service_error_message(exc)
    if error_label is not None:
        error_label.set_text(message)
        error_label.set_visibility(True)
    else:
        ui.notify(message, type="negative")
