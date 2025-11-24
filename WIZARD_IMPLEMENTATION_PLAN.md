# Item Capture Wizard - Implementierungsplan

**Projekt:** Fuellhorn - Lebensmittelvorrats-Verwaltung
**Feature:** 3-Schritt-Wizard für schnelle Artikel-Erfassung (Mobile-First)
**Ansatz:** Test-Driven Development (TDD) mit vollständiger UI-Test-Coverage
**Datum:** 2025-11-24

---

## Übersicht

### Ziel
Implementierung eines mobil-optimierten 3-Schritt-Wizards zur schnellen Erfassung von 5-20 Artikeln nach dem Einkauf, mit Smart Defaults für Bulk-Capture-Workflow.

### TDD-Prinzipien
- **Jede Phase beginnt mit Tests** (rot → grün → refactor)
- **Vollständige UI-Test-Coverage** mit echten Browser-Tests (NiceGUI Testing)
- **Database Isolation** mit in-memory SQLite per Test
- **Commit nach jeder Phase** mit aussagekräftiger Message

### Phasen-Übersicht
1. **Phase 0:** UI Testing Infrastructure Setup (DB Isolation)
2. **Phase 1:** ItemType Enum Aktualisierung
3. **Phase 2:** Wizard Grundstruktur + Step 1 Basis
4. **Phase 3:** Step 1 Validation + Navigation
5. **Phase 4:** Step 2 - Conditional Date Fields
6. **Phase 5:** Step 3 - Location & Categories
7. **Phase 6:** Save Integration
8. **Phase 7:** "Speichern & Nächster" Flow
9. **Phase 8:** Smart Defaults (Browser Storage)
10. **Phase 9:** UI Polish & Mobile Optimization

---

## Phase 0: UI Testing Infrastructure Setup

**Ziel:** Sichere Test-Basis mit DB-Isolation für alle UI-Tests

### 0.1 Tests schreiben (ZUERST)

**Datei:** `tests/test_database_isolation.py`

```python
"""Verify that tests never touch production database."""

from app.database import get_engine
from sqlmodel import text
import pytest


def test_database_is_in_memory(isolated_test_database):
    """Verify that test database is in-memory SQLite."""
    engine = get_engine()

    # Check that it's SQLite
    assert "sqlite" in str(engine.url).lower()

    # Check that it's in-memory (no file path)
    assert str(engine.url) == "sqlite://"


def test_database_isolation_between_tests(isolated_test_database):
    """Verify each test gets a fresh database."""
    from app.models import User
    from sqlmodel import Session, select

    with Session(isolated_test_database) as session:
        # Count users (should only be test admin from fixture)
        statement = select(User)
        users = session.exec(statement).all()

        # Only the fixture-created admin should exist
        assert len(users) == 1
        assert users[0].username == "admin"


def test_production_db_not_loaded():
    """Verify that production database URL is not used."""
    engine = get_engine()

    # Should NOT be PostgreSQL (production)
    assert "postgresql" not in str(engine.url).lower()

    # Should NOT point to any file
    assert "file:" not in str(engine.url).lower()
    assert ".db" not in str(engine.url).lower()
```

**Tests laufen:** `uv run pytest tests/test_database_isolation.py` → **müssen fehlschlagen** (Fixtures fehlen)

### 0.2 conftest.py erweitern

**Datei:** `tests/conftest.py`

Hinzufügen:

```python
# ============================================================================
# NiceGUI Testing Plugin
# ============================================================================

pytest_plugins = ["nicegui.testing.plugin"]


# ============================================================================
# Database Isolation for UI Tests
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def isolated_test_database(monkeypatch):
    """Isolated In-Memory database for every UI test.

    This fixture ensures that:
    1. Each test gets a fresh, empty in-memory SQLite database
    2. Production database is NEVER touched
    3. Test admin user is automatically created
    4. Tests run 10-100x faster than file-based DBs

    How it works:
    - Patches app.database.get_engine() before NiceGUI starts
    - Creates in-memory engine with StaticPool
    - Creates all tables from SQLModel metadata
    - Creates admin test user for authentication

    Scope: function (fresh DB per test)
    Autouse: True (applies to ALL tests, including UI tests)
    """
    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, SQLModel, create_engine
    from app.models import User

    # Create in-memory test engine
    test_engine = create_engine(
        "sqlite://",  # In-memory SQLite
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Reuse connection across threads
    )

    # Patch get_engine() to return test engine
    monkeypatch.setattr("app.database.get_engine", lambda: test_engine)

    # Also reset the global _engine variable
    monkeypatch.setattr("app.database._engine", test_engine)

    # Create all tables
    SQLModel.metadata.create_all(test_engine)

    # Create test admin user (required for UI tests)
    with Session(test_engine) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
        )
        admin.set_password("password123")
        session.add(admin)
        session.commit()

    yield test_engine

    # Cleanup: Drop all tables
    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()


# ============================================================================
# UI Package Cleanup (Route Re-registration)
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_ui_packages():
    """Remove UI package modules after each test.

    This fixture ensures that:
    1. Routes are correctly re-registered between tests
    2. No 404 errors due to stale route registrations
    3. Parent packages are properly cleaned up

    Why this is needed:
    - NiceGUI uses runpy.run_path() to load main.py
    - Routes are registered globally in NiceGUI
    - Without cleanup, routes from previous tests persist
    - This causes conflicts and 404 errors

    Solution:
    - Remove app.ui.* modules from sys.modules
    - Forces Python to re-import and re-register routes

    Scope: function (cleanup after each test)
    Autouse: True (applies to ALL tests)
    """
    import sys

    yield  # Run test first

    # Cleanup after test
    modules_to_remove = [
        key for key in sys.modules.keys()
        if key.startswith("app.ui")
    ]

    for module in modules_to_remove:
        del sys.modules[module]
```

