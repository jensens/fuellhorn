"""NiceGUI Application - Entry Point."""

import os

from app.config import get_storage_secret
from app.database import create_db_and_tables
from nicegui import app, ui

# Serve static files (CSS, icons, etc.)
app.add_static_files("/static", "app/static")


# Load Solarpunk theme CSS and JavaScript for each client connection
@app.on_connect
def _load_theme() -> None:
    ui.add_head_html('<link rel="stylesheet" href="/static/css/solarpunk-theme.css">')
    ui.add_head_html('<script src="/static/js/swipe-card.js"></script>')

    # PWA Meta-Tags
    ui.add_head_html('<link rel="manifest" href="/static/manifest.json">')
    ui.add_head_html('<meta name="theme-color" content="#4A7C59">')
    ui.add_head_html('<meta name="mobile-web-app-capable" content="yes">')

    # Apple-spezifische PWA Meta-Tags
    ui.add_head_html('<link rel="apple-touch-icon" href="/static/pwa/fuellhorn-icon-180.png">')
    ui.add_head_html('<meta name="apple-mobile-web-app-capable" content="yes">')
    ui.add_head_html(
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
    )
    ui.add_head_html('<meta name="apple-mobile-web-app-title" content="Fuellhorn">')


# Import pages to register routes
import app.ui.pages as _pages  # noqa: F401, E402

# Import test pages only during testing (for component tests)
if os.environ.get("TESTING") == "true":
    import app.ui.test_pages as _test_pages  # noqa: F401, E402

# Import API routes to register endpoints
import app.api.health as _api_health  # noqa: F401, E402


if __name__ in {"__main__", "__mp_main__"}:
    from nicegui import ui

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
