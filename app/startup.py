"""Gemeinsame Startkonfiguration für ``main.py`` (Entwicklung) und das ``fuellhorn``-CLI (Produktion).

Vorher registrierte nur ``main.py`` Manifest, Icons, Favicon und PWA-Meta-Tags; das
Prod-Image (CLI) lieferte keine installierbare PWA (Issue #375). Hier gibt es genau
eine Stelle mit paketrelativen Pfaden.
"""

from .config import config
from nicegui import ui
from nicegui.app import App
from nicegui.client import Client
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
    """Registriert Static-Dateien, PWA-Routen und den gemeinsamen Seitenkopf.

    Idempotent bezüglich des Seitenkopfs: NiceGUI hält ``shared_head_html`` als
    Klassenattribut, Tests laden ``main.py`` mehrfach im selben Prozess.
    """
    app.add_static_files("/static", str(STATIC_DIR))
    for url_path, local_file in PWA_FILES.items():
        app.add_static_file(url_path=url_path, local_file=str(local_file))
    if HEAD_HTML not in Client.shared_head_html:
        ui.add_head_html(HEAD_HTML, shared=True)


def run_kwargs(**overrides: Any) -> dict[str, Any]:
    """Gemeinsame Parameter für ``ui.run`` (Titel, Favicon, Host, Port)."""
    kwargs: dict[str, Any] = {
        "title": APP_TITLE,
        "favicon": str(FAVICON),
        "host": config.HOST,
        "port": config.PORT,
        "show": False,
    }
    kwargs.update(overrides)
    return kwargs
