# Füllhorn

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Lebensmittelvorrats-Verwaltung** - Self-hosted inventory management for food storage

Füllhorn ist eine moderne, mobile-first Web-Anwendung zur Verwaltung von Lebensmittelvorräten. Die Anwendung hilft Familien dabei, den Überblick über eingefrorene, eingemachte und gekaufte Lebensmittel zu behalten und Lebensmittelverschwendung zu vermeiden.

## Features (MVP)

- ✅ **Mobile-First Design** - Optimiert für Smartphone-Nutzung
- ✅ **5 Artikel-Typen** mit intelligenter Haltbarkeitsberechnung:
  - Gekauft (nicht gefroren)
  - Gekauft (bereits gefroren)
  - Gekauft und eingefroren
  - Selbst hergestellt (gefroren)
  - Selbst hergestellt (eingemacht)
- ✅ **Smart Defaults** - Zeitfenster-basierte Vorauswahl spart 80% der Eingaben
- ✅ **Ablaufübersicht** - Farbcodierte Warnungen (rot/gelb/grün)
- ✅ **Multi-User** - Rollenbasierte Zugriffskontrolle (Admin, User)
- ✅ **Self-Hostable** - Docker-based deployment

## Tech Stack

- **Backend:** Python 3.14+, FastAPI, SQLModel
- **Frontend:** NiceGUI 3.3.1+ (Vue + Quasar)
- **Database:** SQLite (dev), PostgreSQL (production)
- **Package Manager:** uv
- **Migrations:** Alembic

## Requirements

- Python 3.14+
- uv (package manager)

## Installation

### 1. uv installieren

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Projekt klonen

```bash
git clone https://github.com/jensens/fuellhorn.git
cd fuellhorn
```

### 3. Virtual Environment und Dependencies

```bash
# Python 3.14 installieren und venv erstellen
uv python install 3.14
uv venv

# Dependencies installieren
uv sync

# Development Dependencies installieren
uv sync --dev
```

### 4. Environment-Variablen

```bash
cp .env.example .env
# .env bearbeiten und Secrets eintragen
```

### 5. Datenbank initialisieren

```bash
# Alembic Migrations ausführen
uv run alembic upgrade head
```

### 6. Initialen Admin-Benutzer anlegen

```bash
# Lokale Entwicklung
ADMIN_PASSWORD=your-secure-password uv run fuellhorn create-admin

# Docker Compose (das Prod-Image enthält nur das installierte Paket und sein CLI)
docker compose exec -e ADMIN_PASSWORD=your-secure-password app fuellhorn create-admin
```

Der Admin-Benutzer kann über Environment-Variablen konfiguriert werden:
- `ADMIN_USERNAME` - Benutzername (default: `admin`)
- `ADMIN_EMAIL` - E-Mail-Adresse (default: `admin@fuellhorn.local`)
- `ADMIN_PASSWORD` - Passwort (**erforderlich**, kein Default aus Sicherheitsgründen)

**Wichtig:** Das Passwort nach dem ersten Login ändern!

### 7. Anwendung starten

```bash
uv run python main.py
```

Die Anwendung ist dann erreichbar unter: `http://localhost:8080`

## Development

### Pre-Commit Hooks installieren

```bash
uv tool install pre-commit
uv run pre-commit install
```

### Dev-Server (für parallele Entwicklung)

Das Dev-Server Script konfiguriert automatisch Port und Testdaten basierend auf dem Git-Worktree:

```bash
./scripts/dev-server.sh
```

- **Port**: 8000 + Issue-Nummer (z.B. Issue 123 → Port 8123)
- **Testdaten**: Admin-User (admin/admin123), Kategorien, Lagerorte, Beispiel-Items
- Jeder Worktree hat eine eigene SQLite-DB

```bash
# Ohne Testdaten starten
./scripts/dev-server.sh --no-seed

# Manuell mit spezifischem Port
PORT=8123 uv run python main.py
```

### Tests ausführen

```bash
# Alle Tests
uv run pytest

# Mit Coverage
uv run pytest --cov=app --cov-report=html

# Spezifische Tests
uv run pytest tests/test_services -v
```

### Code Quality

```bash
# Type Checking
uv run ty check app/

# Linting
uv run ruff check app/
uv run ruff check --fix app/

# Formatierung
uv run ruff format app/

# Alles zusammen
uv run pytest && uv run ty check app/ && uv run ruff check app/
```

### Datenbank Migrations

```bash
# Neue Migration erstellen
uv run alembic revision --autogenerate -m "Beschreibung"

# Migration anwenden
uv run alembic upgrade head

# Migration rückgängig machen
uv run alembic downgrade -1

# Migration History
uv run alembic history
```

## Projekt-Struktur

