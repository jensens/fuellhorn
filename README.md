# Füllhorn

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
git clone https://github.com/yourusername/fuellhorn.git
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

### 6. Anwendung starten

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

### Tests ausführen

```bash
# Alle Tests
uv run pytest

# Mit Coverage
uv run pytest --cov=app --cov-report=html

# Spezifische Tests
uv run pytest tests/test_models.py -v
```

### Code Quality

```bash
# Type Checking
uv run mypy app/

# Linting
uv run ruff check app/
uv run ruff check --fix app/

# Formatierung
uv run ruff format app/

# Alles zusammen
uv run pytest && uv run mypy app/ && uv run ruff check app/
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
│   ├── models/              # SQLModel Entitäten
│   ├── services/            # Business Logic
│   ├── auth/                # Authentication & Authorization
│   ├── ui/                  # NiceGUI UI
│   │   ├── pages/           # UI Pages
│   │   └── components/      # Wiederverwendbare Komponenten
│   └── utils/               # Helper Functions
├── alembic/                 # Database Migrations
├── tests/                   # Tests
├── data/                    # SQLite DB (development)
├── main.py                  # Application Entry Point
├── pyproject.toml           # Project Config & Dependencies
└── .env                     # Environment Variables
```

## Docker Deployment

```bash
# Docker Image bauen
docker build -t fuellhorn .

# Mit docker-compose starten
docker-compose up -d
```

## Development Guidelines

Bitte lies vor der Entwicklung:
- [CLAUDE.md](CLAUDE.md) - Entwicklungsregeln und Best Practices
- [TESTING.md](TESTING.md) - Testing Strategy

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
- ❌ Kubernetes Deployment (CDK8s)

Siehe [CLAUDE.md](CLAUDE.md) für vollständige Roadmap.

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

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
