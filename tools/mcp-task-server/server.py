#!/usr/bin/env python3
"""
MCP Server für Fuellhorn GitHub Issue Task Management.

Ermöglicht Claude Code Agents:
- Verfügbare Issues auflisten
- Issue-Details und Briefings abrufen
- Issues zuweisen (Labels aktualisieren)
- Abhängige Issues finden
- Nach PR-Merge aufräumen
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from github import Auth, Github
from github.Issue import Issue
from mcp.server.fastmcp import FastMCP

# Konfiguration
REPO_NAME = os.environ.get("FUELLHORN_REPO", "jensens/fuellhorn")

# MCP Server
mcp = FastMCP("Fuellhorn Task Manager")


def get_github_client() -> Github:
    """GitHub Client mit Token aus Umgebung oder gh CLI."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # Fallback: Token von gh CLI holen
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True,
            )
            token = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Kein GitHub Token gefunden. "
                "Setze GITHUB_TOKEN oder authentifiziere mit 'gh auth login'."
            )
    return Github(auth=Auth.Token(token))


def get_repo_path() -> str:
    """Repository-Pfad automatisch erkennen."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.getcwd()


def issue_to_dict(issue: Issue) -> dict[str, Any]:
    """Issue in Dictionary konvertieren."""
    return {
        "number": issue.number,
        "title": issue.title,
        "state": issue.state,
        "url": issue.html_url,
        "labels": [label.name for label in issue.labels],
        "created_at": issue.created_at.isoformat() if issue.created_at else None,
        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
    }


@mcp.tool()
def list_ready_issues() -> list[dict[str, Any]]:
    """
    Liste alle GitHub Issues mit 'status/agent-ready' Label.

    Gibt Issues zurück die sofort von einem Agent bearbeitet werden können.
    Blockierte Issues (mit 'status/blocked' Label) werden ausgeschlossen.
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)

    issues = repo.get_issues(state="open", labels=["status/agent-ready"])

    result = []
    for issue in issues:
        label_names = [label.name for label in issue.labels]
        if "status/blocked" not in label_names:
            result.append(issue_to_dict(issue))

    return result


@mcp.tool()
def list_inprogress_issues() -> list[dict[str, Any]]:
    """
    Liste alle GitHub Issues mit 'status/in-progress' Label.

    Zeigt welche Issues aktuell von Agents bearbeitet werden.
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)

    issues = repo.get_issues(state="open", labels=["status/in-progress"])

    return [issue_to_dict(issue) for issue in issues]


@mcp.tool()
def get_issue_details(issue_number: int) -> dict[str, Any]:
    """
    Hole detaillierte Informationen zu einem GitHub Issue.

    Args:
        issue_number: Die Issue-Nummer
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)
    issue = repo.get_issue(issue_number)

    return {
        **issue_to_dict(issue),
        "body": issue.body or "",
    }


@mcp.tool()
def get_issue_briefing(issue_number: int) -> dict[str, Any]:
    """
    Generiere ein vollständiges Briefing für einen Agent.

    Enthält:
    - Worktree-Setup Anweisungen
    - Branch-Naming
    - PR-Erstellungs-Befehl
    - Issue-Beschreibung

    Args:
        issue_number: Die Issue-Nummer
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)
    issue = repo.get_issue(issue_number)

    repo_path = get_repo_path()

    # Branch-Suffix aus Titel generieren
    branch_suffix = re.sub(r"[^a-z0-9]", "-", issue.title.lower())
    branch_suffix = re.sub(r"-+", "-", branch_suffix)[:20].strip("-")

    branch_name = f"feature/issue-{issue_number}-{branch_suffix}"
    worktree_path = f"{repo_path}/worktrees/issue-{issue_number}"

    briefing_text = f"""# Agent Briefing: Issue #{issue_number}

## Issue: {issue.title}

**Repository:** {REPO_NAME}
**Issue URL:** {issue.html_url}
**Branch:** `{branch_name}`
**Worktree:** `{worktree_path}`

## Setup Anweisungen

### 1. Worktree erstellen (vom Hauptrepo aus, erst main pullen!)
```bash
git pull origin main
git worktree add {worktree_path} -b {branch_name}
```

### 2. In Worktree wechseln
```bash
cd {worktree_path}
```

### 3. Verzeichnis prüfen
```bash
pwd  # Sollte zeigen: {worktree_path}
```

## Entwicklungs-Workflow

1. Lies CLAUDE.md und TESTING.md
2. TDD: Tests zuerst schreiben
3. Qualitätsprüfung vor Commit:
   ```bash
   uv run pytest
   uv run mypy app/
   uv run ruff check app/
   uv run ruff format app/
   ```

## PR erstellen

