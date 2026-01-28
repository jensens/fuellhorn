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

Die Alembic-Migrationen werden beim Container-Start automatisch ausgeführt.
Bei Problemen die Container-Logs prüfen:

```bash
docker compose logs app
```

Falls eine manuelle Migration erforderlich ist:

```bash
docker exec fuellhorn-app fuellhorn migrate
```

## CLI-Befehle

Das `fuellhorn`-CLI bietet folgende Befehle:

```bash
# Anwendung starten (Standard)
fuellhorn

# Nur Datenbank-Migrationen ausführen
fuellhorn migrate

# Admin-Benutzer erstellen (benötigt ADMIN_PASSWORD Env-Variable)
fuellhorn create-admin

# Standard-Kategorien mit Haltbarkeiten importieren
fuellhorn seed shelf-life-defaults

# Testdaten importieren (Admin, Kategorien, Lagerorte, Beispiel-Items)
fuellhorn seed testdata
```

### Im Container ausführen

```bash
# Standard-Kategorien importieren
docker exec fuellhorn-app fuellhorn seed shelf-life-defaults

# Testdaten importieren
docker exec fuellhorn-app fuellhorn seed testdata

# Admin erstellen
docker exec -e ADMIN_PASSWORD=geheim fuellhorn-app fuellhorn create-admin
```
