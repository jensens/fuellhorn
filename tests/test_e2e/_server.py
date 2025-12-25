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
    # Verwende temporäre Datei statt in-memory für bessere Stabilität
    import tempfile

    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"
    os.environ["_E2E_TEMP_DB"] = temp_db.name  # Für cleanup

    # Entferne NiceGUI Test-Mode Variablen die von pytest geerbt werden könnten
    for var in list(os.environ.keys()):
        if var.startswith("NICEGUI_") or var == "TESTING":
            del os.environ[var]

    # Importiere die App erst hier damit Umgebungsvariablen wirken
    import app.api.health as _api_health  # noqa: F401
    from app.database import create_db_and_tables
    from app.database import get_session

    # WICHTIG: Alle Models importieren damit create_db_and_tables() alle Tabellen erstellt
    from app.models import Category
    from app.models import Item  # noqa: F401 - needed for table creation
    from app.models import Location
    from app.models import LoginAttempt  # noqa: F401 - needed for table creation
    from app.models import User
    from app.models import Withdrawal  # noqa: F401 - needed for table creation
    from app.models.location import LocationType
    import app.ui.pages as _pages  # noqa: F401
    import app.ui.test_pages as _test_pages  # noqa: F401  # Test pages für E2E tests
    from nicegui import app
    from nicegui import ui

    # Static files konfigurieren (wie in main.py)
    # Wichtig: Der Pfad muss relativ zum PROJECT_ROOT sein
    app.add_static_files("/static", str(PROJECT_ROOT / "app" / "static"))

    # Datenbank initialisieren (in-memory SQLite)
    create_db_and_tables()

    # Admin-User erstellen
    # Pre-computed bcrypt hash für "admin" - vermeidet ~100-200ms bcrypt pro Test
    # Generiert mit: bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
    ADMIN_PASSWORD_HASH = "$2b$12$8wqw9nFQlSAdV3SPd9bLZuUzOtK2.YowC9dXnjNvkCkp/1iSQenke"

    with next(get_session()) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
            password_hash=ADMIN_PASSWORD_HASH,  # Pre-hashed für Performance
        )
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

    # ==========================================================================
    # ACHTUNG: Reset-Endpoint NUR für E2E Tests!
    # Dieser Endpoint existiert nur in _server.py (tests/test_e2e/_server.py)
    # und wird NIEMALS in der Produktions-App (main.py) registriert.
    # ==========================================================================
    from sqlalchemy import text

    def _reset_test_data() -> dict:
        """Reset database to initial seed state for test isolation."""
        from app.database import get_engine

        # Use engine directly to ensure same connection as table creation
        with get_engine().connect() as conn:
            # Delete with Raw SQL - use execute on connection directly
            conn.execute(text("DELETE FROM withdrawal"))
            conn.execute(text("DELETE FROM item"))
            conn.execute(text("DELETE FROM login_attempt"))
            conn.commit()
        return {"status": "reset", "message": "Test data cleared"}

    app.add_api_route("/api/test/reset", _reset_test_data, methods=["GET"])

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
