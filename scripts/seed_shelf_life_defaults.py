#!/usr/bin/env python3
"""Seed-Script für Default-Haltbarkeiten.

Dieses Script pflegt die recherchierten Haltbarkeitszeiten für verschiedene
Lebensmittelkategorien in die Datenbank ein.

Ausführung:
    uv run python scripts/seed_shelf_life_defaults.py

Das Script ist idempotent - es kann mehrfach ausgeführt werden ohne
Duplikate zu erzeugen (nutzt create_or_update).
"""

from pathlib import Path
import sys


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import create_db_and_tables
from app.database import get_engine
from app.seed import CATEGORIES_FRESH_ONLY
from app.seed import CATEGORIES_WITH_SHELF_LIFE
from app.seed import SOURCES
from app.seed import create_or_update_shelf_life
from app.seed import get_or_create_category
from app.seed import get_or_create_system_user
from sqlmodel import Session


def seed_shelf_life_defaults() -> None:
    """Seed default shelf life data into the database."""
    print("=" * 60)
    print("Seeding Default-Haltbarkeiten")
    print("=" * 60)

    # Ensure tables exist
    create_db_and_tables()

    with Session(get_engine()) as session:
        # Get admin user ID for created_by
        admin_id = get_or_create_system_user(session)
        print(f"\nVerwende Admin-User ID: {admin_id}")

        categories_created = 0
        shelf_lives_created = 0

        print("\nVerarbeite Kategorien und Haltbarkeiten...")
        print("-" * 60)

        # Track created categories by name for parent lookup
        category_by_name: dict[str, int] = {}

        for name, color, parent_name, shelf_lives in CATEGORIES_WITH_SHELF_LIFE:
            parent_id = category_by_name.get(parent_name) if parent_name else None  # type: ignore[arg-type]
            category = get_or_create_category(session, name, color, admin_id, parent_id)
            category_by_name[name] = category.id  # type: ignore[assignment]
            categories_created += 1
            print(f"  Kategorie '{name}' (ID: {category.id})")

            for storage_type, months_min, months_max, source_key in shelf_lives:
                source_url = SOURCES.get(source_key, "")
                create_or_update_shelf_life(
                    session,
                    category.id,  # type: ignore[arg-type]
                    storage_type,
                    months_min,
                    months_max,
                    source_url,
                )
                shelf_lives_created += 1
                print(f"    {storage_type.value} = {months_min}-{months_max} Monate")

        # Fresh-only categories
        print("\nVerarbeite FRESH-only Kategorien...")
        for name, color in CATEGORIES_FRESH_ONLY:
            category = get_or_create_category(session, name, color, admin_id)
            categories_created += 1
            print(f"  Kategorie '{name}' (ID: {category.id})")

        print("-" * 60)
        print("\nZusammenfassung:")
        print(f"  Kategorien verarbeitet: {categories_created}")
        print(f"  Haltbarkeiten verarbeitet: {shelf_lives_created}")
        print("=" * 60)


if __name__ == "__main__":
    seed_shelf_life_defaults()