```bash
gh pr create --title "feat: {issue.title}" --body "closes #{issue_number}"
```

## Nach PR-Merge (vom Hauptrepo aus)

```bash
git worktree remove {worktree_path}
```

---

## Issue-Beschreibung

{issue.body or "(Keine Beschreibung)"}
"""

    return {
        "issue_number": issue_number,
        "issue_title": issue.title,
        "branch_name": branch_name,
        "worktree_path": worktree_path,
        "briefing_text": briefing_text,
        "worktree_commands": [
            "git pull origin main",
            f"git worktree add {worktree_path} -b {branch_name}",
            f"cd {worktree_path}",
        ],
        "quality_commands": [
            "uv run pytest",
            "uv run mypy app/",
            "uv run ruff check app/",
            "uv run ruff format app/",
        ],
        "pr_command": f'gh pr create --title "feat: {issue.title}" --body "closes #{issue_number}"',
    }


@mcp.tool()
def assign_issue(issue_number: int) -> dict[str, Any]:
    """
    Weise ein Issue einem Agent zu.

    Entfernt 'status/agent-ready' Label und fügt 'status/in-progress' hinzu.

    Args:
        issue_number: Die Issue-Nummer
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)
    issue = repo.get_issue(issue_number)

    labels_removed = []
    labels_added = []

    # agent-ready entfernen
    try:
        issue.remove_from_labels("status/agent-ready")
        labels_removed.append("status/agent-ready")
    except Exception:
        pass

    # in-progress hinzufügen
    try:
        issue.add_to_labels("status/in-progress")
        labels_added.append("status/in-progress")
    except Exception as e:
        return {
            "success": False,
            "issue_number": issue_number,
            "message": f"Fehler beim Setzen von in-progress Label: {e}",
            "labels_removed": labels_removed,
            "labels_added": labels_added,
        }

    return {
        "success": True,
        "issue_number": issue_number,
        "message": f"Issue #{issue_number} erfolgreich zugewiesen",
        "labels_removed": labels_removed,
        "labels_added": labels_added,
    }


@mcp.tool()
def list_dependent_issues(issue_number: int) -> list[dict[str, Any]]:
    """
    Finde alle Issues die von diesem Issue blockiert werden.

    Sucht nach "Blocked by #X" Pattern in Issue-Bodies.
    Diese Issues werden freigeschaltet wenn das aktuelle Issue geschlossen wird.

    Args:
        issue_number: Die Issue-Nummer
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)

    # Pattern für "Blocked by #X" (mit optionalem Doppelpunkt)
    pattern = re.compile(rf"(?i)blocked\s+by:?\s*#{issue_number}\b")

    dependents = []
    for issue in repo.get_issues(state="open"):
        if issue.body and pattern.search(issue.body):
            dependents.append({
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
            })

    return dependents


@mcp.tool()
def complete_issue(issue_number: int) -> dict[str, Any]:
    """
    Prüfe Status nach PR-Merge und gib Aufräum-Anweisungen.

    - Prüft ob ein PR für das Issue existiert und gemerged wurde
    - Gibt Befehl zum Worktree-Aufräumen
    - Listet Issues die jetzt freigeschaltet wurden

    Args:
        issue_number: Die Issue-Nummer
    """
    gh = get_github_client()
    repo = gh.get_repo(REPO_NAME)
    issue = repo.get_issue(issue_number)

    repo_path = get_repo_path()
    worktree_path = f"{repo_path}/worktrees/issue-{issue_number}"

    # PR suchen der dieses Issue schließt
    pr_found = None
    pr_merged = False

    for pr in repo.get_pulls(state="all"):
        if pr.body and f"closes #{issue_number}" in pr.body.lower():
            pr_found = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged,
                "url": pr.html_url,
            }
            pr_merged = pr.merged
            break
        if pr.body and f"close #{issue_number}" in pr.body.lower():
            pr_found = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged,
                "url": pr.html_url,
            }
            pr_merged = pr.merged
            break

    # Abhängige Issues die jetzt freigeschaltet sein sollten
    dependents = list_dependent_issues(issue_number) if issue.state == "closed" else []

    return {
        "issue_number": issue_number,
        "issue_state": issue.state,
        "pr": pr_found,
        "pr_merged": pr_merged,
        "cleanup_command": f"git worktree remove {worktree_path}",
        "worktree_path": worktree_path,
        "unlocked_issues": dependents,
        "message": (
            f"Issue #{issue_number} ist {'geschlossen' if issue.state == 'closed' else 'noch offen'}. "
            f"{'PR wurde gemerged.' if pr_merged else 'Kein gemergter PR gefunden.'}"
        ),
    }


def main() -> None:
    """Entry point für den MCP Server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
