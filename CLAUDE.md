# Entwicklungsregeln für Fuellhorn

Diese Datei enthält wichtige Regeln und Richtlinien für die Entwicklung dieses Projekts.

## Lizenz

**Füllhorn ist lizenziert unter AGPL-3.0-or-later (GNU Affero General Public License v3.0 oder später).**

### Warum AGPLv3?

Die AGPLv3 wurde gewählt, weil:

1. **Self-Hosted Web Application**: Füllhorn ist eine netzwerkbasierte Anwendung, die als Webservice gehostet wird. Die AGPL stellt sicher, dass Änderungen am Code mit der Community geteilt werden müssen, auch wenn die Software nur als SaaS bereitgestellt wird (ohne Binär-Distribution).

2. **Community-getriebene Entwicklung**: Die Copyleft-Lizenz fördert Beiträge zurück zur Community und verhindert proprietäre Forks.

3. **Dependency-Kompatibilität**: Alle verwendeten Dependencies (MIT, Apache 2.0, BSD, LGPL) sind mit AGPLv3 kompatibel.

### Was bedeutet das für Entwickler?

- **Eigene Änderungen**: Wenn du Füllhorn modifizierst und die modifizierte Version als Webservice hostest, musst du den Quellcode deiner Änderungen verfügbar machen.
- **Beiträge zum Projekt**: Alle Contributions zu diesem Repository werden automatisch unter AGPLv3 lizenziert.
- **Private Nutzung**: Du kannst Füllhorn für private/interne Zwecke nutzen, ohne den Code teilen zu müssen, solange du es nicht als Service für Dritte anbietest.

Siehe [LICENSE](LICENSE) für den vollständigen Lizenztext.

---

## Grundprinzipien

### 1. Test-Driven Development (TDD)

**WICHTIG**: Tests sind obligatorisch und müssen immer GRÜN sein!

**Bevor du Tests schreibst oder änderst, lies TESTING.md!**

➡️ **[TESTING.md](TESTING.md)** - Vollständige Test-Strategie und Best Practices

- **Jede neue Funktion benötigt Tests** - keine Implementierung ohne Tests
- **Tests müssen vor dem Commit grün sein** - niemals mit roten Tests committen
- **Test-First Ansatz bevorzugt**:
  1. Test schreiben
  2. Test läuft rot (schlägt fehl)
  3. Implementierung schreiben
  4. Test läuft grün
  5. Refactoring (falls nötig)
- **Mindest-Coverage**: 80% Code-Coverage anstreben
- **Test-Typen**:
  - Unit-Tests für Models und Services
  - Integration-Tests für Datenbank-Operationen
  - **UI-Tests sind Pflicht** mit NiceGUI Testing Framework
- **Test-Isolation**: NIEMALS die globale Datenbank verwenden! Siehe [TESTING.md](TESTING.md)

**Tests ausführen**:
```bash
uv run pytest                          # Alle Tests
uv run pytest --cov=app --cov-report=html  # Mit Coverage-Report
uv run pytest tests/test_models.py     # Spezifische Test-Datei
```

---

### 2. Code-Qualität

#### Type Checking (mypy)

- **Alle Python-Dateien müssen Type Hints haben**
- **mypy muss ohne Fehler durchlaufen**
- Type Hints für:
  - Funktionsparameter
  - Rückgabewerte
  - Klassenvariablen
  - Wichtige lokale Variablen

```bash
uv run mypy app/
```

#### Linting (ruff)

- **Code muss ruff-Standards erfüllen**
- **Keine Linter-Fehler erlaubt** vor Commit
- Ruff konfiguriert in `pyproject.toml`

```bash
uv run ruff check app/              # Check
uv run ruff check --fix app/        # Auto-Fix
uv run ruff format app/             # Formatierung
```

**Workflow vor jedem Commit**:
```bash
# 1. Tests
uv run pytest

# 2. Type Check
uv run mypy app/

# 3. Linting
uv run ruff check app/
uv run ruff format app/

# Erst wenn alles grün ist → Commit!
```

---

### 3. Git Commit-Strategie

#### ⚠️ WICHTIG: Git Worktrees für parallele Entwicklung

**IMMER Git Worktrees verwenden!**

Git Worktrees erlauben es, mehrere Working Directories für das gleiche Repository zu haben. Das verhindert Konflikte, wenn mehrere Agents gleichzeitig am selben Projekt arbeiten.

**Problem ohne Worktrees:**
- Zwei Agents arbeiten im gleichen Working Directory
- Beide ändern Dateien und wollen committen
- Git-Konflikte und Race Conditions entstehen
- Pre-commit Hooks können fehlschlagen
- Dateien können überschrieben werden

**Lösung mit Worktrees:**

```bash
# Haupt-Repository (main branch)
cd /path/to/fuellhorn

# Worktree für Agent 1 erstellen (z.B. für Feature-Entwicklung)
git worktree add worktrees/agent1 -b feature/new-feature

# Worktree für Agent 2 erstellen (z.B. für Bugfix)
git worktree add worktrees/agent2 -b fix/bug-123

# Jeder Agent arbeitet in seinem eigenen Directory:
# - fuellhorn/              (main branch)
# - fuellhorn/worktrees/agent1/  (feature/new-feature branch)
# - fuellhorn/worktrees/agent2/  (fix/bug-123 branch)
```

**Best Practices:**
- **Einen Worktree pro Agent/Task** erstellen
- **Eigener Branch pro Worktree** (nicht main!)
- **Worktree löschen** nach Merge: `git worktree remove worktrees/agent1`
- **Worktrees auflisten**: `git worktree list`