```
fuellhorn/
├── app/
│   ├── api/                 # REST API Endpoints (Health-Check)
│   ├── auth/                # Authentication & Authorization
│   ├── models/              # SQLModel Entitäten
│   ├── services/            # Business Logic
│   ├── alembic/             # Database Migrations (Alembic)
│   ├── static/              # Static Files (CSS, JS)
│   ├── ui/                  # NiceGUI UI
│   │   ├── components/      # Wiederverwendbare Komponenten
│   │   ├── pages/           # UI Pages
│   │   ├── theme/           # Theme-System
│   │   └── validation/      # Form-Validierung
│   └── utils/               # Helper Functions
├── docs/                    # Dokumentation
│   └── agent/               # Agent-spezifische Docs
├── scripts/                 # Hilfs-Skripte (dev-server.sh)
├── tests/                   # Tests
├── data/                    # SQLite DB (development)
├── main.py                  # Application Entry Point
├── pyproject.toml           # Project Config & Dependencies
└── .env                     # Environment Variables
```

## Docker Deployment

Füllhorn ist für Self-Hosting mit Docker konzipiert. Es gibt zwei Deployment-Optionen:

### Option 1: Docker Compose (Empfohlen)

Docker Compose startet Füllhorn mit PostgreSQL als Produktions-Datenbank.

#### Schritt 1: Repository klonen

```bash
git clone https://github.com/jensens/fuellhorn.git
cd fuellhorn
```

#### Schritt 2: Environment-Variablen konfigurieren

```bash
cp .env.example .env
```

**WICHTIG: Sichere Secrets generieren und in `.env` eintragen!**

```bash
# Secrets generieren:
python -c "import secrets; print('FUELLHORN_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"
```

Mindestens diese Werte in `.env` anpassen:
- `FUELLHORN_SECRET` - signiert die Session-Cookies (min. 32 Zeichen; Rotation meldet alle Nutzer ab)
- `POSTGRES_PASSWORD` - PostgreSQL Passwort

#### Schritt 3: Container starten

```bash
docker compose up -d
```

Die Anwendung ist dann erreichbar unter: `http://localhost:8080`

**Hinweis:** Beim ersten Start werden automatisch die Datenbank-Migrationen ausgeführt.

#### Weitere Docker Compose Befehle

```bash
# Logs anzeigen
docker compose logs -f

# Nur App-Logs
docker compose logs -f app

# Container stoppen
docker compose down

# Container stoppen und Daten löschen (ACHTUNG!)
docker compose down -v

# Neues Image holen und Container neu starten (docker-compose.yml nutzt das veröffentlichte Image)
docker compose pull
docker compose up -d
```

### Option 2: Standalone Docker (SQLite)

Für einfache Setups oder Tests kann Füllhorn auch standalone mit SQLite laufen.

```bash
# Image bauen: installiert das veröffentlichte Paket von PyPI (neueste Version) …
docker build -t fuellhorn .
# … oder eine bestimmte Version
docker build --build-arg FUELLHORN_VERSION=1.0.0a9 -t fuellhorn .

# Container starten
docker run -d \
  --name fuellhorn \
  -p 8080:8080 \
  -e FUELLHORN_SECRET="your-nicegui-secret-min-32-chars" \
  -v fuellhorn-data:/app/data \
  fuellhorn
```

Die SQLite-Datei liegt unter `/app/data/fuellhorn.db` im Volume (`FUELLHORN_DATA_DIR`, im Image vorbelegt). Ohne das Volume gehen die Daten beim Neuerstellen des Containers verloren.

**Hinweis:** SQLite ist nur für Einzelnutzer/Tests geeignet. Für Produktions-Deployments mit mehreren Nutzern wird PostgreSQL empfohlen.

### Option 3: Kubernetes (Helm)

Füllhorn bietet einen Helm Chart für Kubernetes-Deployments mit automatischer Migration und Admin-Erstellung.

```bash
helm install fuellhorn ./charts/fuellhorn \
  --set secrets.fuellhornSecret="your-fuellhorn-secret-min-32-chars" \
  --set database.type=postgresql \
  --set database.external.host=postgres.example.com \
  --set database.external.existingSecret=postgres-credentials
```

Features:
- **Automatische Migrationen** - Alembic läuft als Init-Container
- **Optionale Admin-Erstellung** - GitOps-freundlich, keine manuellen Schritte
- **Flexible Konfiguration** - SQLite oder PostgreSQL, Ingress, TLS

Siehe [charts/fuellhorn/README.md](charts/fuellhorn/README.md) für vollständige Dokumentation.

---

## Umgebungsvariablen

### Pflicht-Variablen (Security)

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `FUELLHORN_SECRET` | Signiert die Session-Cookies (NiceGUI `storage_secret`). **Min. 32 Zeichen!** Rotation meldet alle Nutzer ab, Passwörter bleiben gültig. | `secrets.token_urlsafe(32)` |

