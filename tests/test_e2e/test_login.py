"""E2E Tests für die Login-Seite mit Playwright.

Diese Tests prüfen die Login-Funktionalität im echten Browser:
- Login-Seite rendert korrekt
- Login mit gültigen Credentials
- Login mit ungültigen Credentials zeigt Fehler
"""

from playwright.sync_api import Page
from playwright.sync_api import expect


def test_login_page_renders_correctly(page: Page, live_server: str) -> None:
    """Test: Login-Seite rendert alle UI-Elemente korrekt."""
    page.goto(f"{live_server}/login")

    # Titel und Untertitel prüfen
    expect(page.get_by_text("Füllhorn")).to_be_visible()
    expect(page.get_by_text("Lebensmittelvorrats-Verwaltung")).to_be_visible()

    # Formular-Elemente prüfen
    expect(page.get_by_label("Benutzername")).to_be_visible()
    expect(page.get_by_label("Passwort")).to_be_visible()
    # Checkbox hat den vollen Text "Angemeldet bleiben (30 Tage)"
    expect(page.get_by_text("Angemeldet bleiben")).to_be_visible()
    expect(page.get_by_role("button", name="Anmelden")).to_be_visible()


def test_login_with_valid_credentials(page: Page, live_server: str) -> None:
    """Test: Login mit gültigen Credentials leitet zum Dashboard weiter."""
    page.goto(f"{live_server}/login")

    # Credentials eingeben (admin/admin wird von live_server Fixture erstellt)
    page.get_by_label("Benutzername").fill("admin")
    page.get_by_label("Passwort").fill("admin")

    # Login Button klicken
    page.get_by_role("button", name="Anmelden").click()

    # Warten auf Redirect zum Dashboard (mit Timeout)
    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)

    # Verifizieren dass wir auf dem Dashboard sind
    # (URL-Check ist der primäre Erfolgsindikator)
    assert "/dashboard" in page.url


def test_login_with_invalid_credentials(page: Page, live_server: str) -> None:
    """Test: Login mit ungültigen Credentials zeigt Fehlermeldung."""
    page.goto(f"{live_server}/login")

    # Ungültige Credentials eingeben
    page.get_by_label("Benutzername").fill("admin")
    page.get_by_label("Passwort").fill("wrong-password")

    # Login Button klicken
    page.get_by_role("button", name="Anmelden").click()

    # Fehler-Notification prüfen (Text aus auth_service.py)
    expect(page.get_by_text("Username oder Passwort falsch")).to_be_visible(timeout=5000)

    # URL sollte weiterhin /login sein (kein Redirect)
    assert "/login" in page.url
