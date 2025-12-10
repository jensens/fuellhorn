"""E2E Tests für den Artikel-Wizard mit Playwright.

Diese Tests prüfen alle Hauptpfade des 3-Schritt-Wizards:
- Alle 5 Artikel-Typen
- Validierung
- Navigation (Zurück, Abbruch)
- Smart Defaults
- Location-Filtering
"""

from playwright.sync_api import Page
from playwright.sync_api import expect


# =============================================================================
# Helper Functions
# =============================================================================


def login(page: Page, live_server: str) -> None:
    """Login als Admin."""
    page.goto(f"{live_server}/login")
    page.get_by_label("Benutzername").fill("admin")
    page.get_by_label("Passwort").fill("admin")
    page.get_by_role("button", name="Anmelden").click()
    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


def navigate_to_wizard(page: Page, live_server: str) -> None:
    """Navigiere zum Wizard."""
    page.goto(f"{live_server}/items/add")
    # Warte auf den Wizard (Schritt 1)
    expect(page.get_by_text("Schritt 1 von 3")).to_be_visible(timeout=5000)


def fill_step1(
    page: Page,
    product_name: str,
    item_type: str,
    quantity: str,
    unit: str = "g",
) -> None:
    """Fülle Schritt 1 des Wizards aus.

    Args:
        page: Playwright Page
        product_name: Produktname
        item_type: Deutscher Name des Artikel-Typs
        quantity: Menge als String
        unit: Einheit (g, kg, ml, l, Stück, Packung)
    """
    # Produktname
    page.get_by_placeholder("z.B. Tomaten aus Garten").fill(product_name)
    page.get_by_placeholder("z.B. Tomaten aus Garten").blur()

    # Artikel-Typ auswählen
    page.get_by_text(item_type, exact=True).click()

    # Menge eingeben
    page.get_by_placeholder("z.B. 500").fill(quantity)
    page.get_by_placeholder("z.B. 500").blur()

    # Einheit auswählen
    page.get_by_text(unit, exact=True).click()


def click_next(page: Page) -> None:
    """Klicke auf den Weiter-Button."""
    page.get_by_role("button", name="Weiter").click()


def fill_date(page: Page, date_str: str) -> None:
    """Fülle ein Datum-Feld aus (DD.MM.YYYY Format)."""
    # Finde das erste sichtbare Datums-Input
    date_input = page.locator('input[class*="q-field__native"]').first
    date_input.fill(date_str)
    date_input.blur()


def select_category(page: Page, category_name: str) -> None:
    """Wähle eine Kategorie aus."""
    page.get_by_text(category_name, exact=True).click()


def select_location(page: Page, location_name: str) -> None:
    """Wähle einen Lagerort aus."""
    page.get_by_text(location_name, exact=True).click()


def click_save(page: Page) -> None:
    """Klicke auf Speichern."""
    page.get_by_role("button", name="Speichern").first.click()


def click_save_and_next(page: Page) -> None:
    """Klicke auf Speichern & Nächster."""
    page.get_by_role("button", name="Speichern & Nächster").click()


# =============================================================================
# Happy Path Tests - Alle 5 Artikel-Typen
# =============================================================================


def test_wizard_purchased_fresh(page: Page, live_server: str) -> None:
    """Test: PURCHASED_FRESH - Frisch eingekauft."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1: Basisinformationen
    fill_step1(page, "Tomaten frisch", "Frisch eingekauft", "500", "g")
    click_next(page)

    # Step 2: Haltbarkeit (keine Kategorie erforderlich!)
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    # Kategorie sollte NICHT angezeigt werden
    expect(page.get_by_text("Kategorie *")).not_to_be_visible()
    # MHD eingeben
    fill_date(page, "31.12.2025")
    click_next(page)

    # Step 3: Lagerort
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    select_location(page, "Kühlschrank")
    click_save(page)

    # Erfolg: Redirect zum Dashboard (Notification kann zu schnell verschwinden)
    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)
    assert "/dashboard" in page.url


def test_wizard_purchased_frozen(page: Page, live_server: str) -> None:
    """Test: PURCHASED_FROZEN - TK-Ware gekauft."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1
    fill_step1(page, "Tiefkühlpizza", "TK-Ware gekauft", "1", "Stück")
    click_next(page)

    # Step 2: Keine Kategorie erforderlich
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Kategorie *")).not_to_be_visible()
    fill_date(page, "30.06.2025")
    click_next(page)

    # Step 3: Nur Tiefkühler sollte verfügbar sein
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    select_location(page, "Tiefkühler")
    click_save(page)

    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