**Wichtig für Claude Code Agents:**
- Starte jeden Agent in seinem eigenen Worktree-Verzeichnis
- Nutze separate Branches für verschiedene Tasks
- Merge später über Pull Requests zusammen

#### GitHub Issues als Aufgabenverwaltung

**Alle Aufgaben werden über GitHub Issues verwaltet!**

- **Issues ansehen:** https://github.com/jensens/fuellhorn/issues
- **Milestones:** Alpha → Beta → v1.0
- **Agent-ready Issues:** Label `status/agent-ready` zeigt sofort bearbeitbare Tasks

#### Issue-Abhängigkeiten (Blocked by)

**Konvention für Issue-Dependencies:**

Issues können auf andere Issues warten. Das Format im Issue-Body:
```
Blocked by #42
Blocked by #43
```

**Automatische Freischaltung:**
- GitHub Action `.github/workflows/unlock-issues.yml` überwacht Issue-Close-Events
- Wenn ein Issue geschlossen wird, werden alle abhängigen Issues geprüft
- Wenn alle Blocker geschlossen sind → `status/blocked` wird entfernt, `status/agent-ready` wird gesetzt
- Ein Kommentar "🔓 Automatisch freigeschaltet durch Abschluss von #X" wird hinzugefügt

**Labels für Status:**
- `status/agent-ready` - Issue kann sofort bearbeitet werden
- `status/in-progress` - Agent arbeitet gerade daran
- `status/blocked` - Wartet auf andere Issues

**Wichtig für neue Issues:**
- Bei Features mit Dependencies: Im Issue-Template das "Blockiert durch" Feld ausfüllen
- Format muss exakt sein: `Blocked by #XX` (case-insensitive)
- Mehrere Blocker: Eine Zeile pro Blocker
- **NICHT** das Header-Format verwenden (`## Blocked by` + Bullet-Liste) - das wird nicht erkannt!

**Workflow für Agents:**
```bash
# 1. Issue auswählen
gh issue list --label "status/agent-ready"

# 2. Worktree für Issue erstellen (im worktrees/ Unterordner, gitignored)
git worktree add worktrees/issue-<number> -b feature/issue-<number>-<kurzbeschreibung>

# 3. In Worktree wechseln
cd worktrees/issue-<number>

# 4. Implementieren (TDD!)

# 5. PR erstellen mit "closes #<number>"
gh pr create --title "feat: <Beschreibung>" --body "closes #<number>"

# 6. Nach Merge aufräumen (vom Hauptrepo aus)
git worktree remove worktrees/issue-<number>
```

#### Mensch-Agent Workflow

**Übersicht der Zusammenarbeit zwischen Projektmanager (Mensch) und implementierenden Agenten:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROJEKT-ZYKLUS                                     │
│                                                                             │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│   │ PLANEN  │ ───▶ │ ZUWEISEN│ ───▶ │ARBEITEN │ ───▶ │ REVIEW  │ ───▶ ↻    │
│   │ (Mensch)│      │ (Mensch)│      │ (Agent) │      │ (Mensch)│           │
│   └─────────┘      └─────────┘      └─────────┘      └─────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

##### Phase 1: Planung (Mensch/PM)

**Wann:** Vor Beginn eines Sprints oder bei Bedarf

**Aufgaben:**
1. **Project Board prüfen:** https://github.com/users/jensens/projects/2
2. **Prioritäten setzen:** Issues nach Wichtigkeit sortieren
3. **Dependencies klären:** Welche Issues können parallel bearbeitet werden?
4. **Milestones zuweisen:** Alpha → Beta → v1.0

**Befehle:**
```bash
# Offene Issues nach Milestone anzeigen
gh issue list --milestone "Alpha" --state open

# Issue-Details ansehen
gh issue view <number>

# Priorität setzen (via Label)
gh issue edit <number> --add-label "priority/high"
```

---

##### Phase 2: Zuweisung (Mensch/PM)

**Wann:** Wenn ein Agent bereit für neue Arbeit ist

**Workflow:**
1. **Issue auswählen** das keine Blocker hat
2. **Label setzen:** `status/agent-ready` → `status/in-progress`
3. **Agent briefen** mit Issue-Nummer und Kontext

**Befehle:**
```bash
# Issue für Agent vorbereiten
gh issue edit <number> --remove-label "status/agent-ready"
gh issue edit <number> --add-label "status/in-progress"

# Agent starten mit Issue-Kontext
# (In neuem Terminal/Worktree)
cd /path/to/fuellhorn
git worktree add worktrees/issue-<number> -b feature/issue-<number>-<kurz>
cd worktrees/issue-<number>
```

**Briefing-Template für Agent:**
```
Bitte implementiere Issue #<number>: <Titel>

Kontext:
- Beschreibung: <gh issue view <number>>
- Abhängigkeiten: <falls vorhanden>
- Akzeptanzkriterien: <aus Issue-Body>

Wichtig:
- Lies CLAUDE.md und TESTING.md
- TDD: Tests zuerst
- PR erstellen mit "closes #<number>"
```

---

##### Phase 3: Implementierung (Agent)

**Wann:** Nach Briefing durch PM