### 0.3 Erste UI Tests schreiben

**Datei:** `tests/test_ui/test_login.py`

```python
"""UI Tests for Login functionality."""

from nicegui.testing import User
import pytest


async def test_login_page_renders(user: User) -> None:
    """Test that login page renders correctly."""
    await user.open("/login")

    # Check page elements
    await user.should_see("Fuellhorn")
    await user.should_see("Lebensmittelvorrats-Verwaltung")
    await user.should_see("Benutzername")
    await user.should_see("Passwort")
    await user.should_see("Anmelden")


async def test_successful_login(user: User) -> None:
    """Test successful login flow."""
    await user.open("/login")

    # Fill login form
    # Note: admin user is automatically created by isolated_test_database fixture
    await user.fill("Benutzername", "admin")
    await user.fill("Passwort", "password123")

    # Click login button
    await user.click("Anmelden")

    # Should redirect to dashboard
    await user.should_see("Übersicht")
```

### 0.4 Tests validieren

```bash
uv run pytest tests/test_database_isolation.py -v
uv run pytest tests/test_ui/test_login.py -v
uv run mypy tests/
uv run ruff check tests/
```

**Alle Tests → grün ✅**

### 0.5 Commit

```bash
git add tests/conftest.py tests/test_database_isolation.py tests/test_ui/test_login.py
git commit -m "test: setup UI testing infrastructure with database isolation

- Add isolated_test_database fixture with in-memory SQLite
- Add cleanup_ui_packages fixture for route re-registration
- Add database isolation verification tests
- Add first UI test for login page
- Enable NiceGUI testing plugin

This ensures:
- Production database is NEVER touched
- Each test gets fresh database
- 10-100x faster tests with in-memory SQLite
- No route conflicts between tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Phase 1: ItemType Enum aktualisieren

**Ziel:** ItemType Enum auf UI_KONZEPT.md Werte aktualisieren

### 1.1 Tests aktualisieren (ZUERST)

**Dateien:** Alle `tests/test_services/*.py` mit ItemType-Referenzen

Ändern:
- `ItemType.TINNED` → `ItemType.PURCHASED_FRESH`
- `ItemType.JARRED` → `ItemType.HOMEMADE_PRESERVED`
- `ItemType.FROZEN` → `ItemType.PURCHASED_FROZEN` (oder passende Alternative)
- `ItemType.CHILLED` → `ItemType.PURCHASED_FRESH`
- `ItemType.AMBIENT` → `ItemType.PURCHASED_FRESH`

**Tests laufen:** `uv run pytest tests/test_services/` → **müssen fehlschlagen**

### 1.2 ItemType Enum implementieren

**Datei:** `app/models/freeze_time_config.py`

```python
class ItemType(str, Enum):
    """Item type for expiry calculation."""

    PURCHASED_FRESH = "purchased_fresh"              # Frisch eingekauft
    PURCHASED_FROZEN = "purchased_frozen"            # TK-Ware gekauft
    PURCHASED_THEN_FROZEN = "purchased_then_frozen"  # Frisch gekauft → eingefroren
    HOMEMADE_FROZEN = "homemade_frozen"              # Selbst eingefroren (Ernte/Reste)
    HOMEMADE_PRESERVED = "homemade_preserved"        # Selbst eingemacht
```

### 1.3 Alembic Migration

```bash
uv run alembic revision --autogenerate -m "update ItemType enum to match UI_KONZEPT"
# Migration prüfen
uv run alembic upgrade head
```

### 1.4 Tests validieren

```bash
uv run pytest tests/test_services/ -v
uv run mypy app/models/
uv run ruff check app/models/
```

**Alle Tests → grün ✅**

### 1.5 Commit

```bash
git add app/models/freeze_time_config.py tests/test_services/ alembic/versions/
git commit -m "refactor: update ItemType enum to match UI_KONZEPT.md

Changed from generic types (TINNED, JARRED, etc.) to specific
use-case types that reflect actual user workflow:
- PURCHASED_FRESH: Frisch eingekauft
- PURCHASED_FROZEN: TK-Ware gekauft
- PURCHASED_THEN_FROZEN: Frisch gekauft → eingefroren
- HOMEMADE_FROZEN: Selbst eingefroren
- HOMEMADE_PRESERVED: Selbst eingemacht

Updated all service tests to use new enum values.
Added Alembic migration for database schema update.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Phase 2: Wizard Grundstruktur + Step 1 Basis

**Ziel:** Wizard-Seite mit Step 1 Feldern (ohne Validation)

### 2.1 UI Tests schreiben (ZUERST)

**Datei:** `tests/test_ui/test_item_wizard_step1.py`

```python
"""UI Tests for Item Capture Wizard - Step 1."""

from nicegui.testing import User
import pytest


@pytest.fixture
async def logged_in_user(user: User) -> User:
    """Fixture that provides a logged-in user."""
    await user.open("/login")
    await user.fill("Benutzername", "admin")
    await user.fill("Passwort", "password123")
    await user.click("Anmelden")
    await user.should_see("Übersicht")
    return user


async def test_wizard_route_requires_auth(user: User) -> None:
    """Test that /items/add requires authentication."""
    await user.open("/items/add")
    # Should redirect to login
    await user.should_see("Benutzername")


async def test_wizard_step1_renders(logged_in_user: User) -> None:
    """Test that Step 1 of wizard renders correctly."""
    user = logged_in_user
    await user.open("/items/add")

    # Check page header
    await user.should_see("Artikel erfassen")

    # Check progress indicator
    await user.should_see("1 von 3")

    # Check Step 1 fields
    await user.should_see("Produktname")
    await user.should_see("Artikel-Typ")
    await user.should_see("Menge")
    await user.should_see("Einheit")


async def test_step1_has_product_name_input(logged_in_user: User) -> None:
    """Test that product name input exists."""
    user = logged_in_user
    await user.open("/items/add")

    # Try to type in product name field
    # NiceGUI testing: Adjust selector based on implementation
    await user.fill("Produktname", "Testprodukt")


async def test_step1_has_item_type_radios(logged_in_user: User) -> None:
    """Test that 5 item type radio buttons exist."""
    user = logged_in_user
    await user.open("/items/add")

    # Check all 5 item types are present
    await user.should_see("Frisch eingekauft")
    await user.should_see("TK-Ware gekauft")
    await user.should_see("Frisch gekauft → eingefroren")
    await user.should_see("Selbst eingefroren")
    await user.should_see("Selbst eingemacht")


async def test_step1_has_next_button(logged_in_user: User) -> None:
    """Test that Next button exists."""
    user = logged_in_user
    await user.open("/items/add")

    await user.should_see("Weiter")
```

**Tests laufen:** `uv run pytest tests/test_ui/test_item_wizard_step1.py -v` → **müssen fehlschlagen**

### 2.2 Wizard-Seite erstellen

**Datei:** `app/ui/pages/add_item.py`

```python
"""Item Capture Wizard - 3-Step Mobile-First Form."""

from ...auth import require_auth
from ...models.freeze_time_config import ItemType
from ..components import create_bottom_nav
from ..components import create_mobile_page_container
from nicegui import app
from nicegui import ui


@ui.page("/items/add")
@require_auth
def add_item() -> None:
    """3-Schritt-Wizard für schnelle Artikel-Erfassung."""

    # Header with title and close button
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        ui.label("Artikel erfassen").classes("text-h5 font-bold text-primary")
        ui.button(icon="close", on_click=lambda: ui.navigate.to("/dashboard")).props(
            "flat round color=gray-7"
        )

    # Main content
    with create_mobile_page_container():
        # Progress Indicator
        ui.label("Schritt 1 von 3").classes("text-sm text-gray-600 mb-4")

        # Step 1: Basic Information
        ui.label("Basisinformationen").classes("text-h6 font-semibold mb-3")

        # Product Name
        ui.label("Produktname *").classes("text-sm font-medium mb-1")
        product_name_input = ui.input(placeholder="z.B. Tomaten aus Garten").classes(
            "w-full"
        ).props("outlined autofocus")

        # Item Type
        ui.label("Artikel-Typ *").classes("text-sm font-medium mb-2 mt-4")
        item_type_group = ui.radio(
            options={
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
                ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
                ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
            },
            value=None,
        ).classes("w-full").props("size=lg")  # 48x48px touch targets

        # Quantity
        ui.label("Menge *").classes("text-sm font-medium mb-1 mt-4")
        quantity_input = ui.number(
            placeholder="0",
            min=0,
            step=1,
        ).classes("w-full").props("outlined")

        # Unit
        ui.label("Einheit *").classes("text-sm font-medium mb-1 mt-4")
        unit_select = ui.select(
            options=["g", "kg", "ml", "L", "Stück", "Packung"],
            value="g",
        ).classes("w-full").props("outlined")

        # Navigation
        with ui.row().classes("w-full justify-end mt-6 gap-2"):
            ui.button("Weiter", icon="arrow_forward").props(
                "color=primary size=lg disabled"
            ).style("min-height: 48px")

    # Bottom Navigation
    create_bottom_nav(current_page="add")
```

### 2.3 Page registrieren

**Datei:** `app/ui/pages/__init__.py`

```python
from . import add_item
from . import dashboard
from . import login
```

### 2.4 Tests validieren

```bash
uv run pytest tests/test_ui/test_item_wizard_step1.py -v
uv run mypy app/ui/pages/add_item.py
uv run ruff check app/ui/pages/add_item.py
```

**Alle Tests → grün ✅**

### 2.5 Commit

```bash
git add app/ui/pages/add_item.py app/ui/pages/__init__.py tests/test_ui/test_item_wizard_step1.py
git commit -m "feat: add item capture wizard - step 1 basic structure

Implemented mobile-first 3-step wizard for quick item capture:
- Route /items/add with authentication
- Progress indicator (1 von 3)
- Step 1 fields: product name, item type, quantity, unit
- 5 item type radio buttons with 48x48px touch targets
- Bottom navigation integration
- Full UI test coverage with NiceGUI testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Phase 3: Step 1 Validation + Navigation

**Ziel:** Validation für Step 1 Felder + Navigation zu Step 2

### 3.1 UI Tests schreiben (ZUERST)

**Datei:** `tests/test_ui/test_item_wizard_step1.py` (erweitern)

```python
async def test_product_name_too_short_shows_error(logged_in_user: User) -> None:
    """Test validation: product name < 2 characters."""
    user = logged_in_user
    await user.open("/items/add")

    await user.fill("Produktname", "A")
    # Blur field or trigger validation
    # Check error message appears
    await user.should_see("Mindestens 2 Zeichen")


async def test_quantity_zero_shows_error(logged_in_user: User) -> None:
    """Test validation: quantity = 0."""
    user = logged_in_user
    await user.open("/items/add")

    await user.fill("Menge", "0")
    await user.should_see("Menge muss größer als 0 sein")


async def test_all_fields_valid_enables_next(logged_in_user: User) -> None:
    """Test that Next button is enabled when all fields are valid."""
    user = logged_in_user
    await user.open("/items/add")

    # Fill all fields correctly
    await user.fill("Produktname", "Erbsen")
    await user.click("Selbst eingefroren")
    await user.fill("Menge", "500")
    # Unit is pre-selected with "g"

    # Next button should be enabled
    # Click it
    await user.click("Weiter")

    # Should show Step 2
    await user.should_see("2 von 3")


async def test_step2_shows_summary_from_step1(logged_in_user: User) -> None:
    """Test that Step 2 shows summary of Step 1 data."""
    user = logged_in_user
    await user.open("/items/add")

    # Complete Step 1
    await user.fill("Produktname", "Tomaten")
    await user.click("Frisch eingekauft")
    await user.fill("Menge", "1000")
    await user.click("Weiter")

    # Step 2 should show summary
    await user.should_see("Tomaten")
    await user.should_see("1000 g")
    await user.should_see("Frisch eingekauft")
```

**Tests laufen:** → **müssen fehlschlagen**

### 3.2 Validation implementieren

Erweitere `app/ui/pages/add_item.py`:

```python
from typing import Any


# Form state
form_data: dict[str, Any] = {
    "product_name": "",
    "item_type": None,
    "quantity": 0.0,
    "unit": "g",
}

validation_errors: dict[str, str] = {}


def validate_product_name(name: str) -> str | None:
    """Validate product name."""
    if len(name) < 2:
        return "Mindestens 2 Zeichen erforderlich"
    return None


def validate_quantity(qty: float) -> str | None:
    """Validate quantity."""
    if qty <= 0:
        return "Menge muss größer als 0 sein"
    return None


def validate_step1() -> bool:
    """Validate Step 1 fields. Returns True if all valid."""
    global validation_errors
    validation_errors.clear()

    # Product name
    if error := validate_product_name(form_data["product_name"]):
        validation_errors["product_name"] = error

    # Item type
    if form_data["item_type"] is None:
        validation_errors["item_type"] = "Bitte Artikel-Typ auswählen"

    # Quantity
    if error := validate_quantity(form_data["quantity"]):
        validation_errors["quantity"] = error

    # Unit (always valid from select)

    return len(validation_errors) == 0


def show_step2() -> None:
    """Show Step 2 after Step 1 validation."""
    if not validate_step1():
        ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
        return

    # Clear screen and show Step 2
    # (Implementation depends on how you want to structure the UI)
    # For now, simple notification
    ui.notify("Step 2 wird angezeigt", type="info")


# In add_item() function, update fields:

product_name_input = ui.input(placeholder="z.B. Tomaten").classes("w-full").props("outlined autofocus")
product_name_input.bind_value(form_data, "product_name")
product_name_input.on("change", lambda: validate_step1())

# Error message
product_name_error = ui.label("").classes("text-xs text-red-500 mt-1")
product_name_error.bind_text_from(validation_errors, "product_name", backward=lambda x: x or "")

# Similar for other fields...

# Next button
next_button = ui.button("Weiter", icon="arrow_forward").props("color=primary size=lg")
next_button.on("click", show_step2)

# Enable/disable based on validation
def update_next_button() -> None:
    next_button.props(f"{'disabled' if not validate_step1() else ''}")

product_name_input.on("change", update_next_button)
item_type_group.on("change", update_next_button)
quantity_input.on("change", update_next_button)
```

### 3.3 Tests validieren

```bash
uv run pytest tests/test_ui/test_item_wizard_step1.py -v
uv run mypy app/ui/pages/add_item.py
uv run ruff check app/ui/pages/add_item.py
```

**Alle Tests → grün ✅**

### 3.4 Commit

```bash
git add app/ui/pages/add_item.py tests/test_ui/test_item_wizard_step1.py
git commit -m "feat: add validation and navigation for wizard step 1

- Implemented field validation with inline error messages
- Product name: minimum 2 characters
- Quantity: must be > 0
- Item type: required selection
- Next button enabled only when all fields valid
- Navigation to Step 2 after successful validation
- Full UI test coverage for validation logic

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Phase 4: Step 2 - Conditional Date Fields

**Ziel:** Datumsfelder in Step 2 mit bedingter Logik basierend auf ItemType

### 4.1 Validation Logic erweitern

**Datei:** `app/ui/validation/wizard_validation.py`

```python
from datetime import date


def validate_best_before_date(best_before: date | None) -> str | None:
    """Validate best before date."""
    if best_before is None:
        return "Datum erforderlich"
    # Could add future date validation if needed
    return None


def validate_freeze_date(
    freeze_date: date | None,
    item_type: Any,
    best_before: date | None,
) -> str | None:
    """Validate freeze date for frozen items."""
    from ...models.freeze_time_config import ItemType

    frozen_types = {
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    }

    if item_type in frozen_types:
        if freeze_date is None:
            return "Einfrierdatum erforderlich für TK-Artikel"
        # Freeze date should not be before best_before
        if best_before and freeze_date < best_before:
            return "Einfrierdatum kann nicht vor Produktionsdatum liegen"

    return None


def validate_step2(
    item_type: Any,
    best_before: date | None,
    freeze_date: date | None,
) -> dict[str, str]:
    """Validate all Step 2 fields."""
    errors: dict[str, str] = {}

    if error := validate_best_before_date(best_before):
        errors["best_before"] = error

    if error := validate_freeze_date(freeze_date, item_type, best_before):
        errors["freeze_date"] = error

    return errors
```

### 4.2 Unit Tests für Step 2 Validation

**Datei:** `tests/test_ui/test_wizard_validation.py` (erweitern)

```python
from datetime import date, timedelta


def test_validate_best_before_date_valid() -> None:
    """Test valid best before dates."""
    assert validate_best_before_date(date.today()) is None
    assert validate_best_before_date(date.today() + timedelta(days=30)) is None


def test_validate_best_before_date_none() -> None:
    """Test best before date is None."""
    assert validate_best_before_date(None) == "Datum erforderlich"


def test_validate_freeze_date_required_for_frozen() -> None:
    """Test freeze date required for frozen types."""
    error = validate_freeze_date(None, ItemType.PURCHASED_FROZEN, date.today())
    assert error == "Einfrierdatum erforderlich für TK-Artikel"


def test_validate_freeze_date_not_required_for_fresh() -> None:
    """Test freeze date not required for fresh types."""
    error = validate_freeze_date(None, ItemType.PURCHASED_FRESH, date.today())
    assert error is None


def test_validate_freeze_date_cannot_be_before_best_before() -> None:
    """Test freeze date validation against best_before."""
    best_before = date(2024, 1, 1)
    freeze_date_val = date(2023, 12, 1)  # Before best_before

    error = validate_freeze_date(
        freeze_date_val, ItemType.PURCHASED_THEN_FROZEN, best_before
    )
    assert "vor Produktionsdatum" in error
```

### 4.3 Step 2 UI implementieren

**Datei:** `app/ui/pages/add_item.py` - `show_step2()` erweitern

```python
from datetime import date as date_type

def show_step2() -> None:
    """Navigate to Step 2."""
    # ... validation check ...

    form_data["current_step"] = 2
    content_container.clear()
    with content_container:
        # Progress Indicator
        ui.label("Schritt 2 von 3").classes("text-sm text-gray-600 mb-4")

        # Step 2: Date Information
        ui.label("Datumsangaben").classes("text-h6 font-semibold mb-3")

        # Summary from Step 1
        with ui.card().classes("w-full bg-gray-50 p-3 mb-4"):
            ui.label("Zusammenfassung:").classes("text-sm font-medium mb-2")
            item_type_labels = {
                ItemType.PURCHASED_FRESH: "Frisch eingekauft",
                ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
                # ... all types
            }
            type_label = item_type_labels.get(form_data["item_type"], "")
            ui.label(
                f"{form_data['product_name']} • {form_data['quantity']} {form_data['unit']} • {type_label}"
            ).classes("text-sm")

        # Best Before / Production Date (always shown)
        date_label = "Produktionsdatum" if form_data["item_type"] in {
            ItemType.HOMEMADE_FROZEN, ItemType.HOMEMADE_PRESERVED
        } else "Einkaufsdatum"

        ui.label(f"{date_label} *").classes("text-sm font-medium mb-1")
        best_before_input = ui.date(value=date_type.today()).classes("w-full")
        best_before_input.bind_value(form_data, "best_before_date")
        best_before_input.on("update:model-value", update_step2_validation)

        # Freeze Date (conditional - only for frozen types)
        frozen_types = {
            ItemType.PURCHASED_FROZEN,
            ItemType.PURCHASED_THEN_FROZEN,
            ItemType.HOMEMADE_FROZEN,
        }

        if form_data["item_type"] in frozen_types:
            ui.label("Einfrierdatum *").classes("text-sm font-medium mb-1 mt-4")
            freeze_date_input = ui.date(value=date_type.today()).classes("w-full")
            freeze_date_input.bind_value(form_data, "freeze_date")
            freeze_date_input.on("update:model-value", update_step2_validation)

        # Notes (optional)
        ui.label("Notizen (optional)").classes("text-sm font-medium mb-1 mt-4")
        notes_input = ui.textarea(placeholder="z.B. blanchiert").classes("w-full")
        notes_input.bind_value(form_data, "notes")

        # Navigation
        with ui.row().classes("w-full justify-between mt-6 gap-2"):
            ui.button("Zurück", icon="arrow_back", on_click=show_step1).props(
                "flat color=gray-7 size=lg"
            ).style("min-height: 48px")

            step2_next_button = ui.button(
                "Weiter", icon="arrow_forward", on_click=show_step3
            ).props("color=primary size=lg disabled").style("min-height: 48px")
```

### 4.4 Commit

```bash
git add app/ui/validation/wizard_validation.py app/ui/pages/add_item.py tests/test_ui/test_wizard_validation.py
git commit -m "feat: add step 2 conditional date fields

Implemented Step 2 with conditional date fields:
- Best before/production date (all types)
- Freeze date (only frozen types: PURCHASED_FROZEN, PURCHASED_THEN_FROZEN, HOMEMADE_FROZEN)
- Notes field (optional)
- Validation logic with date comparison
- Smart default: today's date
- Mobile-first date pickers

All tests passing, mypy + ruff clean.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Phase 5: Step 3 - Location & Categories

**Ziel:** Lagerort-Auswahl + Kategorien-Auswahl

### 5.1 Step 3 Validation Logic

**Datei:** `app/ui/validation/wizard_validation.py` (erweitern)

```python
def validate_location(location_id: int | None) -> str | None:
    """Validate location selection."""
    if location_id is None:
        return "Bitte Lagerort auswählen"
    return None


def validate_step3(location_id: int | None) -> dict[str, str]:
    """Validate Step 3 fields."""
    errors: dict[str, str] = {}

    if error := validate_location(location_id):
        errors["location"] = error

    # Categories are optional, no validation needed

    return errors
```

### 5.2 Step 3 UI implementieren

- Location Select (Dropdown mit allen aktiven Locations)
- Category Multi-Select (optional)
- Summary aus Step 1 + 2
- Zurück + Speichern Buttons

### 5.3 Commit

---

## Phase 6: Save Integration

**Ziel:** "Speichern" Button funktional - Item in DB speichern

### 6.1 Save Handler implementieren

**Datei:** `app/ui/pages/add_item.py`

```python
def save_item() -> None:
    """Save item to database."""
    from ...services import item_service
    from ...database import get_engine
    from sqlmodel import Session

    # Final validation
    errors = {}
    errors.update(validate_step1(...))
    errors.update(validate_step2(...))
    errors.update(validate_step3(...))

    if errors:
        ui.notify("Bitte alle Pflichtfelder ausfüllen", type="warning")
        return

    # Get current user from session
    user_id = app.storage.user.get("id")

    # Save to database
    with Session(get_engine()) as session:
        item = item_service.create_item(
            session=session,
            product_name=form_data["product_name"],
            best_before_date=form_data["best_before_date"],
            freeze_date=form_data.get("freeze_date"),
            quantity=form_data["quantity"],
            unit=form_data["unit"],
            item_type=form_data["item_type"],
            location_id=form_data["location_id"],
            created_by=user_id,
            category_ids=form_data.get("category_ids", []),
            notes=form_data.get("notes"),
        )

    ui.notify(f"✅ {form_data['product_name']} gespeichert!", type="positive")
    ui.navigate.to("/dashboard")
```

### 6.2 Tests für Save Integration

- Integration test: Save item and verify in DB
- Test error handling

### 6.3 Commit

---

## Phase 7: "Speichern & Nächster" Flow

**Ziel:** Item speichern + Wizard zurücksetzen mit Smart Defaults

### 7.1 Save & Next Handler

```python
def save_and_next() -> None:
    """Save item and prepare for next entry."""
    # Save item (reuse save_item logic)
    save_item_to_db()

    # Store smart defaults in browser storage
    app.storage.user["last_item_entry"] = {
        "timestamp": datetime.now().isoformat(),
        "item_type": form_data["item_type"],
        "unit": form_data["unit"],
        "location_id": form_data["location_id"],
        "category_ids": form_data.get("category_ids", []),
        "best_before_date": form_data["best_before_date"].isoformat(),
    }

    # Reset wizard but keep smart defaults
    ui.notify(f"✅ {form_data['product_name']} gespeichert!", type="positive")
    reset_wizard_with_smart_defaults()
```

### 7.2 Commit

---

## Phase 8: Smart Defaults (Browser Storage)

**Ziel:** Letzte Eingaben als Defaults vorauswählen (30 Min Zeitfenster)

### 8.1 Smart Defaults Logic

```python
def load_smart_defaults() -> None:
    """Load smart defaults from browser storage."""
    last_entry = app.storage.user.get("last_item_entry")

    if not last_entry:
        return

    timestamp = datetime.fromisoformat(last_entry["timestamp"])
    time_diff = (datetime.now() - timestamp).total_seconds() / 60  # minutes

    # Item type + categories: 30 min window
    if time_diff < 30:
        form_data["item_type"] = last_entry.get("item_type")
        form_data["category_ids"] = last_entry.get("category_ids", [])
        form_data["best_before_date"] = date_type.fromisoformat(
            last_entry.get("best_before_date", date_type.today().isoformat())
        )

    # Unit: always
    form_data["unit"] = last_entry.get("unit", "g")

    # Location: always
    form_data["location_id"] = last_entry.get("location_id")
```

### 8.2 Tests für Smart Defaults

- Test 30-min time window
- Test location always pre-filled
- Test unit always pre-filled

### 8.3 Commit

---

## Phase 9: UI Polish & Mobile Optimization

**Ziel:** Final touches, Accessibility, Mobile UX

### 9.1 Features

- Loading states für Save
- Error messages inline (validation)
- Progress bar animation
- Swipe gestures (optional)
- Keyboard navigation
- Screen reader labels (ARIA)

### 9.2 Accessibility

```python
# Add ARIA labels
product_name_input.props("aria-label='Produktname eingeben'")
next_button.props("aria-label='Weiter zu Schritt 2'")
```

### 9.3 Performance

- Debounce validation (avoid too frequent updates)
- Optimize re-renders

### 9.4 Final Testing

```bash
uv run pytest tests/ -v --cov=app/ui
uv run mypy app/
uv run ruff check app/
```

### 9.5 Commit

```bash
git commit -m "feat: ui polish and mobile optimization

Final touches for Item Capture Wizard:
- Loading states and error handling
- Accessibility improvements (ARIA labels)
- Mobile UX optimizations
- Performance improvements
- Full test coverage

Wizard MVP complete! 🎉

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Zusammenfassung Phase 4-9

Jede Phase folgt dem TDD-Muster:
1. ✅ Tests schreiben (rot)
2. ✅ Feature implementieren (grün)
3. ✅ mypy + ruff
4. ✅ Commit + Push

**Gesamtfortschritt nach Phase 9:**
- ✅ 3-Schritt-Wizard vollständig funktional
- ✅ Conditional Logic (Datumsfelder je nach ItemType)
- ✅ Save Integration mit DB
- ✅ "Speichern & Nächster" Workflow
- ✅ Smart Defaults (30 Min Zeitfenster)
- ✅ Mobile-First UX
- ✅ Vollständige Test-Coverage

---

## Wichtige Hinweise

### Database Isolation
- **Jeder Test** bekommt frische in-memory SQLite DB
- **Production DB** wird NIE berührt
- **Fixtures** `isolated_test_database` + `cleanup_ui_packages` sind autouse=True

### UI Testing Best Practices
- Alle UI-Funktionen müssen getestet werden
- Echte Browser-Tests mit `user: User` Fixture
- Async/await syntax für alle UI Tests
- Tests müssen zuerst fehlschlagen (rot), dann implementieren (grün)

### Commit Messages
- Format: `feat:`, `test:`, `fix:`, `refactor:`
- Klare Beschreibung was geändert wurde
- Immer mit Claude Code Attribution

### Quality Checks
Nach jedem Commit:
```bash
uv run pytest tests/ -v
uv run mypy app/
uv run ruff check app/
```

Alle müssen grün sein ✅ vor dem Push!

---

## Geschätzte Gesamtzeit

- **Phase 0:** ~2 Stunden (Testing Setup)
- **Phase 1:** ~1 Stunde (ItemType Enum)
- **Phasen 2-9:** ~2-3 Stunden pro Phase
- **Gesamt:** ~20-30 Stunden reine Implementierung

---

## Status Tracking

- [x] Plan erstellt und dokumentiert
- [x] **Phase 0: UI Testing Infrastructure** ✅ (2025-11-24)
  - Database isolation with in-memory SQLite
  - NiceGUI testing plugin integration
  - 58 tests passing (3 DB isolation + 51 services + 4 UI)
  - Production DB never touched
- [x] **Phase 1: ItemType Enum Update** ✅ (2025-11-24)
  - Updated ItemType enum: TINNED/JARRED/FROZEN/CHILLED/AMBIENT → PURCHASED_FRESH/PURCHASED_FROZEN/PURCHASED_THEN_FROZEN/HOMEMADE_FROZEN/HOMEMADE_PRESERVED
  - Updated expiry_calculator to handle 3 frozen types
  - Updated all test files with new enum values
  - Created Alembic migration (no-op for SQLite)
  - All 58 tests passing, mypy + ruff clean
- [x] **Phase 2: Wizard Grundstruktur + Step 1 Basis** ✅ (2025-11-24)
  - Created /items/add route with @require_auth
  - Step 1 UI: product name, item type (5 radios), quantity, unit
  - Progress indicator (Schritt 1 von 3)
  - Mobile-first layout with 48x48px touch targets
  - Bottom navigation integration
  - UI test: auth requirement verified
  - Note: Full interaction tests deferred to Phase 3 (need login flow)
- [x] **Phase 3: Step 1 Validation + Navigation** ✅ (2025-11-24)
  - Created validation module (app/ui/validation/wizard_validation.py)
  - 16 unit tests for validation logic (all passing)
  - Reactive form state with bind_value()
  - "Weiter" button enabled/disabled based on validation
  - Navigation to Step 2 with form data summary
  - Step 2 basic structure (placeholder for Phase 4)
  - All 75 tests passing, mypy + ruff clean
- [ ] Phase 4: Step 2 Implementation
- [ ] Phase 5: Step 3 Implementation
- [ ] Phase 6: Save Integration
- [ ] Phase 7: Save & Next Flow
- [ ] Phase 8: Smart Defaults
- [ ] Phase 9: UI Polish

---

**Ende des Implementierungsplans**
