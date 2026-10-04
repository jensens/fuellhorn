"""NiceGUI Application - Entry Point (Entwicklung, mit Auto-Reload).

Produktion startet über das ``fuellhorn``-CLI (``app/cli.py``). Beide nutzen
dieselbe Startkonfiguration aus ``app/startup.py`` (Issue #375).
"""

from app.cli import run_migrations
from app.startup import configure_app
from app.startup import run_kwargs
from nicegui import app
from nicegui import ui
import os


# Static-Dateien, PWA-Routen (Manifest, Icons) und gemeinsamer Seitenkopf
configure_app(app)

# Import pages to register routes
import app.ui.pages as _pages  # noqa: F401, E402


# Import test pages only during testing (for component tests)
if os.environ.get("TESTING") == "true":
    import app.ui.test_pages as _test_pages  # noqa: F401, E402

# Import API routes to register endpoints
import app.api.health as _api_health  # noqa: F401, E402


if __name__ in {"__main__", "__mp_main__"}:
    from app.config import config as app_config
    from app.config import get_storage_secret

    # Schema per Alembic anlegen/aktualisieren (wie in Produktion). create_all legte
    # Tabellen ohne alembic_version an, ein späteres 'alembic upgrade head' scheiterte (#376).
    # FUELLHORN_SKIP_MIGRATIONS wie im CLI (#377). Unter TESTING keine Migration: NiceGUIs
    # User-Fixture führt main.py als __main__ aus, sonst migriert jeder UI-Test die konfigurierte
    # Datenbank (lokal data/fuellhorn.db, in CI mit -n auto ein Wettlauf, #391).
    if not app_config.SKIP_MIGRATIONS and os.environ.get("TESTING") != "true":
        run_migrations()

    # NiceGUI starten (Titel, Favicon, HOST/PORT aus app.startup bzw. der Konfiguration)
    ui.run(
        storage_secret=get_storage_secret(),
        reload=True,  # Auto-Reload waehrend Entwicklung
        **run_kwargs(),
    )
