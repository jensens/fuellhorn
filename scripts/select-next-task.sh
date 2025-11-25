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
#   5. Gibt Briefing-Prompt für Agent aus
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

# Dependency-Map: Issue → abhängige Issues
declare -A DEPENDENCIES
DEPENDENCIES[7]="9"           # Item Card → Items Page
DEPENDENCIES[8]="9"           # Expiry Badge → Items Page
DEPENDENCIES[9]="10 11 12 13" # Items Page → Suche, Filter, Sortierung
DEPENDENCIES[14]="15 16"      # Bottom Sheet → Entnehmen, Teilentnahme
DEPENDENCIES[15]="17"         # Komplett entnehmen → Ausblenden
DEPENDENCIES[18]="19"         # Logout Button → Session Cleanup
DEPENDENCIES[20]="21 22 23"   # Categories Liste → CRUD
DEPENDENCIES[24]="25 26 27"   # Locations Liste → CRUD
DEPENDENCIES[28]="29 30 31"   # Users Liste → CRUD
DEPENDENCIES[32]="33 34"      # Settings Liste → Gefrierzeit, Smart Defaults
DEPENDENCIES[37]="38"         # Dockerfile → docker-compose
DEPENDENCIES[38]="39"         # docker-compose → Docs

# Kombinierte Dependencies (beide müssen fertig sein)
# #9 braucht sowohl #7 als auch #8
COMBINED_DEPS_9="7 8"

print_header() {
    echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${BOLD}${YELLOW}─── $1 ───${NC}\n"
}

# Funktion: Alle agent-ready Issues laden
get_ready_issues() {
    gh issue list --repo "$REPO" --label "status/agent-ready" --state open --json number,title,labels --limit 50
}

# Funktion: Issue-Details anzeigen
show_issue_details() {
    local issue_num=$1
    echo -e "${BOLD}Issue #$issue_num Details:${NC}\n"
    gh issue view "$issue_num" --repo "$REPO"
}

# Funktion: Abhängige Issues anzeigen
show_dependents() {
    local issue_num=$1
    local deps="${DEPENDENCIES[$issue_num]}"

    if [ -n "$deps" ]; then
        print_section "Abhängige Issues (werden nach Abschluss freigeschaltet)"
        for dep in $deps; do
            local title=$(gh issue view "$dep" --repo "$REPO" --json title -q .title 2>/dev/null || echo "?")
            echo -e "  ${GREEN}→ #$dep${NC}: $title"
        done
        echo ""
    else
        echo -e "${YELLOW}Keine direkten abhängigen Issues.${NC}\n"
    fi
}

# Funktion: Briefing-Prompt generieren
generate_briefing() {
    local issue_num=$1
    local issue_title=$2
    local issue_body=$(gh issue view "$issue_num" --repo "$REPO" --json body -q .body 2>/dev/null)

    print_section "Briefing-Prompt für Agent"

    echo -e "${BOLD}────────────────────────────────────────────────────────────────${NC}"
    cat << EOF
Bitte implementiere Issue #$issue_num: $issue_title

Kontext:
- Repository: $REPO
- Branch: feature/issue-$issue_num-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 30)

Wichtig:
1. Lies zuerst CLAUDE.md und TESTING.md
2. TDD: Tests zuerst schreiben
3. Qualitätsprüfung vor Commit:
   uv run pytest
   uv run mypy app/
   uv run ruff check app/
   uv run ruff format app/
4. PR erstellen mit "closes #$issue_num" im Body

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

    # in-progress hinzufügen
    gh issue edit "$issue_num" --repo "$REPO" --add-label "status/in-progress" 2>/dev/null || true

    echo -e "${GREEN}✓ Label 'status/agent-ready' entfernt${NC}"
    echo -e "${GREEN}✓ Label 'status/in-progress' hinzugefügt${NC}"
}

# Funktion: Worktree-Befehl anzeigen
show_worktree_command() {
    local issue_num=$1
    local issue_title=$2
    local branch_suffix=$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 20)

    print_section "Worktree erstellen"
    echo -e "${CYAN}git worktree add ../fuellhorn-issue-$issue_num -b feature/issue-$issue_num-$branch_suffix${NC}"
    echo -e "${CYAN}cd ../fuellhorn-issue-$issue_num${NC}"
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

        echo -e "${BOLD}Verfügbare Issues (${count} Stück):${NC}\n"

        # Issues als Tabelle anzeigen
        printf "${BOLD}%-6s %-60s${NC}\n" "#" "Titel"
        printf "%-6s %-60s\n" "------" "------------------------------------------------------------"

        echo "$issues_json" | jq -r '.[] | "#\(.number)\t\(.title)"' | while read line; do
            num=$(echo "$line" | cut -d'#' -f2 | cut -f1)
            title=$(echo "$line" | cut -f2)
            printf "${GREEN}%-6s${NC} %-60s\n" "#$num" "$title"
        done

        echo ""
        echo -e "Eingabe: ${BOLD}Issue-Nummer${NC} zum Anzeigen, ${BOLD}q${NC} zum Beenden"
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

        # Prüfen ob Issue in Liste
        if ! echo "$issues_json" | jq -e ".[] | select(.number == $selection)" > /dev/null 2>&1; then
            echo -e "${RED}Issue #$selection ist nicht in der Liste der agent-ready Issues.${NC}"
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

                # Worktree-Befehl
                show_worktree_command "$selection" "$issue_title"

                # Briefing generieren
                generate_briefing "$selection" "$issue_title"

                # Abhängige Issues nochmal zeigen
                show_dependents "$selection"

                print_section "Nach Abschluss"
                echo -e "Wenn das Issue fertig ist und der PR gemerged wurde:"

                local deps="${DEPENDENCIES[$selection]}"
                if [ -n "$deps" ]; then
                    echo -e "\n${BOLD}Folgende Issues freigeben:${NC}"
                    for dep in $deps; do
                        # Spezialfall: #9 braucht sowohl #7 als auch #8
                        if [ "$dep" = "9" ]; then
                            echo -e "  ${YELLOW}#9 erst freigeben wenn BEIDE #7 und #8 erledigt sind!${NC}"
                            echo -e "  ${CYAN}gh issue edit 9 --add-label 'status/agent-ready'${NC}"
                        else
                            echo -e "  ${CYAN}gh issue edit $dep --add-label 'status/agent-ready'${NC}"
                        fi
                    done
                fi

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
