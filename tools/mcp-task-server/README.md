# Fuellhorn Task MCP Server

MCP Server für GitHub Issue Task Management. Ermöglicht Claude Code Agents selbstständig Issues auszuwählen und Briefings abzurufen.

## Installation

### 1. Dependencies installieren

```bash
cd tools/mcp-task-server
uv sync
```

### 2. MCP Server in Claude Code aktivieren

```bash
claude mcp add fuellhorn-tasks \
  --transport stdio \
  -s user \
  -e FUELLHORN_REPO=jensens/fuellhorn \
  -- uv run --directory /home/jensens/ws/jwk/fuellhorn/tools/mcp-task-server python server.py
```

**Wichtig:** Nach dem Hinzufügen muss eine **neue Claude Code Session** gestartet werden (bestehende Sessions laden den Server nicht nach).

### 3. Aktivierung prüfen

```bash
claude mcp list
```

Sollte zeigen: `fuellhorn-tasks: ✓ Connected`

### Server entfernen

```bash
claude mcp remove fuellhorn-tasks -s user
```

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `list_ready_issues` | Liste agent-ready Issues (ohne Epics!) |
| `list_inprogress_issues` | Liste in-progress Issues (ohne Epics) |
| `list_epics` | Liste Epics mit Sub-Issue Fortschritt |
| `get_issue_details` | Issue-Details abrufen |
| `get_issue_briefing` | Briefing mit Worktree-Anweisungen |
| `assign_issue` | Issue zuweisen (Labels aktualisieren) |
| `list_dependent_issues` | Abhängige Issues finden |
| `complete_issue` | Nach PR-Merge aufräumen |

## Epics und Sub-Issues

**Epics** sind übergeordnete Issues mit Label `type/epic`. Sie werden **nicht direkt bearbeitet** - stattdessen werden ihre Sub-Issues einzeln abgearbeitet.

### Konvention für Sub-Issues

Sub-Issues müssen im Body folgende Zeile enthalten:

```
Part of #<epic-nummer>
```

Beispiel:
```
Part of #42
```

### Automatisches Verhalten

- **Epics erscheinen NICHT in `list_ready_issues`** - Agents arbeiten nur an Sub-Issues
- **Epics bekommen NIE das Label `status/agent-ready`**
- **Wenn alle Sub-Issues geschlossen sind**, wird das Epic automatisch geschlossen
- Der CI-Workflow überwacht dies und kommentiert: `🎉 Epic automatisch geschlossen`

## Konfiguration

### GitHub Token

Der Server benötigt Zugriff auf die GitHub API. Optionen:

1. **Environment Variable:** `GITHUB_TOKEN`
2. **gh CLI:** Falls `gh auth login` ausgeführt wurde, wird das Token automatisch verwendet

## Lokales Testen

```bash
cd tools/mcp-task-server
uv run mcp dev server.py
```

Öffnet eine Web-UI zum Testen der Tools.

## Verwendung in Claude Code

Nach Aktivierung des MCP Servers kann ein Agent:

```
1. list_ready_issues aufrufen um verfügbare Issues zu sehen
2. get_issue_briefing für ein Issue aufrufen
3. assign_issue um das Issue zu übernehmen
4. Nach Abschluss: complete_issue aufrufen
```

## Beispiel-Prompts für Agents

### Neues Issue übernehmen

```
Zeige mir die verfügbaren Issues mit list_ready_issues.
Dann hole mir das Briefing für Issue #42 und weise es mir zu.
```

### Issue-Status prüfen

```
Welche Issues sind gerade in Bearbeitung?
Zeige mir auch welche Issues von Issue #42 abhängen.
```

### Nach PR-Merge aufräumen

```
Mein PR für Issue #42 wurde gemerged.
Rufe complete_issue auf und zeige mir die Aufräum-Anweisungen.
```

### Selbstständig nächstes Issue bearbeiten

```
Finde das nächste verfügbare Issue mit der höchsten Priorität.
Hole das Briefing, weise es mir zu und erstelle den Worktree.
Dann implementiere das Feature nach TDD.
```

### Issue-Details verstehen

```
Zeige mir die Details zu Issue #42 und liste alle abhängigen Issues auf.
```
