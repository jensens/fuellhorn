"""E2E Tests mit Playwright.

Diese Tests verwenden Playwright für echte Browser-Automatisierung.
Sie sind langsamer als die NiceGUI User Fixture Tests, können aber
komplexe Workflows testen die echtes Browser-Verhalten brauchen.

Verwendung:
    # Alle E2E Tests ausführen
    uv run pytest tests/test_e2e/

    # Mit sichtbarem Browser
    uv run pytest tests/test_e2e/ --headed

    # Mit Traces für Debugging
    uv run pytest tests/test_e2e/ --tracing on
"""
