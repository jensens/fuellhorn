"""Gemeinsame Startkonfiguration für ``main.py`` (Entwicklung) und das ``fuellhorn``-CLI (Produktion).

Vorher registrierte nur ``main.py`` Manifest, Icons, Favicon und PWA-Meta-Tags; das
Prod-Image (CLI) lieferte keine installierbare PWA (Issue #375). Hier gibt es genau
eine Stelle mit paketrelativen Pfaden.
"""

from . import config as app_config
from nicegui import ui
from nicegui.app import App
from nicegui.client import Client
from nicegui.storage import Storage
from pathlib import Path
from typing import Any


STATIC_DIR = Path(__file__).parent / "static"
PWA_DIR = STATIC_DIR / "pwa"

APP_TITLE = "Füllhorn - Lebensmittelvorrats-Verwaltung"
FAVICON = PWA_DIR / "fuellhorn-icon-192.png"
THEME_COLOR = "#4A7C59"

# Root-URLs, die Browser für PWA-Installation erwarten -> Datei im Paket
PWA_FILES: dict[str, Path] = {
    "/manifest.json": STATIC_DIR / "manifest.json",
    "/icon-192.png": PWA_DIR / "fuellhorn-icon-192.png",
    "/icon-512.png": PWA_DIR / "fuellhorn-icon-512.png",
    "/apple-touch-icon.png": PWA_DIR / "fuellhorn-icon-180.png",
}

# Wird serverseitig in den <head> jeder Seite gerendert (shared), damit auch
# <script>-Tags ausgeführt werden; per on_connect nachgeschobenes HTML würde
# über insertAdjacentHTML eingefügt und Skripte darin nie ausgeführt.
HEAD_HTML = "\n".join(
    [
        '<link rel="stylesheet" href="/static/css/solarpunk-theme.css">',
        '<script src="/static/js/swipe-card.js"></script>',
        '<link rel="manifest" href="/manifest.json">',
        f'<meta name="theme-color" content="{THEME_COLOR}">',
        '<meta name="mobile-web-app-capable" content="yes">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
        '<meta name="apple-mobile-web-app-title" content="Fuellhorn">',
    ]
)


def configure_app(app: App) -> None:
    """Registriert Static-Dateien, PWA-Routen, Storage-Pfad und den gemeinsamen Seitenkopf.

    Idempotent bezüglich des Seitenkopfs: NiceGUI hält ``shared_head_html`` als
    Klassenattribut, Tests laden ``main.py`` mehrfach im selben Prozess.
    """
    # Sitzungsdateien ins Datenverzeichnis (Volume) statt ins Arbeitsverzeichnis (Issue #429).
    # NiceGUI liest den Pfad als Klassenattribut beim Anlegen jedes Benutzer-Storages.
    storage_path = app_config.config.STORAGE_PATH
    storage_path.mkdir(parents=True, exist_ok=True)
    Storage.path = storage_path
    app.add_static_files("/static", str(STATIC_DIR))
    for url_path, local_file in PWA_FILES.items():
        app.add_static_file(url_path=url_path, local_file=str(local_file))
    if HEAD_HTML not in Client.shared_head_html:
        ui.add_head_html(HEAD_HTML, shared=True)


def run_kwargs(**overrides: Any) -> dict[str, Any]:
    """Gemeinsame Parameter für ``ui.run`` (Titel, Favicon, Host, Port).

    Die Config-Instanz wird zur Laufzeit über das Modul aufgelöst, nicht beim
    Import gebunden: Tests laden ``app.config`` neu und patchen ``app.config.config``.
    """
    config = app_config.config
    kwargs: dict[str, Any] = {
        "title": APP_TITLE,
        "favicon": str(FAVICON),
        "host": config.HOST,
        "port": config.PORT,
        "show": False,
        # Laufzeit des signierten Sitzungs-Cookies (gleitend); ohne Remember-Me
        # endet die Sitzung früher über SESSION_MAX_AGE (app/auth/session.py, #384)
        "session_middleware_kwargs": {"max_age": config.REMEMBER_ME_MAX_AGE},
    }
    kwargs.update(overrides)
    return kwargs
