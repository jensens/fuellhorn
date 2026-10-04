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

### Parallele Ausführung mit pytest-xdist

Alle Suiten laufen parallel (`-n auto` nutzt alle CPU-Kerne):

```bash
# Alle außer E2E, parallel
uv run pytest -n auto

# Nur UI-Tests, parallel
uv run pytest tests/test_ui -n auto

# E2E parallel (automatisch auf 4 Worker gedeckelt, jeder startet einen Server)
uv run pytest tests/test_e2e --run-e2e -n auto
```

**Warum funktioniert das?**
- Jeder Testprozess bekommt einen eigenen NiceGUI-Storage (`NICEGUI_STORAGE_PATH` in `tests/conftest.py`, Issue #391)
- Separate in-memory SQLite-DB pro Testmodul, Rollback pro Test
- E2E: eigener Port (`_find_free_port()`) und Server-Prozess pro Worker, eigene Browser-Instanz pro Test

**CI** (`.github/workflows/tests.yaml`, pro Pull Request):

| Job | Inhalt |
|-----|--------|
| Unit & Service Tests | `tests/test_services`, `test_api`, `test_unit`, `test_auth`, `test_utils`, `test_migrations`, `test_pwa`, `test_config.py`, `test_database_isolation.py` mit `-n auto` |
| UI Tests | `tests/test_ui` mit `-n auto` |
| Migrations (PostgreSQL) | `tests/test_migrations` gegen einen PostgreSQL-Service-Container |
| E2E Tests | `tests/test_e2e --run-e2e -n auto` mit Playwright/Chromium |
| Coverage | kombiniert die Daten aus Unit/Service und UI (`coverage combine`), Schwelle `--fail-under=85`, Report im Job-Summary |

Die Coverage-Schwelle (Stand bei Einführung: 89 %) steigt schrittweise Richtung 90 % (Issue #205); sie gilt nur für den
kombinierten Report, nicht für Teil-Läufe.

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
