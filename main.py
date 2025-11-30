"""NiceGUI Application - Entry Point."""

from app.config import get_storage_secret
from app.database import create_db_and_tables

# Import pages to register routes
import app.ui.pages as _pages  # noqa: F401
import os


# Import test pages only during testing (for component tests)
if os.environ.get("TESTING") == "true":
    import app.ui.test_pages as _test_pages  # noqa: F401

# Import API routes to register endpoints
import app.api.health as _api_health  # noqa: F401
from nicegui import ui


if __name__ in {"__main__", "__mp_main__"}:
    # Datenbank initialisieren
    create_db_and_tables()

    # Port aus Environment (für parallele Entwicklung in Worktrees)
    port = int(os.environ.get("PORT", "8080"))

    # NiceGUI starten
    ui.run(
        title="Füllhorn - Lebensmittelvorrats-Verwaltung",
        storage_secret=get_storage_secret(),
        port=port,
        reload=True,  # Auto-Reload waehrend Entwicklung
        show=False,  # Browser nicht automatisch oeffnen
    )