**Agent-Workflow:**
```bash
# 1. Issue lesen und verstehen
gh issue view <number>

# 2. Worktree erstellen (im worktrees/ Unterordner)
git worktree add worktrees/issue-<number> -b feature/issue-<number>-<kurz>
cd worktrees/issue-<number>

# 3. TDD-Zyklus
#    a) Test schreiben
#    b) Test läuft rot
#    c) Implementieren
#    d) Test läuft grün
#    e) Refactoring

# 4. Qualitätsprüfung
uv run pytest
uv run mypy app/
uv run ruff check app/
uv run ruff format app/

# 5. Commit(s) erstellen
git add .
git commit -m "feat: <Beschreibung>

closes #<number>"

# 6. Push und PR erstellen
git push -u origin feature/issue-<number>-<kurz>
gh pr create --title "feat: <Beschreibung>" --body "closes #<number>

## Änderungen
- ...

## Tests
- [ ] Unit Tests
- [ ] UI Tests (falls relevant)"
```

**Agent-Regeln:**
- ✅ Nur am zugewiesenen Issue arbeiten
- ✅ Tests sind Pflicht
- ✅ Kleine, häufige Commits
- ✅ PR erstellen wenn fertig
- ❌ Keine anderen Dateien ändern als nötig
- ❌ Keine "Verbesserungen" ohne Issue
- ❌ Nicht auf main pushen

---

##### Phase 4: Review (Mensch/PM)

**Wann:** Nach PR-Erstellung durch Agent

**Review-Workflow:**
```bash
# 1. PR ansehen
gh pr view <pr-number>
gh pr diff <pr-number>

# 2. CI-Status prüfen
gh pr checks <pr-number>

# 3. Lokal testen (optional)
gh pr checkout <pr-number>
uv run pytest
uv run python main.py  # Manueller Test

# 4a. Wenn OK → Merge
gh pr merge <pr-number> --squash --delete-branch

# 4b. Wenn Änderungen nötig → Kommentar
gh pr comment <pr-number> --body "Bitte folgende Änderungen:
- ...
- ..."
```

**Nach Merge:**
```bash
# Worktree aufräumen (vom Hauptrepo aus)
git worktree remove worktrees/issue-<number>

# Project Board aktualisiert sich automatisch
# (Issue wird geschlossen durch "closes #<number>")
# Abhängige Issues werden automatisch freigeschaltet (GitHub Action)
```

---

##### Parallele Agenten-Arbeit

**Bis zu 4 Agenten können parallel arbeiten:**

```
Terminal 1 (PM):           fuellhorn/                    (main, Übersicht)
Terminal 2 (Agent 1):      fuellhorn/worktrees/issue-7/  (feature/issue-7-...)
Terminal 3 (Agent 2):      fuellhorn/worktrees/issue-8/  (feature/issue-8-...)
Terminal 4 (Agent 3):      fuellhorn/worktrees/issue-18/ (feature/issue-18-...)
```

**Regeln für Parallelität:**
1. **Unabhängige Issues wählen** - keine gemeinsamen Dateien
2. **Ein Agent pro Issue** - keine Überschneidungen
3. **PM koordiniert** - verhindert Konflikte
4. **Sequentiell mergen** - einer nach dem anderen

**Konflikt-Vermeidung:**
```bash
# Vor PR: main aktualisieren
git fetch origin
git rebase origin/main

# Bei Konflikten: PM entscheidet Reihenfolge
```

---

##### Kommunikation

**PM → Agent:**
- Issue-Nummer + Briefing
- Review-Kommentare auf PR
- Änderungswünsche via `gh pr comment`

**Agent → PM:**
- PR-Erstellung signalisiert "fertig"
- Fragen als Kommentar auf Issue/PR
- Blocker sofort melden

**Asynchrone Kommunikation:**
- Alles über GitHub (Issues, PRs, Comments)
- Keine direkte Chat-Kommunikation nötig
- Vollständige Nachvollziehbarkeit

---

##### Project Board Workflow

**Board:** https://github.com/users/jensens/projects/2

| Spalte | Bedeutung | Wer bewegt |
|--------|-----------|------------|
| **Todo** | Geplante Issues | PM |
| **In Progress** | Agent arbeitet daran | PM (bei Zuweisung) |
| **Done** | Implementiert & gemerged | Automatisch (via PR) |

**PM-Aufgaben am Board:**
```bash
# Issue in "In Progress" verschieben (manuell im UI oder via API)
# Nach Zuweisung an Agent

# Spalten anpassen falls nötig (im UI):
# - "Review" hinzufügen für PR-Phase
# - "Blocked" für blockierte Issues
```

---

##### Typischer Tagesablauf

**Morgens (PM):**
1. Project Board prüfen
2. Gestrige PRs reviewen und mergen
3. Neue Issues für Agents vorbereiten

**Tagsüber (Agents):**
1. Briefing vom PM erhalten
2. Issue implementieren (TDD)
3. PR erstellen
4. Auf Review warten

**Abends (PM):**
1. PRs reviewen
2. Feedback geben oder mergen
3. Nächste Issues priorisieren

---

##### Checkliste für PM

**Vor Agent-Start:**
- [ ] Issue existiert und ist klar beschrieben
- [ ] Dependencies sind erfüllt oder nicht vorhanden
- [ ] Label `status/agent-ready` gesetzt
- [ ] Milestone zugewiesen

**Bei Zuweisung:**
- [ ] Worktree erstellt oder Agent instruiert
- [ ] Label auf `status/in-progress` geändert
- [ ] Agent mit Issue-Nummer gebrieft

**Nach PR:**
- [ ] CI ist grün
- [ ] Code-Review durchgeführt
- [ ] Tests vorhanden und sinnvoll
- [ ] PR gemerged oder Feedback gegeben

