# Docker Deployment

Diese Anleitung beschreibt die Bereitstellung von Fuellhorn mit Docker und Docker Compose.

## Voraussetzungen

- Docker Engine 20.10+
- Docker Compose v2+

## Schnellstart (Production)

Die einfachste Methode verwendet das veröffentlichte GHCR-Image:

```bash
# .env erstellen und konfigurieren
cp .env.example .env

# WICHTIG: Secrets anpassen!
# - SECRET_KEY: Mindestens 32 Zeichen
# - FUELLHORN_SECRET: Mindestens 32 Zeichen
# - POSTGRES_PASSWORD: Sicheres Datenbankpasswort

# Container starten
docker compose up -d

# Logs prüfen
docker compose logs -f app
```

Die Anwendung ist dann unter http://localhost:8080 erreichbar.

## Lokale Entwicklung

Für die Entwicklung mit Source-Build:

```bash
docker compose -f docker-compose.local.yml up
```

Diese Variante:
- Baut das Image aus dem lokalen Quellcode (Dockerfile.dev)
- Mountet das `app/`-Verzeichnis für Code-Änderungen ohne Rebuild
- Verwendet sichere Development-Defaults

Rebuild nach Dependency-Änderungen:
```bash
docker compose -f docker-compose.local.yml up --build
```

## Umgebungsvariablen

| Variable | Beschreibung | Erforderlich | Default |
|----------|--------------|--------------|---------|
| `SECRET_KEY` | App-Secret (min. 32 Zeichen) | Ja | - |
| `FUELLHORN_SECRET` | NiceGUI Storage Secret | Ja | - |
| `POSTGRES_PASSWORD` | Datenbank-Passwort | Ja | - |
| `POSTGRES_USER` | Datenbank-Benutzer | Nein | `fuellhorn` |
| `POSTGRES_DB` | Datenbank-Name | Nein | `fuellhorn` |
| `APP_PORT` | Externer Port | Nein | `8080` |
| `DEBUG` | Debug-Modus | Nein | `false` |

### Secrets generieren

```bash
# Python Secret generieren
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Datenbank-Backup

### Backup erstellen

```bash
docker exec fuellhorn-db pg_dump -U fuellhorn fuellhorn > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Backup wiederherstellen

```bash
docker exec -i fuellhorn-db psql -U fuellhorn fuellhorn < backup.sql
```

## Container-Verwaltung

```bash
# Status prüfen
docker compose ps

# Container stoppen
docker compose down

# Container stoppen und Volumes löschen (ACHTUNG: Datenverlust!)
docker compose down -v

# Logs anzeigen
docker compose logs -f

# In Container-Shell wechseln
docker exec -it fuellhorn-app /bin/bash
```

## Update

```bash
# Neues Image holen
docker compose pull

# Container neu starten
docker compose up -d
```

## Fehlerbehebung

### Container startet nicht

1. Logs prüfen: `docker compose logs app`
2. Healthcheck der Datenbank prüfen: `docker compose ps`
3. Umgebungsvariablen prüfen: Sind alle erforderlichen Secrets gesetzt?

### Datenbank-Verbindung fehlgeschlagen

1. Prüfen ob DB-Container läuft: `docker compose ps db`
2. Healthcheck-Status: `docker inspect fuellhorn-db --format='{{.State.Health.Status}}'`
3. Netzwerk prüfen: `docker network inspect fuellhorn-network`

### Migrations-Fehler

Die Alembic-Migrationen werden beim Start automatisch ausgeführt. Bei Fehlern:

```bash
# Manuell Migrationen ausführen
docker exec fuellhorn-app uv run alembic upgrade head
```
