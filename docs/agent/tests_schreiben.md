# Tests schreiben

## Grundregeln

1. **TDD ist Pflicht** - Erst Test (rot), dann Code (grün), dann Refactor
2. **Niemals Produktions-DB** - Fixtures erledigen die Isolation automatisch
3. **Kleine, fokussierte Tests** - Eine Assertion pro Test
4. **Sprechende Namen** - `test_withdraw_item_partial_reduces_quantity`

## Test-Ausführung

```bash
# Standard (alle außer E2E)
uv run pytest

# E2E Tests (separat, braucht Browser)
uv run pytest -m e2e --run-e2e

# Einzelne Datei
uv run pytest tests/test_services/test_item_service.py -v
```

## Fixtures

Definiert in `tests/conftest.py` - einfach als Parameter verwenden:

| Fixture | Verwendung |
|---------|------------|
| `session` | Unit-Tests mit Datenbank |
| `test_admin` | Admin-User für Unit-Tests |
| `test_user` | Normaler User für Unit-Tests |
| `logged_in_user` | UI-Tests (bereits eingeloggt) |
| `live_server` | E2E mit Playwright (in `test_e2e/conftest.py`) |

## NiceGUI vs Playwright

| | NiceGUI | Playwright |
|---|---------|------------|
| **Wann** | 90% der UI-Tests | Kritische Browser-Flows |
| **Speed** | ~100ms/Test | ~2-5s/Test |
| **Fixture** | `logged_in_user` | `live_server` |

**Faustregel:** Starte mit NiceGUI. Playwright nur wenn echter Browser nötig.

## Beispiele

### Unit-Test

```python
def test_withdraw_item_partial(session: Session, test_admin: User) -> None:
    """Teilentnahme reduziert Menge."""
    item = create_test_item(session, test_admin, quantity=1000)

    item_service.withdraw(session, item.id, quantity=300)

    session.refresh(item)
    assert item.quantity == 700
```

### UI-Test (NiceGUI)

```python
async def test_items_page_shows_items(logged_in_user: User) -> None:
    """Items-Seite zeigt vorhandene Artikel."""
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Vorrat")
```

### E2E-Test (Playwright)

```python
def test_login_flow(page: Page, live_server: str) -> None:
    """Login im echten Browser."""
    page.goto(f"{live_server}/login")
    page.get_by_label("Benutzername").fill("admin")
    page.get_by_label("Passwort").fill("admin")
    page.get_by_role("button", name="Anmelden").click()
    page.wait_for_url(f"{live_server}/dashboard")
```

## Do / Don't

### Do

- Fixtures aus `conftest.py` nutzen
- Docstring für jeden Test
- Vor Commit: `uv run ruff format && uv run ruff check --fix && uv run pytest`

### Don't

- Globale/Produktions-Datenbank in Tests
- Auf Test-Reihenfolge verlassen
- Zu viele Assertions in einem Test
- E2E für alles (nur kritische Flows)