**Nach Merge:**
- [ ] Issue automatisch geschlossen (via "closes #X")
- [ ] Worktree aufgeräumt
- [ ] Nächstes Issue bereit?

---

##### Issue-Abhängigkeiten & Reihenfolge

**Wie finde ich das nächste Issue?**

**Empfohlen: Interaktives Script verwenden:**
```bash
./scripts/select-next-task.sh
```

Das Script bietet:
- Liste aller agent-ready Issues
- Issue-Details auf Knopfdruck
- Automatische Label-Aktualisierung
- Briefing-Prompt für Agent
- Übersicht der abhängigen Issues

**Alternativ manuell:**
```bash
# Alle sofort bearbeitbaren Issues anzeigen
gh issue list --label "status/agent-ready" --state open

# Nach Merge: Folge-Issues prüfen
gh issue view <number>  # Schau in "Blocked by" Sektion
```

**Regel:** Ein Issue ist `agent-ready` wenn alle "Blocked by" Issues geschlossen sind.

---

**Dependency-Graph (Übersicht):**

```
Sprint 1: Kern-UI
═══════════════════════════════════════════════════════════════

  #7 Item Card ─────┐
                    ├──▶ #9 Items Page ──▶ #10 Suche
  #8 Expiry Badge ──┘         │            #11 Filter Kat.
                              │            #12 Filter Ort
                              │            #13 Sortierung
                              │
  #18 Logout Button ──▶ #19 Session Cleanup

Sprint 2: Entnahme
═══════════════════════════════════════════════════════════════

  #14 Bottom Sheet ──┬──▶ #15 Komplett entnehmen ──▶ #17 Ausblenden
                     │
                     └──▶ #16 Teilentnahme

Sprint 3: Admin Pages (parallel!)
═══════════════════════════════════════════════════════════════

  #20 Categories Liste ──▶ #21 Erstellen
                           #22 Bearbeiten
                           #23 Löschen

  #24 Locations Liste ──▶ #25 Erstellen
                          #26 Bearbeiten
                          #27 Löschen

  #28 Users Liste ──▶ #29 Erstellen
                      #30 Bearbeiten
                      #31 Löschen

  #32 Settings Liste ──▶ #33 Gefrierzeit Edit
                         #34 Smart Defaults

Sprint 4: Finalisierung
═══════════════════════════════════════════════════════════════

  #35 Rate-Limiting (standalone)
  #36 Audit-Logging (standalone)

  #37 Dockerfile ──▶ #38 docker-compose ──▶ #39 Docs
```

---

**Start-Issues (sofort bearbeitbar):**

| # | Titel | Parallel mit |
|---|-------|--------------|
| **#7** | Item Card Komponente | #8, #14, #18 |
| **#8** | Expiry Badge Komponente | #7, #14, #18 |
| **#14** | Bottom Sheet Komponente | #7, #8, #18 |
| **#18** | Logout-Button | #7, #8, #14 |
| **#20** | Categories Liste | #24, #28, #32 |
| **#24** | Locations Liste | #20, #28, #32 |
| **#28** | Users Liste | #20, #24, #32 |
| **#32** | Settings Liste | #20, #24, #28 |
| **#35** | Rate-Limiting | #36, #37 |
| **#36** | Audit-Logging | #35, #37 |
| **#37** | Dockerfile | #35, #36 |

---

**Nach Issue-Abschluss - Was kommt als nächstes?**

| Wenn erledigt | Dann freigeben | Label setzen |
|---------------|----------------|--------------|
| #7 + #8 | #9 | `status/agent-ready` |
| #9 | #10, #11, #12, #13 | alle `status/agent-ready` |
| #14 | #15, #16 | beide `status/agent-ready` |
| #15 | #17 | `status/agent-ready` |
| #18 | #19 | `status/agent-ready` |
| #20 | #21, #22, #23 | alle `status/agent-ready` |
| #24 | #25, #26, #27 | alle `status/agent-ready` |
| #28 | #29, #30, #31 | alle `status/agent-ready` |
| #32 | #33, #34 | beide `status/agent-ready` |
| #37 | #38 | `status/agent-ready` |
| #38 | #39 | `status/agent-ready` |

**Befehl zum Freigeben:**
```bash
gh issue edit <number> --add-label "status/agent-ready"
```

---

#### Häufige, kleine Commits

- **Commit oft** - lieber zu viele als zu wenige Commits
- **Commits sollen klein sein** - eine logische Änderung pro Commit
- **Jeder Commit sollte kompilieren und Tests bestehen**

#### Commit-Message Format

```
<typ>: <kurze Beschreibung>

<optionale längere Beschreibung>

disclosure: generated with Claude Code
```

**Commit-Typen**:
- `feat`: Neues Feature
- `fix`: Bugfix
- `test`: Tests hinzugefügt/geändert
- `refactor`: Code-Refactoring
- `docs`: Dokumentation
- `chore`: Build, Dependencies, Config

**Beispiele**:
```bash
git commit -m "feat: Item Model mit 5 Artikel-Typen implementiert"
git commit -m "test: Unit-Tests für Expiry Calculator"
git commit -m "fix: Gefrierzeit-Berechnung für homemade_frozen"
```

#### Workflow

1. Feature-Branch erstellen (optional)
2. Kleine Änderung implementieren
3. Tests schreiben/anpassen
4. Tests laufen lassen → grün
5. Type Check → sauber
6. Linting → sauber
7. Commit
8. Wiederholen

