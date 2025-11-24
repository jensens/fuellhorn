# Fuellhorn - Technology Stack

## Entscheidung: NiceGUI-basierter Stack (wie VellenBase)

Basierend auf deinen positiven Erfahrungen mit VellenBase nutzen wir den gleichen bewährten Stack.

## Technology Stack

### Core Technologies

**Language & Runtime:**
- **Python 3.14+** (modern Python features)
- **uv** als Package Manager (schnell, modern)

**Web Framework:**
- **NiceGUI 3.3.1+**
  - All-in-One Web UI Framework (FastAPI + Vue + Quasar)
  - Pythonic UI-Entwicklung (kein JavaScript nötig)
  - Built-in responsive Design
  - Exzellent für self-hosting
  - Einfache Session-Verwaltung

**Database:**
- **SQLModel 0.0.27** (ORM)
  - Kombiniert SQLAlchemy + Pydantic
  - Type-safe Modelle
  - Perfekt für FastAPI/NiceGUI
- **SQLite** (Development)
- **PostgreSQL** (Production via Docker)

**Security:**
- **bcrypt** für Passwort-Hashing
- **python-dotenv** für Environment-Variablen
- Built-in CSRF/XSS Protection via NiceGUI/FastAPI

**Database Migrations:**
- **Alembic** für Schema-Versioning

---

## Projekt-Struktur

```
fuellhorn/
├── app/
│   ├── models/              # SQLModel Entitäten
│   │   ├── __init__.py
│   │   ├── user.py          # User (von VellenBase übernehmen)
│   │   ├── item.py          # Item (Vorratsartikel)
│   │   ├── category.py      # Category
│   │   ├── location.py      # Location
│   │   ├── freeze_time_config.py
│   │   └── audit_log.py
│   │
│   ├── services/            # Business Logic
│   │   ├── __init__.py
│   │   ├── auth_service.py  # (von VellenBase übernehmen)
│   │   ├── item_service.py
│   │   ├── category_service.py
│   │   └── expiry_calculator.py  # Haltbarkeitsberechnung
│   │
│   ├── auth/                # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── permissions.py   # (von VellenBase anpassen)
│   │   └── decorators.py    # @require_auth, @require_permission
│   │
│   ├── ui/                  # NiceGUI UI
│   │   ├── __init__.py
│   │   ├── layout.py        # Main layout (Sidebar, Header)
│   │   ├── auth.py          # Login page (von VellenBase übernehmen)
│   │   ├── components/      # Wiederverwendbare UI-Komponenten
│   │   │   ├── __init__.py
│   │   │   ├── item_table.py
│   │   │   ├── item_form.py
│   │   │   └── expiry_badge.py
│   │   └── pages/           # UI Pages
│   │       ├── __init__.py
│   │       ├── dashboard.py      # Dashboard mit Ablaufübersicht
│   │       ├── items.py          # Vorratsliste
│   │       ├── add_item.py       # Artikel erfassen (Wizard)
│   │       ├── categories.py     # Kategorie-Verwaltung (Admin)
│   │       ├── locations.py      # Lagerort-Verwaltung (Admin)
│   │       ├── users.py          # Benutzer-Verwaltung (von VellenBase)
│   │       └── settings.py       # Gefrierzeit-Konfiguration
│   │
│   ├── utils/               # Helper Functions
│   │   ├── __init__.py
│   │   ├── security.py      # (von VellenBase übernehmen)
│   │   └── date_utils.py    # Datumsberechnungen
│   │
│   ├── database.py          # DB Setup (von VellenBase übernehmen)
│   └── config.py            # Configuration (von VellenBase anpassen)
│
├── alembic/                 # Database Migrations
│   └── versions/
│
├── tests/                   # Tests
│   ├── test_models/
│   ├── test_services/
│   └── test_ui/
│
├── data/                    # SQLite DB (development)
│   └── fuellhorn.db
│
├── .env                     # Environment Variables
├── .env.example             # Example Environment
├── main.py                  # Application Entry Point
├── pyproject.toml           # Project Config & Dependencies
├── alembic.ini              # Alembic Config
├── README.md
├── Dockerfile               # Docker Setup
└── docker-compose.yml       # Docker Compose (PostgreSQL + App)
```

---

## Von VellenBase übernehmen

### 1. Komplette Übernahme (1:1)
- **User Model** (`app/models/user.py`)
  - Anpassen: Rollen auf `admin` und `user` reduzieren (statt 4 Rollen)
- **Auth Service** (`app/services/auth_service.py`)
- **Auth System** (`app/auth/permissions.py`, `app/auth/decorators.py`)
  - Anpassen: Permissions für Fuellhorn (ITEMS_READ, ITEMS_WRITE, CONFIG_MANAGE)
- **Database Setup** (`app/database.py`)
- **Config** (`app/config.py`)
- **Login Page** (`app/ui/auth.py`)
- **Layout** (`app/ui/layout.py`)
  - Anpassen: Navigation für Fuellhorn (Dashboard, Vorrat, Admin)
- **Security Utils** (`app/utils/security.py`)

### 2. Als Vorlage nutzen
- **UI Pages** - Struktur und Patterns übernehmen
  - Tabellen mit Filter/Suche
  - Create/Edit Dialogs
  - Permission-basierte Sichtbarkeit
- **Service Layer Pattern** - Business Logic trennen
- **Error Handling** - Notifications, Try/Catch
- **Testing Setup** - pytest-Struktur

---

## Rollenmodell für Fuellhorn

Vereinfachtes Rollenmodell (2 Rollen statt 4):

