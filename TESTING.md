# Testing Strategy für Fuellhorn

## Übersicht

Fuellhorn verwendet pytest für alle Tests. Tests sind in drei Kategorien eingeteilt:

1. **Unit Tests** - Testen einzelne Komponenten isoliert (Models, Services)
2. **Integration Tests** - Testen Zusammenspiel mehrerer Komponenten (Service + Datenbank)
3. **UI Tests** - Testen die Benutzeroberfläche mit NiceGUI Testing Framework

## Grundprinzipien

### 1. Test-Isolation ✅

**WICHTIG:** Tests dürfen **NIEMALS** die globale/Produktions-Datenbank berühren!

**✅ VON ANFANG AN RICHTIG!** Alle Tests verwenden automatisch isolierte In-Memory Datenbanken:

#### UI-Tests (NiceGUI)

**Komplett automatisch** durch `isolated_test_database` Fixture (in `tests/conftest.py`):

- **Scope:** function (eine frische DB pro Test!)
- **Autouse:** True (automatisch für alle Tests)
- **Engine:** In-Memory SQLite mit StaticPool
- **Patching:** `app.database.get_engine()` wird gepatcht
- **Isolation:** Jeder Test bekommt komplett neue Datenbank
- **Performance:** 10-100x schneller als File-basiert

```python
# Du musst NICHTS tun - schreibe Tests einfach normal!
async def test_login_page(user: User) -> None:
    await user.open("/login")  # Admin-User ist automatisch vorhanden!
    await user.should_see("Anmelden")
```

#### Unit-Tests

Verwenden die `session` Fixture für In-Memory SQLite:

```python
def test_create_item(session: Session) -> None:
    item = Item(
        product_name="Tomaten",
        item_type=ItemType.HOMEMADE_FROZEN,
        quantity=500,
        unit="g",
        location_id=1
    )
    session.add(item)
    session.commit()
    assert item.id is not None
```

**Warum ist das sicher?**

- **UI-Tests:** `isolated_test_database` patcht `get_engine()` → In-Memory
- **Unit-Tests:** `session` Fixture erstellt eigene In-Memory Engine
- **Produktions-DB:** Wird NIEMALS berührt (verifiziert durch `test_database_isolation.py`)
- **NiceGUI-Kompatibel:** Funktioniert mit `runpy.run_path('main.py')` durch Patching

### 2. Test-Fixtures

#### Session Fixture (Standard)

Jede Test-Datei sollte ihre eigene `session` Fixture haben:

```python
@pytest.fixture(name="session")
def session_fixture() -> Generator[Session]:
    """Erstellt In-Memory SQLite Session für Tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

#### User Fixtures

Für Tests die User benötigen:

```python
@pytest.fixture(name="test_admin")
def test_admin_fixture(session: Session) -> User:
    """Erstellt einen Admin Test-User."""
    user = User(
        username="admin",
        email="admin@example.com",
        is_active=True,
        role="admin",  # Nur ein String, nicht JSON-Array!
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Erstellt einen normalen Test-User."""
    user = User(
        username="testuser",
        email="user@example.com",
        is_active=True,
        role="user",
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

#### Item Fixtures

Für Tests die Items benötigen:

```python
@pytest.fixture(name="test_location")
def test_location_fixture(session: Session, test_admin: User) -> Location:
    """Erstellt einen Test-Lagerort."""
    location = Location(
        name="Tiefkühltruhe",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

@pytest.fixture(name="test_item")
def test_item_fixture(session: Session, test_admin: User, test_location: Location) -> Item:
    """Erstellt einen Test-Artikel."""
    item = Item(
        product_name="Tomaten",
        item_type=ItemType.HOMEMADE_FROZEN,
        quantity=500,
        unit="g",
        location_id=test_location.id,
        production_date=date.today(),
        created_by=test_admin.id,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
```

## Test-Typen

### Unit Tests (Models)

**Beispiel:** `tests/test_item_models.py`

```python
class TestItem:
    def test_create_item(self, session: Session, test_admin: User, test_location: Location) -> None:
        """Test: Item kann erstellt werden."""
        item = Item(
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=500,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            created_by=test_admin.id,
        )
        session.add(item)
        session.commit()

        assert item.id is not None
        assert item.product_name == "Tomaten"
```

### Unit Tests (Services)

**Beispiel:** `tests/test_item_service.py`

```python
class TestItemService:
    def test_create_item(self, session: Session, test_admin: User, test_location: Location) -> None:
        """Test: Item kann via Service erstellt werden."""
        item = item_service.create_item(
            session=session,
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=500,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            user_id=test_admin.id,
        )

        assert item is not None
        assert item.product_name == "Tomaten"
        assert not item.is_withdrawn
```

### Unit Tests (Expiry Calculator)

**Beispiel:** `tests/test_expiry_calculator.py`

```python
class TestExpiryCalculator:
    def test_purchased_fresh(self, session: Session) -> None:
        """Test: Haltbarkeit bei gekauften frischen Artikeln."""
        item = Item(
            product_name="Fleisch",
            item_type=ItemType.PURCHASED_FRESH,
            best_before_date=date(2025, 12, 31),
            quantity=1,
            unit="kg",
            location_id=1,
            created_by=1,
        )

        expiry_date = expiry_calculator.calculate_expiry_date(item)
        assert expiry_date == date(2025, 12, 31)

    def test_homemade_frozen(self, session: Session) -> None:
        """Test: Haltbarkeit bei selbst eingefrorenen Artikeln."""
        item = Item(
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            production_date=date(2025, 11, 1),
            quantity=500,
            unit="g",
            location_id=1,
            created_by=1,
        )

        # Annahme: Standard-Gefrierzeit 12 Monate
        expiry_date = expiry_calculator.calculate_expiry_date(item)
        assert expiry_date == date(2026, 11, 1)

    def test_expiry_status_critical(self) -> None:
        """Test: Status 'critical' bei < 3 Tage."""
        expiry_date = date.today() + timedelta(days=2)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "critical"

    def test_expiry_status_warning(self) -> None:
        """Test: Status 'warning' bei < 7 Tage."""
        expiry_date = date.today() + timedelta(days=5)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "warning"

    def test_expiry_status_ok(self) -> None:
        """Test: Status 'ok' bei >= 7 Tage."""
        expiry_date = date.today() + timedelta(days=10)
        status = expiry_calculator.get_expiry_status(expiry_date)
        assert status == "ok"
```

### Integration Tests

**Beispiel:** `tests/test_item_workflow.py`

Integration Tests testen das Zusammenspiel mehrerer Komponenten:

```python
class TestItemFullWorkflow:
    def test_complete_item_lifecycle(
        self, session: Session, test_admin: User, test_location: Location
    ) -> None:
        """Test: Kompletter Lifecycle eines Items."""
        # 1. Item erstellen
        item = item_service.create_item(
            session=session,
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=1000,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            user_id=test_admin.id,
        )
        assert item.quantity == 1000

        # 2. Teilentnahme
        item_service.withdraw_item(
            session=session,
            item_id=item.id,
            quantity=500,
            user_id=test_admin.id,
        )
        session.refresh(item)
        assert item.quantity == 500
        assert not item.is_withdrawn

        # 3. Vollständige Entnahme
        item_service.withdraw_item(
            session=session,
            item_id=item.id,
            quantity=500,
            user_id=test_admin.id,
        )
        session.refresh(item)
        assert item.quantity == 0
        assert item.is_withdrawn
        assert item.withdrawn_at is not None
```

### UI Tests (NiceGUI)

**Beispiel:** `tests/ui/test_login.py`

UI Tests verwenden das NiceGUI Testing Framework:

```python
# conftest.py
pytest_plugins = ["nicegui.testing.plugin"]

# test_login.py
from nicegui.testing import User

async def test_login_page(user: User) -> None:
    """Test: Login-Seite wird korrekt angezeigt."""
    await user.open("/login")
    await user.should_see("Füllhorn")
    await user.should_see("Anmelden")
    await user.should_see("Angemeldet bleiben")  # Remember-me checkbox

async def test_login_with_remember_me(user: User) -> None:
    """Test: Login mit 'Angemeldet bleiben'."""
    await user.open("/login")

    # Username eingeben
    await user.should_see("Benutzername")
    # ... Login-Flow testen
```

#### NiceGUI Testing Setup

**pytest-Konfiguration** in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
main_file = "main.py"  # ← WICHTIG! Registriert UI-Routen
```

**conftest.py Setup:**

```python
# Aktiviere NiceGUI Testing Plugin
pytest_plugins = ["nicegui.testing.plugin"]

# Isolated Test Database (von VellenBase übernommen)
@pytest.fixture(scope="function", autouse=True)
def isolated_test_database(monkeypatch):
    """Isolierte In-Memory Datenbank für jeden Test."""
    # Patcht get_engine() für In-Memory DB
    # Erstellt Admin-User automatisch
    pass

# Cleanup UI Packages (von VellenBase übernommen)
@pytest.fixture(scope="function", autouse=True)
def cleanup_ui_packages():
    """Entfernt UI Package Modules nach jedem Test."""
    # Ermöglicht korrekte Route Re-Registration
    pass
```

#### Test-Isolation - Lessons Learned von VellenBase ✅

**Datenbank-Isolation:** ✅ **VON ANFANG AN RICHTIG!**

- Jeder Test bekommt frische In-Memory Datenbank
- Produktions-DB wird NIEMALS berührt
- Performance: 10-100x schneller
- `isolated_test_database` Fixture von VellenBase übernommen

**Routing-Isolation:** ✅ **VON ANFANG AN RICHTIG!**

- `cleanup_ui_packages` Fixture von VellenBase übernommen
- Routes werden zwischen Tests korrekt re-registriert
- Keine 404-Fehler
- Parent packages werden aus sys.modules entfernt

**API Authentication:** ✅ **VON ANFANG AN BESSER!**

**Lesson Learned:** VellenBase hatte 6 geskippte API-Tests wegen AsyncClient + Session Storage Problem.

**Fuellhorn Lösung - Dependency Override Pattern:**

```python
# In conftest.py
from fastapi import Depends

@pytest.fixture
def override_api_auth(test_admin: User):
    """Override auth dependency für API tests."""
    from app.auth.dependencies import get_current_user

    async def mock_get_current_user():
        return test_admin

    # Override FastAPI dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()

# In test
from httpx import ASGITransport, AsyncClient

async def test_items_export_api(override_api_auth):
    """Test: Items Export API mit korrekter Auth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/items/export")
        assert response.status_code == 200
```

**Vorteil:** Keine geskippten Tests! API Authentication funktioniert von Anfang an.

## Mobile-First Testing

**Wichtig:** Fuellhorn ist mobile-first, daher:

### Viewport Testing

```python
async def test_mobile_viewport(user: User) -> None:
    """Test: Mobile Viewport wird korrekt gesetzt."""
    await user.open("/")
    # Prüfe dass viewport meta tag gesetzt ist
    # Prüfe dass Bottom Navigation sichtbar ist
```

### Touch-Target Testing

```python
async def test_button_touch_targets(user: User) -> None:
    """Test: Buttons haben mindestens 48x48px Klickfläche."""
    # Teste dass alle Buttons touch-optimiert sind
```

### Infinite Scroll Testing

```python
async def test_infinite_scroll(user: User) -> None:
    """Test: Infinite Scroll lädt weitere Items."""
    await user.open("/items")
    # Scrolle nach unten
    # Prüfe dass weitere Items geladen werden
```

## Test-Ausführung

### Alle Tests ausführen

```bash
uv run pytest
```

### Spezifische Test-Datei

```bash
uv run pytest tests/test_item_service.py -v
```

### Mit Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

### Nur UI Tests

```bash
uv run pytest tests/ui/ -v
```

### Nur Unit Tests (ohne UI)

```bash
uv run pytest tests/ --ignore=tests/ui/ -v
```

## Best Practices

### ✅ DO

1. **IMMER** eigene `session` Fixture erstellen
2. **IMMER** In-Memory SQLite für Tests nutzen
3. **IMMER** Session explizit in Service-Aufrufe injizieren
4. Tests klein und fokussiert halten (eine Assertion pro Test)
5. Sprechende Test-Namen verwenden (`test_create_item_with_valid_data`)
6. Docstrings für Tests schreiben
7. Test-Daten explizit im Test erstellen (nicht in Fixtures verstecken)
8. **Alle 5 Item-Typen** testen (purchased_fresh, purchased_frozen, purchased_then_frozen, homemade_frozen, homemade_preserved)
9. Expiry Calculator für alle Typen testen
10. Mobile-spezifische Features testen (Bottom Nav, Touch Targets)

### ❌ DON'T

1. **NIEMALS** die globale Datenbank in Tests verwenden
2. **NIEMALS** `get_session()` ohne explizite Test-Session verwenden
3. Nicht auf Reihenfolge der Tests verlassen
4. Nicht auf Test-Daten aus anderen Tests zugreifen
5. Nicht zu viele Assertions in einem Test
6. **NIEMALS** API Tests skippen (Dependency Override verwenden!)
7. Nicht Desktop-only testen (auch mobile Features!)

## Troubleshooting

### Fehler: "Database is locked"

**Problem:** Parallel laufende Tests greifen auf dieselbe Datenbankdatei zu.

**Lösung:** In-Memory SQLite verwenden (`sqlite://` statt `sqlite:///file.db`)

### Tests laufen sehr langsam

**Problem:** Tests verwenden möglicherweise echte Datenbank statt In-Memory.

**Lösung:**
1. In-Memory SQLite verwenden (`sqlite://`)
2. `StaticPool` für bessere Performance nutzen
3. Session-Injection korrekt durchführen

### 404 Fehler in UI Tests

**Problem:** Routes werden zwischen Tests nicht korrekt re-registriert.

**Lösung:** `cleanup_ui_packages` Fixture ist korrekt eingerichtet in conftest.py

### API Tests schlagen fehl (401 Unauthorized)

**Problem:** AsyncClient kann nicht auf NiceGUI Session Storage zugreifen.

**Lösung:** Dependency Override Pattern verwenden (siehe oben)

## Beispiel: Komplettes Test-File

```python
"""Tests für Item Service."""

from collections.abc import Generator
from datetime import date, timedelta

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from ..database import SQLModel
from ..models.user import User
from ..models.location import Location, LocationType
from ..models.item import Item, ItemType
from ..services import item_service


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session]:
    """Erstellt In-Memory SQLite Session für Tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_admin")
def test_admin_fixture(session: Session) -> User:
    """Erstellt Admin Test-User."""
    user = User(
        username="admin",
        email="admin@example.com",
        is_active=True,
        role="admin",
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_location")
def test_location_fixture(session: Session, test_admin: User) -> Location:
    """Erstellt Test-Lagerort."""
    location = Location(
        name="Tiefkühltruhe",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


class TestItemService:
    """Tests für Item Service."""

    def test_create_item(self, session: Session, test_admin: User, test_location: Location) -> None:
        """Test: Item kann erstellt werden."""
        item = item_service.create_item(
            session=session,
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=500,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            user_id=test_admin.id,
        )

        assert item is not None
        assert item.product_name == "Tomaten"
        assert item.item_type == ItemType.HOMEMADE_FROZEN
        assert item.quantity == 500
        assert not item.is_withdrawn

    def test_withdraw_item_partial(self, session: Session, test_admin: User, test_location: Location) -> None:
        """Test: Teilentnahme reduziert Menge."""
        # Create item
        item = item_service.create_item(
            session=session,
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=1000,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            user_id=test_admin.id,
        )

        # Partial withdrawal
        item_service.withdraw_item(
            session=session,
            item_id=item.id,
            quantity=300,
            user_id=test_admin.id,
        )

        session.refresh(item)
        assert item.quantity == 700
        assert not item.is_withdrawn

    def test_withdraw_item_complete(self, session: Session, test_admin: User, test_location: Location) -> None:
        """Test: Vollständige Entnahme markiert Item als entnommen."""
        # Create item
        item = item_service.create_item(
            session=session,
            product_name="Tomaten",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=500,
            unit="g",
            location_id=test_location.id,
            production_date=date.today(),
            user_id=test_admin.id,
        )

        # Complete withdrawal
        item_service.withdraw_item(
            session=session,
            item_id=item.id,
            quantity=500,
            user_id=test_admin.id,
        )

        session.refresh(item)
        assert item.quantity == 0
        assert item.is_withdrawn
        assert item.withdrawn_at is not None
        assert item.withdrawn_by == test_admin.id
```

## Referenzen

- [pytest Documentation](https://docs.pytest.org/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
- [NiceGUI Testing](https://nicegui.io/documentation/section_testing)
- VellenBase TESTING.md - Lessons Learned übernommen
- Projekt-Regeln: siehe [CLAUDE.md](CLAUDE.md)
