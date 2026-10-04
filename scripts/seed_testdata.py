"""Testdaten für die lokale Entwicklung einspielen (Admin admin/admin123, Kategorien, Lagerorte, Beispiel-Items).

Dünner Wrapper um ``app.seed.seed_testdata``; die Seed-Logik lebt nur dort (#376).
Für Produktion ungeeignet, dort ``fuellhorn create-admin`` und ``fuellhorn seed shelf-life-defaults`` nutzen.

Usage:
    uv run python scripts/seed_testdata.py
"""

from pathlib import Path
import sys


# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import run_migrations  # noqa: E402
from app.database import get_engine  # noqa: E402
from app.seed import TESTDATA_ADMIN_PASSWORD  # noqa: E402
from app.seed import seed_testdata  # noqa: E402
from sqlmodel import Session  # noqa: E402


def main() -> None:
    """Migrationen anwenden und Testdaten einspielen."""
    print("🌱 Testdaten initialisieren...")
    run_migrations()

    with Session(get_engine()) as session:
        result = seed_testdata(session)

    admin_status = f"erstellt (admin/{TESTDATA_ADMIN_PASSWORD})" if result["admin"] else "existiert bereits"
    print(f"  Admin: {admin_status}")
    print(f"  Kategorien: {result['categories']}, Lagerorte: {result['locations']}, Items: {result['items']}")
    print("✅ Fertig!")


if __name__ == "__main__":
    main()