### 1. Admin
**Permissions:**
- `ADMIN_FULL` - Voller Zugriff
- `USER_MANAGE` - Benutzer verwalten
- `CONFIG_MANAGE` - Kategorien, Lagerorte, Gefrierzeiten konfigurieren
- `ITEMS_READ` - Vorrat einsehen
- `ITEMS_WRITE` - Artikel erfassen, bearbeiten, entnehmen

### 2. User (Befüller)
**Permissions:**
- `ITEMS_READ` - Vorrat einsehen
- `ITEMS_WRITE` - Artikel erfassen, bearbeiten, entnehmen

**Access Control Rules:**
- Gemeinsamer Vorrat für alle Benutzer eines Haushalts
- Nur Admins können Kategorien, Lagerorte, Gefrierzeiten verwalten
- Audit-Log für alle Aktionen

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "fuellhorn"
version = "0.1.0"
description = "Lebensmittelvorrats-Verwaltung"
authors = [
    { name = "Jens Jensens", email = "jens@example.com" }
]
requires-python = ">=3.14"
dependencies = [
    "nicegui>=3.3.1",
    "sqlmodel>=0.0.27",
    "bcrypt>=4.0.0",
    "python-dotenv>=1.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",  # PostgreSQL driver
    "python-dateutil>=2.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "ruff>=0.5.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.mypy]
strict = true
disallow_untyped_defs = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 120
target-version = "py314"
```

---

## Environment Variables (.env)

```env
# Application
DEBUG=true
HOST=0.0.0.0
PORT=8080

# Security
SECRET_KEY=your-super-secret-key-here-min-32-chars
FUELLHORN_SECRET=another-secret-for-password-pepper

# Database
DB_TYPE=sqlite
DATABASE_URL=sqlite:///data/fuellhorn.db
# For production with PostgreSQL:
# DB_TYPE=postgresql
# DATABASE_URL=postgresql://user:password@localhost:5432/fuellhorn
```

---

## Implementierungs-Reihenfolge

### Phase 1: Basis-Setup (Tag 1-2)
1. ✅ Projekt initialisieren (pyproject.toml, main.py)
2. ✅ VellenBase Auth-System übernehmen und anpassen
3. ✅ Database Setup (database.py, config.py)
4. ✅ User Model + Auth Service
5. ✅ Login Page + Layout mit Sidebar
6. ✅ Test: Login funktioniert

### Phase 2: Datenmodell (Tag 3-4)
1. ✅ Models erstellen (Item, Category, Location, FreezeTimeConfig, AuditLog)
2. ✅ Alembic Migrations
3. ✅ Service Layer für Items
4. ✅ Expiry Calculator (Haltbarkeitsberechnung)
5. ✅ Unit Tests für Models & Services

### Phase 3: Kern-UI (Tag 5-8)
1. ✅ Dashboard mit Ablaufübersicht (rot/gelb/grün)
2. ✅ Vorratsliste mit Filter/Suche/Sortierung
3. ✅ Artikel-Erfassung (Wizard, 3 Schritte)
   - Schritt 1: Produktname, Typ, Menge
   - Schritt 2: Datum (MHD/Produktionsdatum/Einfrierdatum je nach Typ)
   - Schritt 3: Lagerort, Kategorien, Notizen
   - "Weiter zum nächsten Artikel" nach Speichern
4. ✅ Artikel-Details anzeigen
5. ✅ Entnahme-Funktion (Dialog)

### Phase 4: Admin-Bereich (Tag 9-10)
1. ✅ Kategorie-Verwaltung (CRUD)
2. ✅ Lagerort-Verwaltung (CRUD)
3. ✅ Gefrierzeit-Konfiguration
4. ✅ Benutzer-Verwaltung (von VellenBase übernehmen)

### Phase 5: Polishing & Tests (Tag 11-12)
1. ✅ Responsive Design testen
2. ✅ Audit-Logging einbauen
3. ✅ Integration Tests
4. ✅ Docker Setup (Dockerfile, docker-compose.yml)
5. ✅ README mit Installation & Setup

---

## UI Design Principles (von VellenBase übernehmen)

**Gleiche Patterns wie VellenBase:**
- Left Sidebar Navigation (immer sichtbar)
- Hauptbereich mit Breadcrumb
- Tabellen mit Filter/Suche/Sortierung
- Modals/Dialogs für Create/Edit
- Notifications (Success/Error Toast)
- Farbcodierung für Status (rot/gelb/grün)

**NiceGUI First Approach:**
1. Soviele NiceGUI Core-Komponenten wie möglich verwenden
2. Wenn etwas fehlt: Erst recherchieren, ob es ein gepflegtes Plugin gibt
3. Nur wenn nichts existiert: Selbst machen

**Design:**
- Mit NiceGUI Standard-Theme starten (Quasar/Material Design)
- **Funktion zuerst, angepasstes Design später**
- Keine vorzeitige Design-Arbeit

---

## Vorteile dieses Stacks

✅ **Bewährt**: VellenBase läuft erfolgreich mit diesem Stack
✅ **Schnell**: Pythonic UI-Entwicklung ohne JavaScript
✅ **Type-Safe**: SQLModel + Mypy + Pydantic
✅ **Self-Hostable**: Docker + SQLite/PostgreSQL
✅ **Sicher**: bcrypt, Permission-System, Audit-Logging
✅ **Wartbar**: Klare Trennung (Models/Services/UI)
✅ **Testbar**: Pytest + Type Safety
✅ **Produktionsreif**: Alembic Migrations, PostgreSQL-Support

---

## Nächste Schritte

1. ✅ Tech-Stack Dokumentation abgestimmt
2. 🔄 Projekt initialisieren (Phase 1 starten)
3. 🔜 VellenBase Code übernehmen und anpassen
4. 🔜 Datenmodell implementieren
5. 🔜 UI aufbauen
