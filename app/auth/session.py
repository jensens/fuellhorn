"""Login-Sitzung in ``app.storage.user`` (Issue #384).

NiceGUI hält den Sitzungsinhalt serverseitig; im Browser liegt nur ein signiertes
Cookie mit der Sitzungs-ID. Dessen Laufzeit ist ``REMEMBER_ME_MAX_AGE`` (gleitend,
Starlette setzt das Cookie bei jeder Antwort neu). Ohne "Angemeldet bleiben"
endet die Sitzung zusätzlich nach ``SESSION_MAX_AGE`` ohne Aktivität.

``session_version`` auf dem Benutzer steigt bei jeder Passwortänderung
(``User.set_password``); eine Sitzung mit alter Version wird beim nächsten
Request abgemeldet. Damit wirken Selbständerung, Admin-Reset und
``create-admin --reset-password`` sofort auf alle anderen Geräte.

Die Funktionen arbeiten auf einem beliebigen Mapping (Tests) und standardmäßig
auf ``app.storage.user``.
"""

from .. import config as app_config
from ..models.user import User
from collections.abc import MutableMapping
from datetime import datetime
from nicegui import app
from typing import Any


SESSION_EXPIRED_MESSAGE = "Sitzung abgelaufen, bitte neu anmelden."
PASSWORD_CHANGED_MESSAGE = "Das Passwort wurde geändert, bitte neu anmelden."


def _storage(storage: MutableMapping[str, Any] | None) -> MutableMapping[str, Any]:
    return app.storage.user if storage is None else storage


def start_session(
    user: User,
    *,
    remember_me: bool,
    storage: MutableMapping[str, Any] | None = None,
    now: datetime | None = None,
) -> None:
    """Beginnt eine frische Sitzung; Reste einer alten Sitzung werden verworfen."""
    data = _storage(storage)
    data.clear()
    data["authenticated"] = True
    data["user_id"] = user.id
    data["username"] = user.username
    data["remember_me"] = remember_me
    data["session_version"] = user.session_version
    touch_session(data, now=now)


def end_session(storage: MutableMapping[str, Any] | None = None, *, reason: str | None = None) -> None:
    """Beendet die Sitzung; ``reason`` zeigt die Login-Seite als Flash-Nachricht an.

    Der Schlüssel entspricht ``app.ui.components.flash.FLASH_KEY`` (kein Import,
    damit das Auth-Paket nicht vom UI-Paket abhängt).
    """
    data = _storage(storage)
    data.clear()
    if reason:
        data["flash"] = {"message": reason, "type": "warning"}


def touch_session(storage: MutableMapping[str, Any] | None = None, *, now: datetime | None = None) -> None:
    """Merkt die letzte Aktivität (verlängert die Sitzung ohne Remember-Me)."""
    _storage(storage)["last_seen"] = (now or datetime.now()).isoformat()


def refresh_session_version(user: User, storage: MutableMapping[str, Any] | None = None) -> None:
    """Nach eigener Passwortänderung: die eigene Sitzung bleibt gültig."""
    _storage(storage)["session_version"] = user.session_version


def session_problem(
    storage: MutableMapping[str, Any],
    user: User,
    *,
    now: datetime | None = None,
    max_age: int | None = None,
) -> str | None:
    """Grund, warum die Sitzung nicht mehr gilt, oder None wenn alles in Ordnung ist.

    Args:
        storage: Sitzungsdaten (``app.storage.user``)
        user: frisch aus der Datenbank geladener Benutzer
        now: Bezugszeitpunkt (Tests)
        max_age: Inaktivitätsgrenze in Sekunden ohne Remember-Me (Default: ``SESSION_MAX_AGE``)
    """
    now = now or datetime.now()
    if max_age is None:
        max_age = app_config.config.SESSION_MAX_AGE

    version = storage.get("session_version")
    last_seen_raw = storage.get("last_seen")
    if version is None or last_seen_raw is None:
        return SESSION_EXPIRED_MESSAGE
    if version != user.session_version:
        return PASSWORD_CHANGED_MESSAGE
    if not storage.get("remember_me", False):
        last_seen = datetime.fromisoformat(last_seen_raw)
        if (now - last_seen).total_seconds() >= max_age:
            return SESSION_EXPIRED_MESSAGE
    return None