---

### 4. Tidy First & Commit Discipline

**WICHTIG**: Strukturelle und verhaltensändernde Änderungen NIEMALS mischen!

Nach Kent Beck's "Tidy First" Ansatz - strukturelle Änderungen von verhaltensändernden Änderungen trennen:

#### Arten von Änderungen

1. **Strukturelle Änderungen (Structural)**: Refactoring ohne Verhaltensänderung
   - Umbenennen von Variablen/Funktionen/Klassen
   - Methoden extrahieren
   - Duplikation entfernen
   - Code-Organisation verbessern
   - Import-Sortierung

2. **Verhaltensändernde Änderungen (Behavioral)**: Funktionalität hinzufügen/ändern
   - Neue Features
   - Bug Fixes
   - Logik-Änderungen
   - Neue Validierungen

#### Commit-Regeln

- **NIE strukturelle und verhaltensändernde Änderungen mischen** im selben Commit
- **Strukturelle Änderungen zuerst** - Aufräumen vor dem Feature-Add
- **Ein Commit = Ein Änderungstyp**

**Commit-Message Format**:
```
# Strukturell
refactor: extract expiry calculation into separate module

# Verhaltensändernd
feat: add freeze time configuration for categories
fix: prevent negative quantities in item creation
```

#### Wann committen?

**NUR wenn ALLE Bedingungen erfüllt sind**:
1. ✅ Alle Tests bestehen (außer bekannte Long-Running-Tests)
2. ✅ Alle Linter-Warnungen behoben
3. ✅ Alle Type-Checker-Fehler behoben
4. ✅ Die Änderung repräsentiert eine logische Einheit
5. ✅ Self-Review der Diff durchgeführt

**Häufige, kleine Commits sind besser als große!**
- Wenn etwas funktioniert → sofort committen als Safety-Checkpoint
- Lieber 10 kleine Commits als 1 großer
- Jeder Commit sollte die Codebasis in einem funktionierenden Zustand hinterlassen

---

### 5. Code Quality Standards

#### Einfachheit (Simplicity)

