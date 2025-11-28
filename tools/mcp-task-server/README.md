# Fuellhorn Task MCP Server

MCP Server für GitHub Issue Task Management. Ermöglicht Claude Code Agents selbstständig Issues auszuwählen und Briefings abzurufen.

## Installation

```bash
cd tools/mcp-task-server
uv sync
```

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `list_ready_issues` | Liste agent-ready Issues |
| `list_inprogress_issues` | Liste in-progress Issues |
| `get_issue_details` | Issue-Details abrufen |
| `get_issue_briefing` | Briefing mit Worktree-Anweisungen |
| `assign_issue` | Issue zuweisen (Labels aktualisieren) |
| `list_dependent_issues` | Abhängige Issues finden |
| `complete_issue` | Nach PR-Merge aufräumen |

## Konfiguration

Der Server ist in `.mcp.json` im Projekt-Root konfiguriert und wird automatisch von Claude Code erkannt.

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
