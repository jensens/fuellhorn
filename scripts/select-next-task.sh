#!/bin/bash
#
# select-next-task.sh - Interaktives Script zur Auswahl des nächsten Issues für Agenten
#
# Verwendung:
#   ./scripts/select-next-task.sh
#
# Das Script:
#   1. Zeigt alle agent-ready Issues
#   2. Erlaubt Auswahl und zeigt Details
#   3. Fragt ob Issue zugewiesen werden soll
#   4. Aktualisiert Labels (agent-ready → in-progress)
#   5. Gibt Briefing-Prompt für Agent aus (Agent erstellt Worktree selbst!)
#   6. Zeigt abhängige Issues die danach freigeschaltet werden
#

set -e

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Repository (kann angepasst werden)
REPO="jensens/fuellhorn"

print_header() {
    echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${BOLD}${YELLOW}─── $1 ───${NC}\n"
}

# Funktion: Alle agent-ready Issues laden (ohne blockierte!)
get_ready_issues() {
    # Hole agent-ready Issues und filtere blockierte heraus
    gh issue list --repo "$REPO" --label "status/agent-ready" --state open --json number,title,labels --limit 50 | \
        jq '[.[] | select(.labels | map(.name) | index("status/blocked") | not)]'
}

# Funktion: Alle in-progress Issues laden
get_inprogress_issues() {
    gh issue list --repo "$REPO" --label "status/in-progress" --state open --json number,title --limit 20
}

# Funktion: Issue-Details anzeigen
show_issue_details() {
    local issue_num=$1
    echo -e "${BOLD}Issue #$issue_num Details:${NC}\n"
    gh issue view "$issue_num" --repo "$REPO"
}

# Funktion: Abhängige Issues dynamisch finden (sucht "Blocked by #X" in Issue-Bodies)
find_dependents() {
    local issue_num=$1
    # Suche alle offenen Issues die "Blocked by #<issue_num>" im Body haben
    gh issue list --repo "$REPO" --state open --json number,title,body --limit 100 | \
        jq -r --arg num "$issue_num" '.[] | select(.body != null) | select(.body | test("(?i)blocked\\s+by:?\\s*#" + $num + "\\b")) | "\(.number)\t\(.title)"'
}

# Funktion: Abhängige Issues anzeigen
show_dependents() {
    local issue_num=$1

    print_section "Abhängige Issues (werden nach Abschluss freigeschaltet)"

    local deps
    deps=$(find_dependents "$issue_num")

    if [ -n "$deps" ]; then
        echo "$deps" | while IFS=$'\t' read -r dep_num dep_title; do
            echo -e "  ${GREEN}→ #$dep_num${NC}: $dep_title"
        done
        echo ""
    else
        echo -e "${YELLOW}Keine abhängigen Issues gefunden.${NC}\n"
    fi
}

# Funktion: Briefing-Prompt generieren
generate_briefing() {
    local issue_num=$1
    local issue_title=$2
    local branch_suffix
    branch_suffix=$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 20)
    # Worktree im Unterordner worktrees/ (gitignored)
    local worktree_abs
    worktree_abs="$(pwd)/worktrees/issue-$issue_num"
    local branch_name="feature/issue-$issue_num-$branch_suffix"
    local issue_body
    issue_body=$(gh issue view "$issue_num" --repo "$REPO" --json body -q .body 2>/dev/null)

    print_section "Briefing-Prompt für Agent (in Zwischenablage kopieren!)"

    echo -e "${BOLD}────────────────────────────────────────────────────────────────${NC}"
    cat << EOF
Bitte implementiere Issue #$issue_num: $issue_title

WICHTIG - Worktree selbst erstellen:
Du musst zuerst einen Git Worktree erstellen um isoliert zu arbeiten.

1. Worktree erstellen (vom Hauptrepo aus, unbedingt erst main pullen!):
   git pull origin main
   git worktree add $worktree_abs -b $branch_name

2. In Worktree wechseln:
   cd $worktree_abs

3. Prüfen mit 'pwd' dass du im richtigen Verzeichnis bist!

Kontext:
- Repository: $REPO
- Issue: https://github.com/$REPO/issues/$issue_num
- Branch: $branch_name
- Worktree: $worktree_abs