- **Die einfachste Lösung, die funktionieren könnte**
- **YAGNI** (You Aren't Gonna Need It) - nur implementieren was jetzt gebraucht wird
- **Keine vorzeitige Optimierung** - zuerst funktionstüchtig, dann optimieren
- **Toten Code sofort löschen** - kein auskommentierter Code

#### Klarheit (Clarity)

- **Namen offenbaren Absicht** - keine kryptischen Variablennamen
- **Funktionen tun eine Sache** - Single Responsibility
- **Lesbarkeit vor Cleverness** - optimiere für den nächsten Entwickler
- **Dependencies explizit machen** - keine versteckten Abhängigkeiten
- **Fail Fast and Loud** - mit klaren Fehlermeldungen

#### Refactoring-Trigger

**Refactoring durchführen wenn du siehst**:

1. **Duplikation** - Rule of Three: beim dritten Kopieren refactorn
2. **Lange Methoden** - >20 Zeilen ist verdächtig
3. **Zu viele Parameter** - >3 Parameter riecht nach Problem
4. **Erklärende Kommentare** - Code sollte selbsterklärend sein
5. **Verschachtelte Conditionals** - in Methoden extrahieren

#### Kommentare

- **Kommentare erklären WARUM, nicht WAS**
- **Fokus auf aktuelles Verhalten**, nicht auf Historie
- **Veraltete Kommentare sofort löschen**
- **Bevorzuge selbstdokumentierenden Code** über Kommentare

---

## Projekt-spezifische Regeln

### Mobile-First Development

**WICHTIG**: Fuellhorn ist für mobile/Smartphone-Nutzung optimiert!

- **Touch-optimierte Buttons**: Mindestens 48x48px Klickfläche
- **Bottom Navigation**: Statt Desktop-Sidebar (4 Items: Übersicht, Erfassen, Vorrat, Mehr)
- **Card Layout**: Statt Tabellen für bessere mobile UX
- **Bottom Sheets**: Statt Center-Modals für Dialogs
- **Infinite Scroll**: Keine Pagination-Buttons, kontinuierliches Scrollen
- **Responsive Testing**: Immer in mobiler Ansicht testen (Chrome DevTools)

### NiceGUI Best Practices

- **`on_change` für Input-Events** verwenden (nicht `.on("input")`)
- **Date Picker**: Menu-Pattern mit `ui.menu()` und `bind_value()` verwenden
- **Storage**: `app.storage.user` nur im UI-Kontext verfügbar
- **Browser Storage**: `app.storage.browser` für Smart Defaults (persistiert über Sessions)
- **Testing**: User-Fixture von `nicegui.testing.plugin` verwenden
- **Relative Imports**: Innerhalb von `app/` immer relative Imports verwenden

### Smart Defaults (Browser Storage)

**Wichtig für UX**: Smart Defaults mit Zeitfenstern implementieren!

```python
# Browser Storage Struktur
{
  "last_item_entry": {
    "timestamp": "2025-11-24T15:30:00",
    "item_type": "purchased_then_frozen",
    "location_id": 3,
    "category_ids": [1, 5],
    "unit": "g",
    "last_date": "2025-11-24"
  },
  "preferences": {
    "item_type_time_window": 30,    # Minuten
    "category_time_window": 30,     # Minuten
    "location_time_window": 60,     # Minuten
    "date_time_window": 30          # Minuten
  }
}
```

**Smart Default Logik**:
1. **Artikel-Typ**: Default "purchased_fresh" (>90%), bei < 30 Min → letzter Typ
2. **Produktions-/Einfrierdatum**: Default "heute", bei < 30 Min → letztes Datum
3. **Lagerort**: Bei < 60 Min → letzter Lagerort, sonst erster in Liste
4. **Kategorien**: Bei < 30 Min → letzte Kategorien, sonst leer
5. **Einheit**: Immer letzte Einheit, Default "g"

**Implementierung**:
- Nach jedem Item-Save → Browser Storage aktualisieren mit Timestamp
- Beim Laden des Erfassen-Formulars → Zeitfenster prüfen
- Zeitfenster konfigurierbar in Settings

### Architektur

**3-Schichten-Modell einhalten**:

1. **Models** (Data Layer) - `app/models/`
   - `user.py` - User mit Rollen (2 Rollen: admin, user)
   - `item.py` - Vorratsartikel (5 Artikel-Typen)
   - `category.py` - Kategorien/Tags (flache Struktur)
   - `location.py` - Lagerorte (frozen/chilled/ambient)
   - `freeze_time_config.py` - Gefrierzeit-Konfiguration
   - `audit_log.py` - Audit-Protokoll

2. **Services** (Business Logic) - `app/services/`
   - `auth_service.py` - Authentication & User Management (von VellenBase)
   - `item_service.py` - Item CRUD & Withdrawal
   - `category_service.py` - Category Management
   - `location_service.py` - Location Management
   - `expiry_calculator.py` - Haltbarkeitsberechnung (Kernlogik!)
   - `freeze_time_service.py` - Gefrierzeit-Konfiguration

3. **UI** (Presentation) - `app/ui/`
   - `auth.py` - Login/Logout mit Session Management (von VellenBase anpassen)
   - `layout.py` - Hauptlayout mit Bottom Navigation (mobile-first!)
   - `pages/` - Einzelne Seiten
     - `dashboard.py` - Dashboard mit Ablaufübersicht (rot/gelb/grün)
     - `items.py` - Vorratsliste (Card Layout, Infinite Scroll)
     - `add_item.py` - Artikel-Erfassung (3-Step Wizard mit Smart Defaults)
     - `categories.py` - Kategorie-Verwaltung (Admin)
     - `locations.py` - Lagerort-Verwaltung (Admin)
     - `users.py` - Benutzer-Verwaltung (Admin, von VellenBase)
     - `settings.py` - Gefrierzeit-Konfiguration & Smart Default Zeitfenster
   - `components/` - Wiederverwendbare UI-Komponenten
     - `item_card.py` - Item als Card mit Expiry-Badge
     - `item_form.py` - Item-Formular (wiederverwendbar)
     - `expiry_badge.py` - Status-Badge (rot/gelb/grün)
     - `bottom_nav.py` - Bottom Navigation Component

4. **Auth** - `app/auth/`
   - `permissions.py` - Permission-Enum + Rolle→Permission Mapping (2 Rollen!)
   - `decorators.py` - `@require_permissions()` für UI Pages
   - `dependencies.py` - DB-backed User-Fetching mit Caching

**Regeln:**
- **Keine Business-Logic in UI-Code**
- **Keine UI-Code in Services**
- **Relative Imports** innerhalb von `app/` (z.B. `from ..models.user import User`)

### Authentication & Authorization

**Decorator-basiertes Permission-System** mit DB-backed Permissions (von VellenBase übernehmen)

#### Architektur

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Roles     │ ──▶ │ Permissions  │ ──▶ │  Decorators │
│ (was User   │     │ (was User    │     │  (schützen  │
│  ist)       │     │  darf)       │     │   Pages)    │
└─────────────┘     └──────────────┘     └─────────────┘
```

#### Role-System (Vereinfacht: 2 Rollen)

```python
from ..models.user import Role, User

# 2 Rollen: admin, user
user = User(role="user")  # Kein JSON-Array, nur ein String!

# Permissions für Fuellhorn
class Permission(str, Enum):
    ADMIN_FULL = "admin:full"
    USER_MANAGE = "user:manage"
    CONFIG_MANAGE = "config:manage"  # Kategorien, Lagerorte, Gefrierzeiten
    ITEMS_READ = "items:read"
    ITEMS_WRITE = "items:write"
```

#### Permission-Mapping

```python
# Admin: Alles
# User: Nur Items lesen/schreiben

def get_permissions_for_user(user: User) -> set[Permission]:
    if user.role == "admin":
        return set(Permission)  # Alle Permissions
    elif user.role == "user":
        return {Permission.ITEMS_READ, Permission.ITEMS_WRITE}
    return set()
```

#### UI Page Protection

```python
from ...auth import Permission, require_permissions

@ui.page("/items")
@require_permissions(Permission.ITEMS_READ)
def items() -> None:
    create_main_layout()
    # User ist authentifiziert UND hat ITEMS_READ Permission
```

#### Session Management

**Lange Sessions für gute UX!**

- **"Angemeldet bleiben" Checkbox** (default: ON)
  - WITH remember-me: 30 Tage Session
  - WITHOUT: 24 Stunden Session
- **Sliding Expiration**: Zeitfenster erneuert sich bei Aktivität

**Session Storage** (`app.storage.user`):
- `authenticated` (bool)
- `user_id` (int)
- `username` (str)
- `remember_me` (bool)

**Rollen werden aus DB geholt** bei jedem Request (wie VellenBase):
```python
from ..auth import get_current_user

current_user = get_current_user(require_auth=True)
# → Holt User aus DB, cached per Request (ContextVar)
```

**Vorteil:** Rollen-Änderungen sofort wirksam, kein Logout nötig!

### Expiry Calculation (Kernlogik!)

**5 Artikel-Typen mit unterschiedlicher Haltbarkeitsberechnung**:

1. **purchased_fresh** (Gekauft, nicht gefroren)
   ```python
   expiry_date = item.best_before_date
   ```

2. **purchased_frozen** (Gekauft, bereits gefroren)
   ```python
   expiry_date = item.best_before_date
   ```

3. **purchased_then_frozen** (Gekauft und eingefroren)
   ```python
   freeze_time = get_freeze_time(item.categories, "purchased_then_frozen")
   expiry_date = item.freeze_date + freeze_time  # Monate
   ```

4. **homemade_frozen** (Selbst hergestellt, gefroren)
   ```python
   freeze_time = get_freeze_time(item.categories, "homemade_frozen")
   expiry_date = item.production_date + freeze_time  # Monate
   ```

5. **homemade_preserved** (Selbst hergestellt, eingemacht)
   ```python
   shelf_life = get_freeze_time(item.categories, "homemade_preserved")
   expiry_date = item.production_date + shelf_life  # Monate
   ```

**Expiry Status**:
```python
days_until_expiry = (expiry_date - today).days

if days_until_expiry < 3:
    status = "critical"  # Rot
elif days_until_expiry < 7:
    status = "warning"   # Gelb
else:
    status = "ok"        # Grün
```

**Service implementieren**:
- `app/services/expiry_calculator.py` - Zentrale Logik
- Keine Duplikation der Berechnungslogik!
- Unit-Tests für alle 5 Typen

### Datenbank

- **SQLModel für alle Models verwenden**
- **Keine Raw-SQL-Queries** (außer wenn absolut notwendig)
- **Alembic Migrations**: Eingerichtet und aktiv
  - Siehe [Datenbank-Migrationen](#datenbank-migrationen) für Befehle
- **SQLite Development, PostgreSQL Production**
  - `DB_TYPE=sqlite` für Development
  - `DB_TYPE=postgresql` für Production (Docker)

### Dependencies

- **Neue Dependencies in `pyproject.toml` hinzufügen** mit `uv add <package>`
- **Begründung für neue Dependency** in Commit-Message
- **Lock-File** (`uv.lock`) automatisch aktualisiert und committen

### Deployment

- **Docker**: `Dockerfile` + `docker-compose.yml` für Self-Hosting
  - PostgreSQL Container
  - App Container mit Alembic Migrations (Init)
  - **MVP**: Sehr einfaches Image, kein Multi-Stage Build, kein Security Hardening
  - **Post-MVP**: Optimierung (Multi-Stage, Security Hardening)
- **Self-Hostable**: Zielgruppe sind Familien, die selbst hosten

### Sicherheit

- **Niemals Secrets im Code** - nur über Environment-Variablen
- **Passwörter immer hashen** (bcrypt)
- **Input-Validierung** mit Pydantic
- **SQL-Injection** durch SQLModel verhindert
- **Audit-Logging**: Alle wichtigen Aktionen loggen
  - Login/Logout
  - Item Created/Updated/Withdrawn
  - User Created/Updated
  - Config Changes

---

## Datenbank-Migrationen

Fuellhorn verwendet **Alembic** für Schema-Migrationen (wie VellenBase).

### Wichtige Befehle

```bash
# Aktuelle Migration-Version anzeigen
uv run alembic current

# Migrations-History anzeigen
uv run alembic history

# Neue Migration erstellen (autogenerate)
uv run alembic revision --autogenerate -m "Beschreibung der Änderung"

# Migration anwenden
uv run alembic upgrade head

# Migration rückgängig machen (eine Version zurück)
uv run alembic downgrade -1
```

### Workflow beim Schema-Ändern

1. **Model ändern** in `app/models/`
2. **Migration generieren**: `uv run alembic revision --autogenerate -m "add column xyz"`
3. **Migration prüfen** in `alembic/versions/` (autogenerate ist nicht perfekt!)
4. **Migration anwenden**: `uv run alembic upgrade head`
5. **Tests anpassen** falls nötig
6. **Commit** mit Migration-Datei

### Deployment

- **Docker**: Migrations werden automatisch beim Startup ausgeführt (Init Container/Script)
- **Lokal**: Manuell `uv run alembic upgrade head` ausführen

---

## Entwicklungsumgebung Setup

### uv installieren

```bash
# uv installieren (einmalig)
curl -LsSf https://astral.sh/uv/install.sh | sh
# oder mit pip: pip install uv
```

### Initiales Setup

```bash
# Python-Version installieren und Virtual Environment anlegen
uv python install 3.14
uv venv

# Dependencies installieren (aus pyproject.toml)
uv sync

# Pre-Commit Hooks (empfohlen)
uv tool install pre-commit
uv run pre-commit install
```

### Dependencies verwalten

```bash
# Production Dependencies hinzufügen
uv add <package-name>

# Development Dependencies hinzufügen
uv add --dev <package-name>

# Dependencies synchronisieren
uv sync
```

---

## Workflow Zusammenfassung

### Neue Feature implementieren

```bash
# 1. Branch (optional)
git checkout -b feature/new-feature

# 2. Tests schreiben
# tests/test_new_feature.py erstellen

# 3. Implementierung
# app/services/new_feature.py implementieren

# 4. Tests ausführen
uv run pytest tests/test_new_feature.py

# 5. Type Check
uv run mypy app/

# 6. Linting
uv run ruff check --fix app/
uv run ruff format app/

# 7. Commit (wenn alles grün)
git add .
git commit -m "feat: neues Feature implementiert"

# 8. Nächster kleiner Schritt...
```

---

## Qualitätskriterien vor Merge/Deploy

- ✅ Alle Tests grün (`pytest`)
- ✅ Type Check sauber (`mypy`)
- ✅ Linting sauber (`ruff`)
- ✅ Code-Coverage > 80%
- ✅ Dokumentation aktualisiert (falls relevant)
- ✅ Mobile-Responsive getestet (Chrome DevTools)

---

## Hilfreiche Befehle

```bash
# Kompletter Check vor Commit
uv run pytest && uv run mypy app/ && uv run ruff check app/ && echo "✅ Alles OK!"

# Coverage-Report anzeigen
uv run pytest --cov=app --cov-report=html

# App starten (Entwicklung)
uv run python main.py

# Dependency hinzufügen
uv add <package-name>

# Alembic Migration erstellen
uv run alembic revision --autogenerate -m "migration description"
```

---

## Von VellenBase übernehmen

### 1:1 Übernahme (nur anpassen)

Diese Komponenten direkt von VellenBase kopieren und für Fuellhorn anpassen:

- **User Model** (`app/models/user.py`)
  - ✏️ Anpassen: `role` von JSON-Array auf String ändern (nur 2 Rollen: admin, user)

- **Auth Service** (`app/services/auth_service.py`)
  - ✏️ Anpassen: Permission-Mapping für 2 Rollen

- **Auth System** (`app/auth/permissions.py`, `app/auth/decorators.py`, `app/auth/dependencies.py`)
  - ✏️ Anpassen: Permissions für Fuellhorn (ITEMS_READ, ITEMS_WRITE, CONFIG_MANAGE, etc.)

- **Database Setup** (`app/database.py`)
  - ✅ 1:1 übernehmen

- **Config** (`app/config.py`)
  - ✏️ Anpassen: Fuellhorn-spezifische Settings

- **Security Utils** (`app/utils/security.py`)
  - ✅ 1:1 übernehmen

### Als Vorlage nutzen

Diese Patterns von VellenBase lernen und adaptieren:

- **Login Page** (`app/ui/auth.py`)
  - ✏️ Anpassen: "Angemeldet bleiben" Checkbox hinzufügen (default ON)

- **Layout** (`app/ui/layout.py`)
  - ⚠️ Komplett neu: Bottom Navigation statt Sidebar!

- **UI Pages** - Struktur und Patterns übernehmen
  - ⚠️ Anpassen: Card Layout statt Tabellen
  - ⚠️ Anpassen: Bottom Sheets statt Center-Modals
  - ⚠️ Anpassen: Infinite Scroll statt Pagination
  - ✅ Permission-basierte Sichtbarkeit übernehmen

- **Service Layer Pattern** - Business Logic trennen
  - ✅ Gleicher Ansatz wie VellenBase

- **Error Handling** - Notifications, Try/Catch
  - ✅ Gleicher Ansatz wie VellenBase

- **Testing Setup** - pytest-Struktur
  - ✅ Gleicher Ansatz wie VellenBase

---

## Zusammenarbeit mit Claude Code

- Diese Datei dient als Referenz für Claude Code (AI Assistant)
- Claude muss sich an diese Regeln halten bei Code-Generierung
- Bei Unsicherheiten: Nachfragen statt raten
- Bei Fragestellungen auch die WebSearch mit einbeziehen

---

## Unterschiede zu VellenBase

**Architektur**:
- ✅ Gleicher Tech-Stack (NiceGUI + FastAPI + SQLModel)
- ✅ Gleiche 3-Schichten-Architektur
- ✅ Gleicher Permission-basierter Auth-Ansatz

**Infrastruktur & DevOps**:
- ⚠️ **GitHub** statt GitLab (Repository Hosting)
- ⚠️ **GitHub Actions** statt GitLab CI (CI/CD Pipeline)
- ⚠️ **Open Source von Anfang an** (Public Repository)

**UI/UX**:
- ⚠️ **Mobile-First** statt Desktop-First
- ⚠️ **Bottom Navigation** statt Sidebar
- ⚠️ **Card Layout** statt Tabellen
- ⚠️ **Infinite Scroll** statt Pagination (Performance-Optimierung Post-MVP)
- ⚠️ **Bottom Sheets** statt Center-Modals

**Datenmodell**:
- ⚠️ **Items** statt Members (völlig andere Domain)
- ⚠️ **5 Artikel-Typen** mit unterschiedlicher Expiry-Logik
- ⚠️ **Flache Kategorien** (Tags)
- ⚠️ **Lagerorte** mit Typen (frozen/chilled/ambient)

**UX Features**:
- ✨ **Smart Defaults** mit Zeitfenstern (Browser Storage)
- ✨ **Lange Sessions** (30 Tage mit "Angemeldet bleiben")
- ✨ **3-Step Wizard** für Item-Erfassung
- ✨ **Expiry Status** (rot/gelb/grün)

---

## Produkt-Anforderungen & Roadmap

Alle funktionalen und nicht-funktionalen Anforderungen, Use Cases, User Stories und die Post-MVP Roadmap sind in **[requirements.md](requirements.md)** dokumentiert.

**CLAUDE.md fokussiert sich auf Entwicklungsregeln und Prozesse, nicht auf Produkt-Features.**