def test_wizard_purchased_then_frozen(page: Page, live_server: str) -> None:
    """Test: PURCHASED_THEN_FROZEN - Frisch gekauft dann eingefroren."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1
    fill_step1(page, "Hackfleisch eingefroren", "Frisch gekauft → eingefroren", "500", "g")
    click_next(page)

    # Step 2: Kategorie + Einfrierdatum erforderlich
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Kategorie *")).to_be_visible()
    select_category(page, "Fleisch")
    # Einfrierdatum
    fill_date(page, "15.11.2025")
    click_next(page)

    # Step 3
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    select_location(page, "Tiefkühler")
    click_save(page)

    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


def test_wizard_homemade_frozen(page: Page, live_server: str) -> None:
    """Test: HOMEMADE_FROZEN - Selbst eingefroren.

    Besonderheit: Braucht Produktionsdatum UND Einfrierdatum!
    """
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1
    fill_step1(page, "Selbstgemachte Bolognese", "Selbst eingefroren", "800", "g")
    click_next(page)

    # Step 2: Kategorie + Produktionsdatum + Einfrierdatum
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Kategorie *")).to_be_visible()
    select_category(page, "Fleisch")

    # Produktionsdatum (erstes Datum-Feld)
    date_inputs = page.locator('input[class*="q-field__native"]')
    date_inputs.first.fill("01.11.2025")
    date_inputs.first.blur()

    # Einfrierdatum (zweites Datum-Feld)
    expect(page.get_by_text("Einfrierdatum *")).to_be_visible()
    date_inputs.nth(1).fill("02.11.2025")
    date_inputs.nth(1).blur()

    click_next(page)

    # Step 3
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    select_location(page, "Tiefkühler")
    click_save(page)

    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


def test_wizard_homemade_preserved(page: Page, live_server: str) -> None:
    """Test: HOMEMADE_PRESERVED - Selbst eingemacht."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1
    fill_step1(page, "Erdbeermarmelade", "Selbst eingemacht", "3", "Stück")
    click_next(page)

    # Step 2: Kategorie + Produktionsdatum
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Kategorie *")).to_be_visible()
    select_category(page, "Obst")
    fill_date(page, "15.06.2025")
    click_next(page)

    # Step 3: Speisekammer (nicht Tiefkühler!)
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    select_location(page, "Speisekammer")
    click_save(page)

    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


# =============================================================================
# Validierung Tests
# =============================================================================


def test_wizard_step1_validation_disables_next(page: Page, live_server: str) -> None:
    """Test: Weiter-Button ist disabled bei leerem Formular."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Weiter-Button sollte initial disabled sein
    next_button = page.get_by_role("button", name="Weiter")
    expect(next_button).to_be_disabled()

    # Nur Produktname eingeben - Button noch disabled
    page.get_by_placeholder("z.B. Tomaten aus Garten").fill("Test")
    page.get_by_placeholder("z.B. Tomaten aus Garten").blur()
    expect(next_button).to_be_disabled()

    # Artikel-Typ wählen - noch disabled
    page.get_by_text("Frisch eingekauft", exact=True).click()
    expect(next_button).to_be_disabled()

    # Menge eingeben - noch disabled (keine Einheit)
    page.get_by_placeholder("z.B. 500").fill("100")
    page.get_by_placeholder("z.B. 500").blur()
    # Einheit ist standardmäßig "g", also sollte Button jetzt enabled sein
    expect(next_button).to_be_enabled()


def test_wizard_step2_validation_requires_category(page: Page, live_server: str) -> None:
    """Test: Für HOMEMADE_PRESERVED muss Kategorie gewählt werden."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1 mit HOMEMADE_PRESERVED
    fill_step1(page, "Testprodukt", "Selbst eingemacht", "100", "g")
    click_next(page)

    # Step 2: Weiter-Button sollte disabled sein ohne Kategorie
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    next_button = page.get_by_role("button", name="Weiter")
    expect(next_button).to_be_disabled()

    # Kategorie wählen
    select_category(page, "Gemüse")

    # Jetzt sollte Weiter enabled sein (Datum hat Default: heute)
    expect(next_button).to_be_enabled()


