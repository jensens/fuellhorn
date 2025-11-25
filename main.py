"""NiceGUI Application - Entry Point."""

from app.config import get_storage_secret
from app.database import create_db_and_tables

# Import pages to register routes
import app.ui.pages as _pages  # noqa: F401

# Import API routes to register endpoints (wird spaeter erstellt)
# import app.api.routes as _api_routes  # noqa: F401
from nicegui import ui


if __name__ in {"__main__", "__mp_main__"}:
    # Datenbank initialisieren
    create_db_and_tables()

    # NiceGUI starten
    ui.run(
        title="Füllhorn - Lebensmittelvorrats-Verwaltung",
        storage_secret=get_storage_secret(),
        reload=True,  # Auto-Reload waehrend Entwicklung
        show=False,  # Browser nicht automatisch oeffnen
    )
