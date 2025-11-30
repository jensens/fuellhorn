"""Rate Limit Service - Progressive Verzögerung bei Login-Fehlversuchen.

Implementiert IP-basiertes Brute-Force-Schutz nach Nextcloud-Ansatz:
- Exponentiell steigende Verzögerung statt Account-Lockout
- Keine DoS-Gefahr durch absichtliche Sperrung
- OWASP-konform (keine User-Enumeration)
"""

import math

from ..models.login_attempt import LoginAttempt
from datetime import datetime
from datetime import timedelta
from sqlmodel import Session
from sqlmodel import select


# Konfiguration
MAX_DELAY_SECONDS = 60  # Maximale Verzögerung
RESET_AFTER_HOURS = 24  # Reset nach 24h ohne Fehlversuche


def get_delay_seconds(fail_count: int) -> int:
    """Berechnet die Verzögerung basierend auf Fehlversuchen.

    Verzögerung steigt exponentiell: 0s, 1s, 2s, 4s, 8s, 16s, 32s, 60s (max)

    Args:
        fail_count: Anzahl bisheriger Fehlversuche

    Returns:
        Verzögerung in Sekunden (0 bis MAX_DELAY_SECONDS)
    """
    if fail_count <= 1:
        return 0

    # Exponentiell: 2^(n-2) Sekunden
    delay = 2 ** (fail_count - 2)
    return int(min(delay, MAX_DELAY_SECONDS))


def get_login_attempt(session: Session, ip_address: str) -> LoginAttempt | None:
    """Ruft den Login-Versuch für eine IP ab.

    Args:
        session: Datenbank-Session
        ip_address: IP-Adresse

    Returns:
        LoginAttempt oder None wenn nicht vorhanden
    """
    statement = select(LoginAttempt).where(LoginAttempt.ip_address == ip_address)
    return session.exec(statement).first()


def get_required_delay(session: Session, ip_address: str) -> int:
    """Berechnet die erforderliche Wartezeit für eine IP.

    Args:
        session: Datenbank-Session
        ip_address: IP-Adresse

    Returns:
        Verbleibende Wartezeit in Sekunden (0 wenn keine Wartezeit nötig)
    """
    attempt = get_login_attempt(session, ip_address)

    if attempt is None:
        return 0

    # Reset nach 24h ohne Fehlversuche
    reset_threshold = datetime.now() - timedelta(hours=RESET_AFTER_HOURS)
    if attempt.last_attempt < reset_threshold:
        # Alte Einträge zurücksetzen
        attempt.fail_count = 0
        session.add(attempt)
        session.commit()
        return 0

    # Berechne Verzögerung
    delay_seconds = get_delay_seconds(attempt.fail_count)
    if delay_seconds == 0:
        return 0

    # Berechne verbleibende Wartezeit
    required_wait_until = attempt.last_attempt + timedelta(seconds=delay_seconds)
    remaining = (required_wait_until - datetime.now()).total_seconds()

    # ceil() damit auch 0.1s noch als 1s gewertet wird
    return max(0, math.ceil(remaining))


def record_failed_attempt(session: Session, ip_address: str) -> int:
    """Zeichnet einen fehlgeschlagenen Login-Versuch auf.

    Args:
        session: Datenbank-Session
        ip_address: IP-Adresse

    Returns:
        Neue Anzahl an Fehlversuchen
    """
    attempt = get_login_attempt(session, ip_address)

    if attempt is None:
        attempt = LoginAttempt(ip_address=ip_address, fail_count=1)
    else:
        # Reset nach 24h
        reset_threshold = datetime.now() - timedelta(hours=RESET_AFTER_HOURS)
        if attempt.last_attempt < reset_threshold:
            attempt.fail_count = 1
        else:
            attempt.fail_count += 1

    attempt.last_attempt = datetime.now()
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return attempt.fail_count


def record_successful_login(session: Session, ip_address: str) -> None:
    """Setzt den Fehlerzähler nach erfolgreichem Login zurück.

    Args:
        session: Datenbank-Session
        ip_address: IP-Adresse
    """
    attempt = get_login_attempt(session, ip_address)

    if attempt is not None:
        attempt.fail_count = 0
        attempt.last_attempt = datetime.now()
        session.add(attempt)
        session.commit()


def cleanup_old_attempts(session: Session) -> int:
    """Löscht alte Login-Versuche (älter als 24h).

    Kann periodisch aufgerufen werden um die Tabelle sauber zu halten.

    Args:
        session: Datenbank-Session

    Returns:
        Anzahl gelöschter Einträge
    """
    threshold = datetime.now() - timedelta(hours=RESET_AFTER_HOURS)
    statement = select(LoginAttempt).where(LoginAttempt.last_attempt < threshold)
    old_attempts = session.exec(statement).all()

    count = len(old_attempts)
    for attempt in old_attempts:
        session.delete(attempt)

    session.commit()
    return count
