#!/usr/bin/env python3
"""Default-Kategorien und -Haltbarkeiten für die lokale Entwicklung einspielen.

Dünner Wrapper um ``app.seed.seed_shelf_life_defaults``; die Seed-Logik lebt nur dort.
In Produktion ``fuellhorn seed shelf-life-defaults`` nutzen.

Usage:
    uv run python scripts/seed_shelf_life_defaults.py
"""

from pathlib import Path
import sys


# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import run_migrations  # noqa: E402
from app.database import get_engine  # noqa: E402
from app.seed import seed_shelf_life_defaults  # noqa: E402
from sqlmodel import Session  # noqa: E402


def main() -> None:
    """Migrationen anwenden und Default-Haltbarkeiten einspielen."""
    print("🌱 Default-Haltbarkeiten initialisieren...")
    run_migrations()

    with Session(get_engine()) as session:
        categories, shelf_lives = seed_shelf_life_defaults(session)

    print(f"  Kategorien: {categories}, Haltbarkeiten: {shelf_lives}")
    print("✅ Fertig!")


if __name__ == "__main__":
    main()
