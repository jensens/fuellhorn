"""Standalone E2E Test Server.

Dieses Script wird als separater Prozess gestartet für E2E Tests.
Es bekommt den Port als Command-Line Argument.
"""

import os
from pathlib import Path
import sys


# Projekt-Root zum Python-Pfad hinzufügen
# (tests/test_e2e/_server.py -> Projekt-Root ist 3 Ebenen höher)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    """Starte den Test-Server."""
    if len(sys.argv) != 2:
        print("Usage: python _server.py <port>", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[1])

    # Setze Umgebungsvariablen für Test-Modus
    # WICHTIG: TESTING NICHT setzen, da sonst NiceGUI Test-Modus aktiviert wird
    # und NICEGUI_SCREEN_TEST_PORT erwartet
    os.environ["SECRET_KEY"] = "test-secret-key-for-e2e-tests"
    os.environ["FUELLHORN_SECRET"] = "test-fuellhorn-secret-for-e2e-tests"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # Entferne NiceGUI Test-Mode Variablen die von pytest geerbt werden könnten
    for var in list(os.environ.keys()):
        if var.startswith("NICEGUI_") or var == "TESTING":
            del os.environ[var]

    # Importiere die App erst hier damit Umgebungsvariablen wirken
    # HINWEIS: test_pages wird NICHT importiert da wir echte UI testen
    import app.api.health as _api_health  # noqa: F401
    from app.database import create_db_and_tables
    from app.database import get_session
    from app.models import Category
    from app.models import Location
    from app.models import User
    from app.models.location import LocationType
    import app.ui.pages as _pages  # noqa: F401
    from nicegui import app
    from nicegui import ui

    # Static files konfigurieren (wie in main.py)
    # Wichtig: Der Pfad muss relativ zum PROJECT_ROOT sein
    app.add_static_files("/static", str(PROJECT_ROOT / "app" / "static"))

    # Datenbank initialisieren (in-memory SQLite)
    create_db_and_tables()

    # Admin-User erstellen
    with next(get_session()) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
        )
        admin.set_password("admin")  # Einfaches Passwort für E2E Tests
        session.add(admin)
        session.commit()
        session.refresh(admin)

        # Kategorien für Wizard-Tests erstellen
        categories = [
            Category(name="Gemüse", color="#4CAF50", created_by=admin.id),
            Category(name="Obst", color="#FF9800", created_by=admin.id),
            Category(name="Fleisch", color="#F44336", created_by=admin.id),
        ]
        session.add_all(categories)

        # Lagerorte für Wizard-Tests erstellen (alle LocationTypes abdecken)
        locations = [
            Location(
                name="Kühlschrank",
                location_type=LocationType.CHILLED,
                color="#87CEEB",
                created_by=admin.id,
            ),
            Location(
                name="Tiefkühler",
                location_type=LocationType.FROZEN,
                color="#6495ED",
                created_by=admin.id,
            ),
            Location(
                name="Speisekammer",
                location_type=LocationType.AMBIENT,
                color="#DAA520",
                created_by=admin.id,
            ),
        ]
        session.add_all(locations)
        session.commit()

    # Server starten
    ui.run(
        host="127.0.0.1",
        port=port,
        title="Füllhorn - E2E Test",
        storage_secret="test-storage-secret",
        reload=False,
        show=False,
    )


if __name__ == "__main__":
    main()
