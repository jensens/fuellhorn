"""Konsistenztest: Jedes ``ui.navigate.to``-Ziel im UI muss eine registrierte Route sein (Issue #366).

Zwei Links führten ins 404 (``/add-item``, ``/items/{id}``), weil niemand die Ziele
gegen ``@ui.page`` prüfte. Dieser Test liest beide Seiten aus dem Quelltext, damit
er ohne laufende App auskommt und auch künftige Tippfehler fängt.
"""

from pathlib import Path
import re


APP_UI = Path(__file__).resolve().parents[2] / "app" / "ui"

ROUTE_PATTERN = re.compile(r"@ui\.page\(\s*[\"']([^\"']+)[\"']")
NAVIGATE_PATTERN = re.compile(r"navigate\.to\(\s*f?[\"']([^\"']+)[\"']")
PLACEHOLDER = re.compile(r"\{[^}]*\}")


def _registered_routes() -> set[str]:
    routes: set[str] = set()
    for source in (APP_UI / "pages").glob("*.py"):
        routes.update(ROUTE_PATTERN.findall(source.read_text(encoding="utf-8")))
    return routes


def _navigation_targets() -> dict[str, list[str]]:
    """Mapping Ziel-Pfad → Fundstellen (ohne Query-String, Platzhalter normalisiert)."""
    targets: dict[str, list[str]] = {}
    for source in APP_UI.rglob("*.py"):
        if "test_pages" in source.parts:
            continue
        for match in NAVIGATE_PATTERN.finditer(source.read_text(encoding="utf-8")):
            path = PLACEHOLDER.sub("{param}", match.group(1).split("?")[0])
            targets.setdefault(path, []).append(str(source.relative_to(APP_UI.parent.parent)))
    return targets


def _matches(target: str, route: str) -> bool:
    target_parts = target.strip("/").split("/")
    route_parts = route.strip("/").split("/")
    if len(target_parts) != len(route_parts):
        return False
    return all(r.startswith("{") or r == t for t, r in zip(target_parts, route_parts, strict=True))


def test_navigation_targets_are_registered_routes() -> None:
    """Alle statischen Navigationsziele zeigen auf existierende Seiten."""
    routes = _registered_routes()
    assert routes, "keine @ui.page-Routen gefunden"

    unresolved = {
        target: files for target, files in _navigation_targets().items() if not any(_matches(target, r) for r in routes)
    }
    assert unresolved == {}, f"Navigationsziele ohne Route: {unresolved}"


def test_route_matcher_handles_parameters() -> None:
    """Hilfsfunktion: Platzhalter im Ziel passen auf Platzhalter in der Route."""
    assert _matches("/items/{param}/edit", "/items/{item_id}/edit")
    assert not _matches("/items/{param}", "/items/{item_id}/edit")