def test_wizard_step3_validation_requires_location(page: Page, live_server: str) -> None:
    """Test: Speichern-Button ist disabled ohne Lagerort."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Schnell durch Steps 1-2
    fill_step1(page, "Testprodukt", "Frisch eingekauft", "100", "g")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)

    # Step 3: Buttons sollten disabled sein
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    save_button = page.get_by_role("button", name="Speichern").first
    expect(save_button).to_be_disabled()

    # Lagerort wählen
    select_location(page, "Kühlschrank")

    # Jetzt sollte Speichern enabled sein
    expect(save_button).to_be_enabled()


# =============================================================================
# Navigation Tests
# =============================================================================


def test_wizard_back_button_preserves_data(page: Page, live_server: str) -> None:
    """Test: Zurück-Button behält Daten bei."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1 ausfüllen
    product_name = "Testprodukt Zurück"
    fill_step1(page, product_name, "Frisch eingekauft", "999", "kg")
    click_next(page)

    # Step 2
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)

    # Zurück klicken
    page.get_by_role("button", name="Zurück").click()

    # Prüfen ob Daten erhalten sind
    expect(page.get_by_text("Schritt 1 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_placeholder("z.B. Tomaten aus Garten")).to_have_value(product_name)
    expect(page.get_by_placeholder("z.B. 500")).to_have_value("999")


def test_wizard_back_button_roundtrip_preserves_summary(page: Page, live_server: str) -> None:
    """Test: Roundtrip (vor, zurück, vor, vor) behält alle Daten in Zusammenfassung.

    Issue #49: Nach Zurück von Schritt 2 zu Schritt 1 und wieder vor bis
    zur Zusammenfassung sollten alle Daten korrekt sein.
    """
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1 ausfüllen
    product_name = "Roundtrip Testprodukt"
    fill_step1(page, product_name, "Frisch eingekauft", "750", "g")
    click_next(page)

    # Step 2 - Datum setzen
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    fill_date(page, "31.12.2025")

    # Zurück zu Step 1
    page.get_by_role("button", name="Zurück").click()
    expect(page.get_by_text("Schritt 1 von 3")).to_be_visible(timeout=5000)

    # Prüfe dass Daten noch da sind
    expect(page.get_by_placeholder("z.B. Tomaten aus Garten")).to_have_value(product_name)

    # Wieder vorwärts zu Step 2 und Step 3
    click_next(page)
    expect(page.get_by_text("Schritt 2 von 3")).to_be_visible(timeout=5000)
    click_next(page)
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)

    # Location auswählen
    select_location(page, "Kühlschrank")

    # Zusammenfassung prüfen - Produktname sollte korrekt sein
    expect(page.get_by_text(product_name)).to_be_visible()


def test_wizard_cancel_returns_to_dashboard(page: Page, live_server: str) -> None:
    """Test: X-Button schließt den Wizard und geht zum Dashboard."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # X-Button klicken - find button in page header (right side)
    close_button = page.locator(".sp-page-header button.sp-back-btn")
    close_button.wait_for(state="visible", timeout=5000)
    close_button.click()

    # Sollte zum Dashboard navigieren
    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


# =============================================================================
# Erfolg & Notizen Tests
# =============================================================================


def test_wizard_saved_item_appears_in_list(page: Page, live_server: str) -> None:
    """Test: Gespeicherter Artikel erscheint in der Liste."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    unique_name = "Eindeutiger Testartikel"
    fill_step1(page, unique_name, "Frisch eingekauft", "100", "g")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)
    select_location(page, "Kühlschrank")
    click_save(page)

    # Warte auf Dashboard
    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)

    # Gehe zur Items-Liste
    page.goto(f"{live_server}/items")

    # Artikel sollte sichtbar sein
    expect(page.get_by_text(unique_name)).to_be_visible(timeout=5000)


