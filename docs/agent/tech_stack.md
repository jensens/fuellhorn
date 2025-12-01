# Tech-Stack

## Core Technologies

- **Python 3.14+** mit **uv** als Package Manager
- **NiceGUI 3.3.1+** - Web UI Framework (FastAPI + Vue + Quasar)
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **SQLite** (Development) / **PostgreSQL** (Production)
- **Alembic** - Database Migrations
- **bcrypt** - Passwort-Hashing

## Konfiguration

| Datei | Beschreibung |
|-------|--------------|
| `pyproject.toml` | Dependencies, Tool-Konfiguration |
| `.env.example` | Environment Variables Vorlage |
| `docker-compose.yml` | Production Setup mit PostgreSQL |
| `Dockerfile` | Container Build |

## Architektur

Siehe [architektur_erklaert.md](architektur_erklaert.md) für das 3-Schichten-Modell.

## Rollen

| Rolle | Rechte |
|-------|--------|
| `admin` | Voller Zugriff (Benutzer, Kategorien, Lagerorte, Items) |
| `user` | Items lesen/schreiben |
