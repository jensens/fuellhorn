# Entwicklungsregeln für Fuellhorn

Diese Datei enthält die wichtigsten Regeln für Agenten. Detaillierte Dokumentation findest du in `/docs/`.

## Lizenz

**AGPL-3.0-or-later** - Copyleft-Lizenz für netzwerkbasierte Software. Details in [LICENSE](LICENSE).

---

## Wichtigste Regeln

### 1. Tests sind Pflicht (TDD)

**Tests müssen IMMER grün sein!**

```bash
# Vor jedem Commit ausführen:
uv run pytest                    # Tests
uv run mypy app/                 # Type Check
uv run ruff check app/           # Linting
uv run ruff format app/          # Formatierung
```

- **Keine Implementierung ohne Tests**
- **Test-First Ansatz bevorzugt**: Test schreiben → rot → implementieren → grün
- **UI-Tests sind Pflicht** mit NiceGUI Testing Framework

**Detaillierte Test-Strategie:** [docs/TESTING.md](docs/TESTING.md)

### 2. Git Worktrees verwenden

**IMMER Git Worktrees für Issues verwenden!**

```bash
# 1. Haupt-Repo: main aktualisieren
git pull origin main

# 2. Worktree für Issue erstellen
git worktree add worktrees/issue-<number> -b feature/issue-<number>-<kurzbeschreibung>

# 3. In Worktree arbeiten
cd worktrees/issue-<number>

# 4. Nach Merge aufräumen (vom Hauptrepo aus)
git worktree remove worktrees/issue-<number>
```

### 3. Commit-Regeln

**Tidy First:** Strukturelle und verhaltensändernde Änderungen NIEMALS mischen!

```bash
# Strukturell (Refactoring)
git commit -m "refactor: extract expiry calculation"

# Verhaltensändernd (Features/Fixes)
git commit -m "feat: add freeze time config"
git commit -m "fix: prevent negative quantities"
```

**Commit-Typen:** `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

**Häufige, kleine Commits** - lieber 10 kleine als 1 großer!

---

## Aufgabenverwaltung

### GitHub Issues

Alle Aufgaben werden über **GitHub Issues** verwaltet: https://github.com/jensens/fuellhorn/issues

**Labels:**
- `status/agent-ready` - Issue kann bearbeitet werden
- `status/in-progress` - Agent arbeitet daran
- `status/blocked` - Wartet auf andere Issues
- `type/epic` - Übergeordnetes Issue (nicht direkt bearbeiten!)

### Issue-Abhängigkeiten

Issues können auf andere warten. Format im Issue-Body:
```
Blocked by #42
```

Automatische Freischaltung via GitHub Action wenn Blocker geschlossen wird.

### Epics und Sub-Issues

**Epics** (`type/epic` Label) werden **nicht direkt bearbeitet**. Stattdessen:
- Sub-Issues haben `Part of #<epic>` im Body
- Wenn alle Sub-Issues geschlossen → Epic wird automatisch geschlossen

### MCP Server für Task-Management

Ein MCP Server (`fuellhorn-tasks`) ermöglicht automatisierte Issue-Verwaltung:

| Tool | Beschreibung |
|------|-------------|
| `list_ready_issues` | Agent-ready Issues (ohne Epics) |
| `list_epics` | Epics mit Sub-Issue Fortschritt |
| `get_issue_briefing` | Briefing mit Worktree-Anweisungen |
| `assign_issue` | Issue übernehmen |
| `complete_issue` | Nach PR-Merge aufräumen |

**Installation:** [tools/mcp-task-server/README.md](tools/mcp-task-server/README.md)

**Typischer Workflow:**
1. `list_ready_issues` → Verfügbare Issues sehen
2. `get_issue_briefing(issue_number)` → Setup-Anweisungen holen
3. `assign_issue(issue_number)` → Issue übernehmen
4. Implementieren (TDD!)
5. PR erstellen mit `closes #<number>`
6. `complete_issue(issue_number)` → Aufräumen

---

## Architektur

### 3-Schichten-Modell

1. **Models** (`app/models/`) - SQLModel Entitäten
2. **Services** (`app/services/`) - Business Logic
3. **UI** (`app/ui/`) - NiceGUI Presentation

**Regeln:**
- Keine Business-Logic in UI-Code
- Keine UI-Code in Services
- Relative Imports innerhalb von `app/`

**Details:** [docs/tech-stack.md](docs/tech-stack.md)

### 5 Artikel-Typen

| Typ | Haltbarkeit |
|-----|-------------|
| `purchased_fresh` | MHD |
| `purchased_frozen` | MHD |
| `purchased_then_frozen` | Einfrierdatum + Gefrierzeit |
| `homemade_frozen` | Produktionsdatum + Gefrierzeit |
| `homemade_preserved` | Produktionsdatum + Haltbarkeit |

**Details:** [docs/data-model.md](docs/data-model.md)

### Rollen (2 Stück)

- **admin** - Voller Zugriff (Benutzer, Kategorien, Lagerorte)
- **user** - Items lesen/schreiben

---

## Mobile-First Entwicklung

**WICHTIG**: Fuellhorn ist für Smartphone-Nutzung optimiert!

- **Touch-optimierte Buttons**: min. 48x48px
- **Bottom Navigation** statt Sidebar
- **Card Layout** statt Tabellen
- **Bottom Sheets** statt Center-Modals

**Details:** [docs/UI_KONZEPT.md](docs/UI_KONZEPT.md)

---

## Detaillierte Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/TESTING.md](docs/TESTING.md) | Test-Strategie, Fixtures, E2E Tests |
| [docs/requirements.md](docs/requirements.md) | Produkt-Anforderungen, Use Cases, MVP |
| [docs/data-model.md](docs/data-model.md) | Datenmodell, Entitäten, Beziehungen |
| [docs/UI_KONZEPT.md](docs/UI_KONZEPT.md) | Mobile-First UI/UX, Wireframes |
| [docs/tech-stack.md](docs/tech-stack.md) | Tech-Stack, Projektstruktur |
| [docs/shelf-life-defaults.md](docs/shelf-life-defaults.md) | Standard-Haltbarkeiten |

---

## Schnellreferenz

### Häufige Befehle

```bash
# App starten
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

### Agent-Workflow (Kurzform)

```bash
# 1. Issue holen (MCP oder manuell)
gh issue list --label "status/agent-ready"

# 2. Worktree erstellen
git pull origin main
git worktree add worktrees/issue-<N> -b feature/issue-<N>-<kurz>
cd worktrees/issue-<N>

# 3. TDD implementieren
# Test → Rot → Code → Grün → Refactor

# 4. Qualitätsprüfung
uv run pytest && uv run mypy app/ && uv run ruff check app/

# 5. Commit & PR
git add . && git commit -m "feat: <beschreibung>"
git push -u origin feature/issue-<N>-<kurz>
gh pr create --title "feat: <titel>" --body "closes #<N>"

# 6. Nach Merge aufräumen (vom Hauptrepo)
git worktree remove worktrees/issue-<N>
```

### Agent-Regeln

- ✅ Nur am zugewiesenen Issue arbeiten
- ✅ Tests sind Pflicht
- ✅ Kleine, häufige Commits
- ✅ PR erstellen wenn fertig
- ❌ Keine anderen Dateien ändern als nötig
- ❌ Keine "Verbesserungen" ohne Issue
- ❌ Nicht auf main pushen
