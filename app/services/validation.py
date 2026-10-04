"""Zentrale Eingabevalidierung für alle Service-Einstiege (Issue #383).

Vorher prüfte nur die UI (und nur punktuell): Admin-Dialoge und CLI akzeptierten
Passwörter wie "1", Benutzernamen mit Leerzeichen, E-Mails ohne "@", beliebige
Strings als Farbe (landen in ``style()``), Haltbarkeiten außerhalb 1-36 Monaten
und leere Namen. Alle Funktionen trimmen, prüfen und geben den bereinigten Wert
zurück oder werfen ``ServiceValidationError`` mit deutscher Meldung.
"""

from .errors import ServiceValidationError
import re


MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 100
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.@+-]{3,50}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
SHELF_LIFE_MIN_MONTHS = 1
SHELF_LIFE_MAX_MONTHS = 36


def require_non_empty(value: str | None, label: str) -> str:
    """Trimmt und verlangt mindestens ein sichtbares Zeichen."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise ServiceValidationError(f"{label} darf nicht leer sein.")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ServiceValidationError(f"{label} darf höchstens {MAX_NAME_LENGTH} Zeichen lang sein.")
    return cleaned


def validate_username(value: str | None) -> str:
    cleaned = require_non_empty(value, "Benutzername")
    if not USERNAME_PATTERN.match(cleaned):
        raise ServiceValidationError(
            "Benutzername: 3 bis 50 Zeichen, nur Buchstaben, Ziffern und . _ @ + - (keine Leerzeichen)."
        )
    return cleaned


def validate_email(value: str | None) -> str:
    cleaned = require_non_empty(value, "E-Mail-Adresse")
    if not EMAIL_PATTERN.match(cleaned):
        raise ServiceValidationError(f"'{cleaned}' ist keine gültige E-Mail-Adresse.")
    return cleaned


def validate_password(value: str | None) -> str:
    if value is None or len(value) < MIN_PASSWORD_LENGTH:
        raise ServiceValidationError(f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben.")
    if value.strip() != value:
        raise ServiceValidationError("Das Passwort darf nicht mit Leerzeichen beginnen oder enden.")
    return value


def validate_hex_color(value: str | None) -> str | None:
    """Erlaubt nur #RGB/#RRGGBB; verhindert CSS-Injection über ``style()`` (None bleibt None)."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if not HEX_COLOR_PATTERN.match(cleaned):
        raise ServiceValidationError(f"'{cleaned}' ist keine gültige Farbe (erwartet #RRGGBB).")
    return cleaned.upper() if len(cleaned) == 7 else cleaned


def validate_shelf_life_months(months_min: int, months_max: int) -> tuple[int, int]:
    for label, value in (("Mindest-Haltbarkeit", months_min), ("Maximal-Haltbarkeit", months_max)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ServiceValidationError(f"{label} muss eine ganze Zahl sein.")
        if not SHELF_LIFE_MIN_MONTHS <= value <= SHELF_LIFE_MAX_MONTHS:
            raise ServiceValidationError(
                f"{label} muss zwischen {SHELF_LIFE_MIN_MONTHS} und {SHELF_LIFE_MAX_MONTHS} Monaten liegen."
            )
    if months_min > months_max:
        raise ServiceValidationError("Mindest-Haltbarkeit darf nicht größer als die Maximal-Haltbarkeit sein.")
    return months_min, months_max
