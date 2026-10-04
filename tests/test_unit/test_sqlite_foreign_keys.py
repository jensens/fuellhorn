"""Tests: SQLite erzwingt Fremdschlüssel wie PostgreSQL (Issue #378).

Ohne ``PRAGMA foreign_keys=ON`` ließ SQLite in Dev und Tests referenzierte Zeilen
still löschen und Waisen anlegen; Produktion (PostgreSQL) warf dagegen Fehler.
"""

from app.models import Item
from app.models import ItemType
from datetime import date
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


class Settings:
    DEBUG = False
    SQL_ECHO = False
    DB_TYPE = "sqlite"
    DATABASE_URL = "sqlite://"

    def get_database_url(self) -> str:
        return self.DATABASE_URL


def test_app_engine_enables_sqlite_foreign_keys() -> None:
    from app.database import create_app_engine

    engine = create_app_engine(Settings())  # type: ignore[arg-type]
    with engine.connect() as connection:
        assert connection.execute(sa.text("PRAGMA foreign_keys")).scalar_one() == 1


def test_test_engine_helper_enables_sqlite_foreign_keys() -> None:
    from app.database import create_sqlite_test_engine

    engine = create_sqlite_test_engine()
    with engine.connect() as connection:
        assert connection.execute(sa.text("PRAGMA foreign_keys")).scalar_one() == 1


def test_item_with_unknown_location_is_rejected(session: Session) -> None:
    """Die Session-Fixture der Tests verhält sich wie PostgreSQL: kein Insert mit toter Referenz."""
    session.add(
        Item(
            product_name="Waise",
            best_before_date=date(2027, 1, 1),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=9999,
            created_by=9999,
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