Arbeitsschritte:
1. Worktree erstellen (siehe oben)
2. Lies CLAUDE.md und TESTING.md
3. TDD: Tests zuerst schreiben
4. Qualitätsprüfung vor Commit:
   uv run pytest
   uv run mypy app/
   uv run ruff check app/
   uv run ruff format app/
5. PR erstellen mit "closes #$issue_num" im Body:
   gh pr create --title "feat: $issue_title" --body "closes #$issue_num"
6. Nach PR-Merge: Worktree aufräumen (vom Hauptrepo aus):
   git worktree remove $worktree_abs

Issue-Beschreibung:
$issue_body
EOF
    echo -e "${BOLD}────────────────────────────────────────────────────────────────${NC}"
}

# Funktion: Labels aktualisieren
update_labels() {
    local issue_num=$1

    echo -e "\n${YELLOW}Aktualisiere Labels...${NC}"

    # agent-ready entfernen
    gh issue edit "$issue_num" --repo "$REPO" --remove-label "status/agent-ready" 2>/dev/null || true
    echo -e "${GREEN}✓ Label 'status/agent-ready' entfernt${NC}"

    # in-progress hinzufügen (mit Fehlerprüfung)
    if gh issue edit "$issue_num" --repo "$REPO" --add-label "status/in-progress" 2>/dev/null; then
        echo -e "${GREEN}✓ Label 'status/in-progress' hinzugefügt${NC}"
    else
        echo -e "${RED}✗ FEHLER: Label 'status/in-progress' konnte nicht gesetzt werden!${NC}"
        echo -e "${YELLOW}  Bitte manuell erstellen: gh label create 'status/in-progress' --color 'FBCA04'${NC}"
    fi
}

