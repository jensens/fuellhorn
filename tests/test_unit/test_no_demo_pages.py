"""Tests: Demo-Seiten gehören nicht in die Produktions-Routen (Issue #374).

``/demo/chips`` und ``/demo/swipe`` waren ohne Auth in ``app.ui.pages`` registriert.
Die Swipe-Demo bleibt als Test-Seite erhalten (E2E-Tests nutzen sie), wird aber
wie alle Test-Seiten nur unter ``TESTING`` geladen.
"""

import pkgutil


def test_production_pages_contain_no_demo_modules() -> None:
    import app.ui.pages

    names = {module.name for module in pkgutil.iter_modules(app.ui.pages.__path__)}

    assert not {name for name in names if name.startswith("demo_")}


def test_swipe_demo_lives_in_test_pages() -> None:
    import app.ui.test_pages

    names = {module.name for module in pkgutil.iter_modules(app.ui.test_pages.__path__)}

    assert "test_swipe" in names
