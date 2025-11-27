"""E2E Tests mit Playwright.

Diese Tests verwenden Playwright für echte Browser-Automatisierung.
Sie sind langsamer als die NiceGUI User Fixture Tests, können aber
komplexe Workflows testen die echtes Browser-Verhalten brauchen.

WICHTIG: E2E Tests müssen SEPARAT von den regulären Tests laufen!
         Sie starten echte Server-Prozesse und können mit dem
         NiceGUI Testing Plugin kollidieren.

Verwendung:
    # Reguläre Tests (ohne E2E)
    uv run pytest tests/ --ignore=tests/test_e2e/

    # E2E Tests separat ausführen
    uv run pytest tests/test_e2e/

    # Mit sichtbarem Browser
    uv run pytest tests/test_e2e/ --headed

    # Mit Traces für Debugging
    uv run pytest tests/test_e2e/ --tracing on
"""
