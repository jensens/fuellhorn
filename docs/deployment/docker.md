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
# - FUELLHORN_SECRET: Mindestens 32 Zeichen (signiert Session-Cookies)
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
- Verwendet feste Development-Defaults (unsichere Dev-Secrets; nur lokal verwenden)

Rebuild nach Dependency-Änderungen:
```bash
docker compose -f docker-compose.local.yml up --build
```

Hinweise:
- Das Dev-Image installiert nur die Abhängigkeiten, nicht das Paket selbst, und startet mit `uv run --no-sync`. Änderungen an `pyproject.toml`/`uv.lock` wirken erst nach `--build`.
- Weil `.git` nicht im Build-Kontext liegt, meldet das Dev-Image die Version `0.0.0.dev0`.

## Produktions-Image

Das Image (`Dockerfile`) wird in zwei Schritten gebaut:

1. `uv sync --frozen --no-dev --no-install-project` installiert **exakt die Versionen aus `uv.lock`**, also dieselben wie in Tests und CI. Ohne diesen Schritt würde jeder Build die Abhängigkeiten neu auflösen (z.B. ein neueres `sqlmodel`, das naive Datetimes ablehnt).
2. `uv pip install --no-deps fuellhorn==<Version>` legt das veröffentlichte Wheel dazu, ohne die Abhängigkeiten anzufassen.

Der Release-Workflow prüft jedes gebaute Image, bevor Versions- und `latest`-Tag entstehen: installierte Versionen gegen `uv.lock`, `fuellhorn migrate && fuellhorn create-admin` mit SQLite und `/api/health` nach dem Start.

Der Container läuft als Benutzer `fuellhorn` (uid/gid 1000), nicht als root. Bei Bind-Mounts
für `/app/data` muss das Verzeichnis dieser uid gehören (`chown 1000:1000 ./data`); benannte
Volumes übernehmen die Rechte automatisch. Der Healthcheck folgt der Variable `PORT`.

Lokal bauen (ohne `--build-arg` wird die neueste PyPI-Version installiert):

```bash
docker build --build-arg FUELLHORN_VERSION=1.0.0a9 -t fuellhorn .
```

## Umgebungsvariablen

| Variable | Beschreibung | Erforderlich | Default |
|----------|--------------|--------------|---------|
| `FUELLHORN_SECRET` | Signiert die Session-Cookies (NiceGUI `storage_secret`). Rotation meldet alle Nutzer ab. | Ja | - |
| `POSTGRES_PASSWORD` | Datenbank-Passwort | Ja | - |
| `POSTGRES_USER` | Datenbank-Benutzer | Nein | `fuellhorn` |
| `POSTGRES_DB` | Datenbank-Name | Nein | `fuellhorn` |
| `APP_PORT` | Externer Port | Nein | `8080` |
| `HOST` / `PORT` | Bind-Adresse und Port im Container | Nein | `0.0.0.0` / `8080` |
| `DEBUG` | Debug-Modus | Nein | `false` |
| `SQL_ECHO` | Alle SQL-Statements samt Parametern loggen (nur zur Fehlersuche, enthält Hashes und Tokens) | Nein | `false` |
| `TRUSTED_PROXIES` | Kommagetrennte IPs von Reverse-Proxys, deren `X-Forwarded-For` für das Login-Rate-Limiting vertraut wird. Leer: direkte Client-IP zählt. | Nein | leer |
| `FUELLHORN_DATA_DIR` | Datenverzeichnis für SQLite-Datei und Login-Sitzungen. Muss im Container auf das gemountete Volume zeigen. | Nein | `/app/data` im Image, sonst `./data` |
| `NICEGUI_STORAGE_PATH` | Verzeichnis der Login-Sitzungen (NiceGUI-Storage). Ohne Volume meldet jeder Neustart alle Benutzer ab. | Nein | `$FUELLHORN_DATA_DIR/.nicegui` |
| `NICEGUI_REDIS_URL` | Login-Sitzungen in Redis statt im Dateisystem (`redis://host:6379/0`); nötig, sobald mehrere Instanzen laufen (#434). `NICEGUI_REDIS_KEY_PREFIX` setzt den Key-Präfix. | Nein | leer |

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

Die Alembic-Migrationen werden beim Container-Start automatisch ausgeführt (Prod-Image über das
`fuellhorn`-CLI, Dev-Image über `main.py`). `FUELLHORN_SKIP_MIGRATIONS=true` schaltet das ab,
z.B. wenn der Helm-Hook-Job migriert.
Bei Problemen die Container-Logs prüfen:

```bash
docker compose logs app
```

Falls eine manuelle Migration erforderlich ist:

```bash
docker exec fuellhorn-app fuellhorn migrate
```

## Zeitzone

Die App speichert Zeitstempel (`created_at`, `last_login`, Login-Sperre „bis HH:MM“) als naive lokale Zeit
(`datetime.now()`), nicht timezone-aware (Entscheidung in Issue #401: eine einzelne Haushalts-Instanz, keine
Zeitzonen-Mischung). Der Container muss deshalb in der Zeitzone der Nutzer laufen: `TZ=Europe/Vienna` in
`docker-compose.yml` (Default) bzw. `timezone: Europe/Vienna` im Helm-Chart. Ohne `TZ` gilt UTC.

## CLI-Befehle

Das `fuellhorn`-CLI bietet folgende Befehle:

```bash
# Anwendung starten (Standard)
fuellhorn

# Nur Datenbank-Migrationen ausführen
fuellhorn migrate

# Admin-Benutzer erstellen (benötigt ADMIN_PASSWORD Env-Variable)
fuellhorn create-admin

# Recovery: Admin ausgesperrt (Passwort vergessen, versehentlich degradiert/deaktiviert)?
# Setzt den Benutzer aus ADMIN_USERNAME (Default admin) auf Rolle Admin, aktiv,
# Passwort aus ADMIN_PASSWORD. Die App verhindert zwar, dass sich der letzte
# aktive Admin selbst aussperrt, nicht aber vergessene Passwörter.
ADMIN_PASSWORD=neues-passwort fuellhorn create-admin --reset-password

# Standard-Kategorien mit Haltbarkeiten importieren (idempotent, legt nur
# Fehlendes an und überschreibt keine angepassten Werte).
# Nach Updates, die Standard-Kategorien ändern, einmal ausführen: Migrationen
# benennen nur um und ordnen bestehende Kategorien zu, neue Gruppen und
# Kategorien (z.B. Obst & Gemüse, Vorrat, Milch, Sahne) legt erst dieser Seed an.
fuellhorn seed shelf-life-defaults
```

`fuellhorn seed testdata` (Admin `admin/admin`, Beispieldaten) ist nur für die lokale
Entwicklung gedacht und läuft nur mit `DEBUG=true` oder dem ausdrücklichen Flag
`--i-know-this-is-dev`. In Produktion nicht verwenden.

Alle Seed-Befehle wenden vorher die Alembic-Migrationen an; eine leere Datenbank
wird dabei korrekt mit `alembic_version` angelegt.

### Im Container ausführen

```bash
# Standard-Kategorien importieren
docker exec fuellhorn-app fuellhorn seed shelf-life-defaults

# Admin erstellen
docker exec -e ADMIN_PASSWORD=geheim fuellhorn-app fuellhorn create-admin
```
