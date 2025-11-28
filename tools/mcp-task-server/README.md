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