# Hauptmenü
main_menu() {
    while true; do
        print_header "Fuellhorn - Nächstes Issue auswählen"

        # Issues laden
        local issues_json=$(get_ready_issues)
        local count=$(echo "$issues_json" | jq 'length')

        if [ "$count" -eq 0 ]; then
            echo -e "${YELLOW}Keine agent-ready Issues vorhanden.${NC}"
            echo -e "Prüfe ob abhängige Issues abgeschlossen wurden und setze Labels manuell:"
            echo -e "${CYAN}gh issue edit <number> --add-label 'status/agent-ready'${NC}"
            exit 0
        fi

        # In-Progress Issues laden und anzeigen
        local inprogress_json
        inprogress_json=$(get_inprogress_issues)
        local inprogress_count
        inprogress_count=$(echo "$inprogress_json" | jq 'length')

        if [ "$inprogress_count" -gt 0 ]; then
            echo -e "${BOLD}${YELLOW}⏳ In Bearbeitung (${inprogress_count}):${NC}\n"
            printf "${BOLD}%-6s %-60s${NC}\n" "#" "Titel"
            printf "%-6s %-60s\n" "------" "------------------------------------------------------------"
            echo "$inprogress_json" | jq -r '.[] | "#\(.number)\t\(.title)"' | while read -r line; do
                num=$(echo "$line" | cut -d'#' -f2 | cut -f1)
                title=$(echo "$line" | cut -f2)
                printf "${YELLOW}%-6s${NC} %-60s\n" "#$num" "$title"
            done
            echo ""
        fi

        echo -e "${BOLD}${GREEN}✅ Verfügbar (${count}):${NC}\n"

        # Issues als Tabelle anzeigen
        printf "${BOLD}%-6s %-60s${NC}\n" "#" "Titel"
        printf "%-6s %-60s\n" "------" "------------------------------------------------------------"

        echo "$issues_json" | jq -r '.[] | "#\(.number)\t\(.title)"' | while read -r line; do
            num=$(echo "$line" | cut -d'#' -f2 | cut -f1)
            title=$(echo "$line" | cut -f2)
            printf "${GREEN}%-6s${NC} %-60s\n" "#$num" "$title"
        done

        echo ""
        echo -e "Eingabe: ${BOLD}Issue-Nummer${NC} (grün=auswählen, gelb=Briefing erneut anzeigen), ${BOLD}q${NC} zum Beenden"
        read -p "> " selection

        # Beenden
        if [ "$selection" = "q" ] || [ "$selection" = "Q" ]; then
            echo -e "\n${YELLOW}Auf Wiedersehen!${NC}"
            exit 0
        fi

        # Nummer extrahieren (falls mit # eingegeben)
        selection=$(echo "$selection" | sed 's/#//')

        # Prüfen ob gültige Nummer
        if ! [[ "$selection" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}Ungültige Eingabe. Bitte Issue-Nummer eingeben.${NC}"
            sleep 1
            continue
        fi

        # Prüfen ob Issue in agent-ready Liste
        if ! echo "$issues_json" | jq -e ".[] | select(.number == $selection)" > /dev/null 2>&1; then
            # Prüfen ob Issue in in-progress Liste (dann Briefing nochmal zeigen)
            if echo "$inprogress_json" | jq -e ".[] | select(.number == $selection)" > /dev/null 2>&1; then
                clear
                print_header "Issue #$selection - Briefing erneut anzeigen"
                local inprogress_title
                inprogress_title=$(echo "$inprogress_json" | jq -r ".[] | select(.number == $selection) | .title")
                generate_briefing "$selection" "$inprogress_title"
                show_dependents "$selection"
                echo -e "\n${YELLOW}(Issue ist bereits in Bearbeitung - Labels nicht geändert)${NC}"
                echo -e "\nDrücke Enter um fortzufahren oder 'q' zum Beenden..."
                read -r -p "" next
                if [ "$next" = "q" ]; then
                    exit 0
                fi
                clear
                continue
            fi
            echo -e "${RED}Issue #$selection ist nicht in der Liste der verfügbaren Issues.${NC}"
            sleep 1
            continue
        fi

        # Issue-Details anzeigen
        clear
        print_header "Issue #$selection - Details"

        local issue_title=$(echo "$issues_json" | jq -r ".[] | select(.number == $selection) | .title")

        show_issue_details "$selection"

        echo ""
        show_dependents "$selection"

        # Frage ob zuweisen
        echo -e "${BOLD}Möchtest du dieses Issue einem Agenten zuweisen?${NC}"
        echo -e "  ${GREEN}j${NC} = Ja, zuweisen"
        echo -e "  ${YELLOW}n${NC} = Nein, zurück zur Liste"
        echo -e "  ${RED}q${NC} = Beenden"
        read -p "> " confirm

        case "$confirm" in
            j|J|ja|Ja|JA|y|Y|yes|Yes|YES)
                clear
                print_header "Issue #$selection wird zugewiesen"

                # Labels aktualisieren
                update_labels "$selection"

                # Briefing generieren (Agent erstellt Worktree selbst)
                generate_briefing "$selection" "$issue_title"

                print_section "Nächster Schritt"
                echo -e "1. ${CYAN}Starte einen neuen Agent (z.B. in VSCode oder Terminal)${NC}"
                echo -e "2. ${CYAN}Kopiere das Briefing oben und gib es dem Agent${NC}"
                echo -e "3. ${CYAN}Der Agent erstellt seinen Worktree selbst und räumt ihn nach dem PR auf${NC}"
                echo ""

                # Abhängige Issues nochmal zeigen
                show_dependents "$selection"

                print_section "Nach Abschluss"
                echo -e "Wenn das Issue fertig ist und der PR gemerged wurde:"
                echo -e "  ${GREEN}✓${NC} Abhängige Issues werden ${BOLD}automatisch${NC} freigeschaltet"
                echo -e "    (GitHub Action: unlock-issues.yml)"

                echo -e "\n${GREEN}Issue #$selection ist jetzt in Bearbeitung!${NC}"
                echo -e "\nDrücke Enter um fortzufahren oder 'q' zum Beenden..."
                read -p "" next
                if [ "$next" = "q" ]; then
                    exit 0
                fi
                ;;
            n|N|nein|Nein|NEIN|no|No|NO)
                # Zurück zur Liste
                clear
                continue
                ;;
            q|Q)
                echo -e "\n${YELLOW}Auf Wiedersehen!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Ungültige Eingabe.${NC}"
                sleep 1
                ;;
        esac

        clear
    done
}

# Script starten
clear
main_menu
