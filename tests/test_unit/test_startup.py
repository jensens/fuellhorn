"""Tests: gemeinsame Startkonfiguration (Issue #375).

Läuft bewusst ohne ``main.py``: Das Prod-Image startet über das CLI, das vorher
weder Manifest noch Icons noch Favicon registrierte.
"""

from nicegui.client import Client
from pathlib import Path
import pytest
from starlette.routing import Route


class TestStaticAssets:
    def test_pwa_files_exist_in_package(self) -> None:
        from app.startup import FAVICON
        from app.startup import PWA_FILES
        from app.startup import STATIC_DIR

        assert (STATIC_DIR / "css" / "solarpunk-theme.css").is_file()
        assert (STATIC_DIR / "js" / "swipe-card.js").is_file()
        assert FAVICON.is_file()
        for local_file in PWA_FILES.values():
            assert local_file.is_file(), local_file

    def test_static_paths_are_package_relative(self) -> None:
        """Nicht vom Arbeitsverzeichnis abhängig (main.py nutzte das relative 'app/static')."""
        import app
        from app.startup import STATIC_DIR

        assert STATIC_DIR.is_absolute()
        assert STATIC_DIR.parent == Path(app.__file__).parent


class TestConfigureApp:
    def test_registers_static_mount_and_pwa_routes(self) -> None:
        from app.startup import PWA_FILES
        from app.startup import configure_app
        from nicegui import app as nicegui_app

        configure_app(nicegui_app)

        route_paths = {route.path for route in nicegui_app.routes if isinstance(route, Route)}
        assert set(PWA_FILES) <= route_paths
        # NiceGUI registriert Static-Verzeichnisse als GET-Route mit Pfad-Parameter
        assert "/static/{path:path}" in route_paths

    def test_shared_head_html_contains_pwa_tags_and_is_added_once(self) -> None:
        from app.startup import HEAD_HTML
        from app.startup import configure_app
        from nicegui import app as nicegui_app

        configure_app(nicegui_app)
        configure_app(nicegui_app)

        assert '<link rel="manifest" href="/manifest.json">' in HEAD_HTML
        assert '<script src="/static/js/swipe-card.js"></script>' in HEAD_HTML
        assert Client.shared_head_html.count(HEAD_HTML) == 1


class TestRunKwargs:
    def test_contains_title_favicon_host_and_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import app.config
        from app.startup import APP_TITLE
        from app.startup import FAVICON
        from app.startup import run_kwargs

        monkeypatch.setattr(app.config.config, "HOST", "127.0.0.1")
        monkeypatch.setattr(app.config.config, "PORT", 9123)

        kwargs = run_kwargs(reload=False)

        assert kwargs["title"] == APP_TITLE
        assert kwargs["favicon"] == str(FAVICON)
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 9123
        assert kwargs["reload"] is False
        assert kwargs["show"] is False

    def test_session_cookie_lifetime_comes_from_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issue #384: Cookie-Laufzeit = REMEMBER_ME_MAX_AGE statt Starlette-Default (14 Tage)."""
        import app.config
        from app.startup import run_kwargs

        monkeypatch.setattr(app.config.config, "REMEMBER_ME_MAX_AGE", 1234)

        assert run_kwargs()["session_middleware_kwargs"] == {"max_age": 1234}
