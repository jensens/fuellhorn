# Entwicklungsregeln für Fuellhorn

Detaillierte Dokumentation findest du in:

```
docs/agent/
├── aufgabenverwaltung.md      # Issue-Workflow
├── architektur_erklaert.md    # 3-Schichten-Modell
├── informationsarchitektur.md # Navigation, User Flows
├── tech_stack.md              # Technologien, Konfiguration
├── tests_schreiben.md         # Test-Strategie
└── ui_und_design.md           # Visuelles Design
```
---

## Wichtigste Regeln

### Zusammenfassung Agent-Regeln

- ✅ Nur am zugewiesenen Issue arbeiten
- ✅ Tests sind Pflicht
- ✅ Kleine, häufige Commits
- ✅ PR erstellen wenn fertig
- ❌ Keine anderen Dateien ändern als nötig
- ❌ Keine "Verbesserungen" ohne Issue
- ❌ Nicht auf main pushen
- ✅ **IMMER Linter/Formatter VOR Tests ausführen**: `uv run ruff format app/ && uv run ruff check --fix app/`


### Test Driven Development

Immer lesen und befolgen wenn Code hinzugefügt/geändert wird: [docs/agent/tests_schreiben.md](docs/agent/tests_schreiben.md)

### Issues first

- Immer den Issue Workflow befolgen
- Issues liegen auf Github.
- Immer auf Issues arbeiten, nie Code ohne Issue Bezug ändern
- Im Zweifel Issue anlegen

Immer lesen und befolgen wenn Issues, Epics, ... bearbeitet werden: [docs/agent/aufgabenverwaltung.md](docs/agent/aufgabenverwaltung.md)

### MCP Server (tributary)

Für alle GitHub-Operationen den `tributary` MCP-Server verwenden:
- Issues lesen/erstellen/bearbeiten
- PRs erstellen
- Labels setzen
- Kommentare schreiben

Verfügbare Tools: `mcp__tributary_*`

**Nicht** `gh` CLI direkt nutzen, sondern immer die MCP-Tools.


### Commit-Regeln

- **Häufige, kleine Commits** - lieber 10 kleine als 1 großer!
- **Commit-Typen:** `feat`, `fix`, `test`, `refactor`, `docs`, `chore`
- **Tidy First:** Strukturelle und verhaltensändernde Änderungen NIEMALS mischen!
- **Linter, Typecheck, Test** sind grün vor Commit!

---

## Schnellreferenz

### Dev-Server (parallele Entwicklung)

**Für Worktrees automatisch Port und Testdaten konfiguriert:**

Im main oder im worktree:

```bash
./scripts/dev-server.sh
```

- **Port**: 8000 + Issue-Nummer (z.B. Issue 123 → Port 8123)
- **Testdaten**: Admin (admin/admin), Kategorien, Lagerorte, Beispiel-Items
- Jeder Worktree hat eigene SQLite-DB

```bash
# Ohne Testdaten starten
./scripts/dev-server.sh --no-seed

# Manuell mit Port
PORT=8123 uv run python main.py
```

### Häufige Befehle

```bash
# App starten (Standard-Port 8080)
uv run python main.py

# Qualitätsprüfung (alles)
uv run pytest && uv run mypy app/ && uv run ruff check app/

# Migration erstellen
uv run alembic revision --autogenerate -m "description"

# Migration anwenden
uv run alembic upgrade head

# Dependencies
uv add <package>        # Production
uv add --dev <package>  # Development
```
