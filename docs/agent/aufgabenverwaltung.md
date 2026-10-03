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

Blockierte Issues tragen das Label `status/blocked`. Wenn der Blocker geschlossen ist, Label manuell entfernen und `status/agent-ready` setzen (keine Automatisierung vorhanden).

### Epics und Sub-Issues

**Epics** (`type/epic` Label) werden **nicht direkt bearbeitet**. Stattdessen:
- Sub-Issues haben `Part of #<epic>` im Body
- Epic manuell schließen, wenn alle Sub-Issues geschlossen sind

### Arbeiten mit der gh CLI

Alle GitHub-Operationen laufen über die `gh` CLI (authentifiziert via `gh auth login`).

| Aufgabe | Befehl |
|---------|--------|
| Agent-ready Issues anzeigen | `gh issue list --label status/agent-ready` |
| Issue lesen | `gh issue view <nr> --comments` |
| Issue übernehmen | `gh issue edit <nr> --remove-label status/agent-ready --add-label status/in-progress` |
| Issue anlegen | `gh issue create --title "fix: ..." --body-file body.md --label type/bug` |
| Kommentar schreiben | `gh issue comment <nr> --body "..."` |
| PR erstellen | `gh pr create --fill` (Body mit `closes #<nr>`) |

Interaktive Auswahl inkl. Briefing: `./scripts/select-next-task.sh`

**Typischer Workflow:**
1. `gh issue list --label status/agent-ready` → Verfügbare Issues sehen
2. `gh issue view <nr>` → Beschreibung und Akzeptanzkriterien lesen
3. Label auf `status/in-progress` setzen, Worktree anlegen
4. Implementieren (TDD!)
5. PR erstellen mit `closes #<nr>`
6. Nach Merge: Worktree entfernen, Label `status/in-progress` entfernen
