"""Datenbank-Initialisierung und Session-Management.

Stellt Funktionen für Datenbank-Verbindung und Session-Management bereit.
"""

from .config import config

# Alle Models werden hier importiert damit SQLModel sie kennt
from .models import Category  # noqa: F401
from .models import CategoryShelfLife  # noqa: F401
from .models import Item  # noqa: F401
from .models import Location  # noqa: F401
from .models import SystemSettings  # noqa: F401
from .models import User  # noqa: F401
from collections.abc import Generator
from sqlalchemy import Engine
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine


# Globale Engine-Variable (wird lazy initialisiert)
_engine: Engine | None = None


def get_engine() -> Engine:
    """Gibt die Datenbank-Engine zurück (lazy initialization).

    Returns:
        Engine: Die SQLModel Engine für DB-Operationen.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.get_database_url(),
            echo=config.DEBUG,  # SQL-Statements loggen in Debug-Modus
            connect_args=({"check_same_thread": False} if config.DB_TYPE == "sqlite" else {}),
        )
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
