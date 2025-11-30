"""LoginAttempt Model für IP-basiertes Brute-Force-Tracking.

Trackt fehlgeschlagene Login-Versuche pro IP-Adresse für progressive Verzögerung.
"""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class LoginAttempt(SQLModel, table=True):
    """Login-Versuch Tracking pro IP-Adresse.

    Ermöglicht progressive Verzögerung bei wiederholten Fehlversuchen
    ohne Account-Sperrung (OWASP-konform).
    """

    __tablename__ = "login_attempt"

    # Primary Key
    id: int | None = Field(default=None, primary_key=True)

    # IP-Adresse (Index für schnelle Abfragen)
    ip_address: str = Field(index=True)

    # Anzahl fehlgeschlagener Versuche
    fail_count: int = Field(default=0)

    # Zeitpunkt des letzten Versuchs
    last_attempt: datetime = Field(default_factory=datetime.now)

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<LoginAttempt {self.ip_address} ({self.fail_count} Fehlversuche)>"
