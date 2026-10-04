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

## Datenbank-Initialisierung

Entwicklung (`main.py`), Produktion (`fuellhorn`-CLI) und die Seed-Befehle legen das
Schema **einheitlich über Alembic** an:

```python
run_migrations()  # Alembic: alembic upgrade head
```

- Eine leere Datenbank bekommt alle Tabellen **und** `alembic_version`
- Spätere Schema-Änderungen laufen als Migration, Daten bleiben erhalten
- Dieselbe Historie in Dev und Prod

`create_db_and_tables()` (SQLModel `create_all`) wird nur noch in Tests verwendet.
Es ist additiv (überschreibt keine Daten), legt aber keine `alembic_version` an:
Eine so erzeugte Datenbank lässt `alembic upgrade head` später mit
"table already exists" scheitern. Eine alte Dev-Datenbank, die noch per
`create_all` entstanden ist, einmalig mit `uv run alembic stamp head` markieren.

### Migrationen erstellen

**Bei jeder Model-Änderung eine Migration erstellen:**

```bash
# 1. Model ändern (z.B. in app/models/)

# 2. Migration generieren
uv run alembic revision --autogenerate -m "Beschreibung der Änderung"

# 3. Migration prüfen (in alembic/versions/)
#    - Generierte SQL-Statements überprüfen
#    - Downgrade-Funktion testen

# 4. Migration lokal testen
uv run alembic upgrade head
```

### Migrationen in Development manuell ausführen

Falls du Migrationen in der Entwicklung testen willst:

```bash
# Statt main.py direkt zu starten:
uv run alembic upgrade head
uv run python main.py
```

Oder verwende das CLI wie in Produktion:

```bash
uv run fuellhorn
```

### Häufige Fehler vermeiden

1. **Model geändert, aber keine Migration erstellt**
   - Dev funktioniert, Prod schlägt fehl
   - Lösung: Immer `alembic revision --autogenerate` nach Model-Änderungen

2. **Schema-Drift zwischen Dev und Prod**
   - Symptom: Tests laufen, Deployment fehlschlägt
   - Lösung: Regelmäßig mit `alembic upgrade head` in Dev testen

3. **Autogenerate erkennt nicht alle Änderungen**
   - Alembic erkennt nicht: Tabellen-/Spaltennamen-Änderungen, Constraints
   - Lösung: Generierte Migration manuell prüfen und anpassen

## Rollen

| Rolle | Rechte |
|-------|--------|
| `admin` | Voller Zugriff (Benutzer, Kategorien, Lagerorte, Items) |
| `user` | Items lesen/schreiben |
