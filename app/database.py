"""Datenbank-Initialisierung und Session-Management.

Stellt Funktionen für Datenbank-Verbindung und Session-Management bereit.
"""

from .config import Config
from .config import config

# Alle Models werden hier importiert damit SQLModel sie kennt
from .models import Category  # noqa: F401
from .models import CategoryShelfLife  # noqa: F401
from .models import Item  # noqa: F401
from .models import Location  # noqa: F401
from .models import LoginAttempt  # noqa: F401
from .models import SystemSettings  # noqa: F401
from .models import User  # noqa: F401
from .models import Withdrawal  # noqa: F401
from collections.abc import Generator
from sqlalchemy import Engine
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from typing import Any


# Globale Engine-Variable (wird lazy initialisiert)
_engine: Engine | None = None


def _enable_sqlite_foreign_keys(engine: Engine) -> Engine:
    """SQLite erzwingt Fremdschlüssel nur mit ``PRAGMA foreign_keys=ON`` pro Verbindung.

    Ohne das Pragma ließen sich in Dev und Tests referenzierte Zeilen still löschen
    und Waisen anlegen, während PostgreSQL (Produktion) Fehler wirft (Issue #378).
    """
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_app_engine(settings: Config | None = None) -> Engine:
    """Erstellt die Engine aus der Konfiguration.

    SQL-Echo hängt nur an SQL_ECHO, nicht an DEBUG: Es schreibt jedes Statement
    samt Parametern (Passwort-Hashes, Tokens, IPs) ins Log (Issue #374).
    """
    settings = config if settings is None else settings
    engine = create_engine(
        settings.get_database_url(),
        echo=settings.SQL_ECHO,
        connect_args=({"check_same_thread": False} if settings.DB_TYPE == "sqlite" else {}),
    )
    return _enable_sqlite_foreign_keys(engine)


def create_sqlite_test_engine() -> Engine:
    """In-Memory-SQLite mit StaticPool und Fremdschlüsseln (nur für Tests).

    Dieselbe Fremdschlüssel-Durchsetzung wie die Anwendungs-Engine, damit sich
    Tests bei Löschungen und toten Referenzen wie PostgreSQL verhalten (Issue #378).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return _enable_sqlite_foreign_keys(engine)


def get_engine() -> Engine:
    """Gibt die Datenbank-Engine zurück (lazy initialization).

    Returns:
        Engine: Die SQLModel Engine für DB-Operationen.
    """
    global _engine
    if _engine is None:
        _engine = create_app_engine()
    return _engine


def reset_engine() -> None:
    """Setzt die Engine zurück (nur für Tests!)."""
    global _engine
    _engine = None


def create_db_and_tables() -> None:
    """Erstellt alle Tabellen in der Datenbank."""
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session]:
    """Gibt eine Datenbank-Session zurück.

    Yields:
        Session: Eine SQLModel Session für DB-Operationen.
    """
    with Session(get_engine()) as session:
        yield session


def drop_db_and_tables() -> None:
    """Löscht alle Tabellen (nur für Tests!)."""
    SQLModel.metadata.drop_all(get_engine())