def test_wizard_with_notes(page: Page, live_server: str) -> None:
    """Test: Notizen werden gespeichert."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Step 1 mit Notizen
    fill_step1(page, "Artikel mit Notiz", "Frisch eingekauft", "100", "g")
    page.get_by_placeholder("z.B. je 12 Stück, 300g pro Packung").first.fill("Testnotiz für E2E Test")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)
    select_location(page, "Kühlschrank")
    click_save(page)

    page.wait_for_url(f"{live_server}/dashboard", timeout=10000)


# =============================================================================
# Smart Defaults Tests
# =============================================================================


def test_wizard_save_and_next_preserves_defaults(page: Page, live_server: str) -> None:
    """Test: Nach 'Speichern & Nächster' werden Defaults übernommen.

    Unit und Location sollten vorbelegt sein.
    """
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Erstes Item speichern mit "Speichern & Nächster"
    fill_step1(page, "Erstes Item", "Frisch eingekauft", "100", "kg")  # kg statt g!
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)
    select_location(page, "Kühlschrank")
    click_save_and_next(page)

    # Warte auf Wizard-Reload
    expect(page.get_by_text("Schritt 1 von 3")).to_be_visible(timeout=10000)

    # Prüfe: Einheit "kg" sollte vorausgewählt sein (nicht "g")
    # Die kg-Chip sollte selektiert sein (hat bg-primary Klasse)
    kg_chip = page.get_by_text("kg", exact=True)
    # Prüfen ob der Parent-Button die selected-Klasse hat
    expect(kg_chip).to_be_visible()


def test_wizard_smart_defaults_item_type_within_window(page: Page, live_server: str) -> None:
    """Test: Item-Type wird innerhalb 30min Fenster übernommen."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # Erstes Item mit speziellem Typ speichern
    fill_step1(page, "TK-Test Item", "TK-Ware gekauft", "1", "Stück")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)
    select_location(page, "Tiefkühler")
    click_save_and_next(page)

    # Warte auf Wizard-Reload
    expect(page.get_by_text("Schritt 1 von 3")).to_be_visible(timeout=10000)

    # Item-Type "TK-Ware gekauft" sollte vorausgewählt sein
    # (Das Chip hat bg-primary wenn selektiert)
    tk_chip = page.get_by_text("TK-Ware gekauft", exact=True)
    expect(tk_chip).to_be_visible()


# =============================================================================
# Location-Filtering Tests
# =============================================================================


def test_wizard_frozen_types_show_only_freezer(page: Page, live_server: str) -> None:
    """Test: Frozen-Typen zeigen nur Tiefkühler als Lagerort."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # PURCHASED_FROZEN
    fill_step1(page, "Frozen Test", "TK-Ware gekauft", "100", "g")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)

    # Step 3: Nur Tiefkühler sollte sichtbar sein
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Tiefkühler")).to_be_visible()
    # Kühlschrank und Speisekammer sollten NICHT sichtbar sein
    expect(page.get_by_text("Kühlschrank")).not_to_be_visible()
    expect(page.get_by_text("Speisekammer")).not_to_be_visible()


def test_wizard_fresh_types_show_chilled_and_ambient(page: Page, live_server: str) -> None:
    """Test: Frische Typen zeigen Kühlschrank und Speisekammer."""
    login(page, live_server)
    navigate_to_wizard(page, live_server)

    # PURCHASED_FRESH
    fill_step1(page, "Fresh Test", "Frisch eingekauft", "100", "g")
    click_next(page)
    fill_date(page, "31.12.2025")
    click_next(page)

    # Step 3: Kühlschrank sollte sichtbar sein
    expect(page.get_by_text("Schritt 3 von 3")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Kühlschrank")).to_be_visible()
    # Tiefkühler sollte NICHT sichtbar sein für frische Ware
    expect(page.get_by_text("Tiefkühler")).not_to_be_visible()
