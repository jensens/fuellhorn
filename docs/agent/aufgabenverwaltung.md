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