### Datenbank-Konfiguration

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `DB_TYPE` | Datenbanktyp: `sqlite` oder `postgresql` | `sqlite` |
| `DATABASE_URL` | Datenbank-Verbindungs-URL | `sqlite:///data/fuellhorn.db` |
| `POSTGRES_USER` | PostgreSQL Benutzername (docker-compose) | `fuellhorn` |
| `POSTGRES_PASSWORD` | PostgreSQL Passwort (docker-compose) | - |
| `POSTGRES_DB` | PostgreSQL Datenbankname (docker-compose) | `fuellhorn` |

### Anwendungs-Konfiguration

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `DEBUG` | Debug-Modus aktivieren | `false` |
| `SQL_ECHO` | Alle SQL-Statements samt Parametern loggen (nur zur Fehlersuche, enthält Hashes und Tokens) | `false` |
| `HOST` | Bind-Adresse | `0.0.0.0` |
| `PORT` | Port | `8080` |
| `APP_PORT` | Externer Port (docker-compose) | `8080` |
| `TZ` | Zeitzone des Containers. Die App speichert und zeigt Zeitstempel (Sperre „bis HH:MM“, Erfassungszeit) als naive lokale Zeit; ohne `TZ` ist das die UTC des Images (#401) | `Europe/Vienna` (docker-compose) |

### Session-Konfiguration

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `SESSION_MAX_AGE` | Ohne "Angemeldet bleiben": Abmeldung nach so vielen Sekunden ohne Aktivität | `86400` (24h) |
| `REMEMBER_ME_MAX_AGE` | Laufzeit des Sitzungs-Cookies in Sekunden (gleitend, gilt mit "Angemeldet bleiben") | `2592000` (30 Tage) |

Eine Passwortänderung (selbst, durch einen Admin oder per `create-admin --reset-password`) meldet alle anderen
Sitzungen dieses Benutzers beim nächsten Aufruf ab. Sitzungsdaten liegen serverseitig im NiceGUI-Storage
(`$FUELLHORN_DATA_DIR/.nicegui`, überschreibbar über `NICEGUI_STORAGE_PATH`; im Container also auf dem
Daten-Volume, sonst meldet jeder Neustart alle Benutzer ab); im Browser liegt nur ein signiertes Cookie.

---

## Release

Veröffentlicht wird über GitHub Actions: Ein veröffentlichtes GitHub-Release mit Tag `vX.Y.Z` (bzw.
`vX.Y.ZaN` für Vorabversionen) baut das Paket, lädt es zu PyPI, baut die Container-Images für amd64 und
arm64 mit Smoke-Test und schiebt das Helm-Chart nach ghcr.io. Ein Push auf `main` veröffentlicht nur auf
Test-PyPI.

Ablauf, Tag-Regeln und Nacharbeiten: [RELEASE.md](RELEASE.md)

## Development Guidelines

Bitte lies vor der Entwicklung:
- [CLAUDE.md](CLAUDE.md) - Entwicklungsregeln und Best Practices
- [docs/agent/tests_schreiben.md](docs/agent/tests_schreiben.md) - Testing Strategy

### Aufgabenverwaltung

Alle Aufgaben werden über **GitHub Issues** verwaltet:
- **[Issues](https://github.com/jensens/fuellhorn/issues)** - Offene Aufgaben
- **[Milestones](https://github.com/jensens/fuellhorn/milestones)** - Alpha → Beta → v1.0

## Roadmap

### MVP (aktuell)
- ✅ Artikel-Erfassung mit 3-Step Wizard
- ✅ Haltbarkeitsberechnung für alle 5 Typen
- ✅ Dashboard mit Ablaufübersicht
- ✅ Benutzer- und Rechteverwaltung

### Post-MVP
- ❌ Barcode-Scanner Integration
- ❌ OCR für MHD-Erkennung
- ❌ PWA Features (Offline-Modus)
- ❌ Statistiken & Analytics
- ✅ Kubernetes Deployment (Helm Chart)

Siehe [docs/requirements.md](docs/requirements.md) für vollständige Roadmap.

## Lizenz

Füllhorn ist lizenziert unter der **GNU Affero General Public License v3.0 oder später (AGPL-3.0-or-later)**.

Die AGPL-3.0 ist eine Copyleft-Lizenz, die speziell für netzwerkbasierte Software entwickelt wurde. Sie stellt sicher, dass Änderungen am Code auch dann mit der Community geteilt werden müssen, wenn die Software nur als Webservice gehostet wird (ohne Weitergabe von Binärdateien).

Siehe [LICENSE](LICENSE) für den vollständigen Lizenztext.

## Contributing

Contributions sind willkommen! Bitte:
1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'feat: add amazing feature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

**Wichtig:** Bitte [CLAUDE.md](CLAUDE.md) beachten - Tests, Type Checking und Linting müssen grün sein!

## Support

Bei Fragen oder Problemen bitte ein Issue auf GitHub öffnen.
