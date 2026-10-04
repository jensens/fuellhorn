"""Doku-Guards (Issue #400): genannte Pfade existieren, CLI-Befehle gibt es, bekannte Altlasten sind weg."""

from pathlib import Path
import pytest
import re


REPO = Path(__file__).resolve().parents[2]
DOC_FILES = sorted(
    [REPO / "README.md", REPO / "CLAUDE.md", REPO / "charts" / "fuellhorn" / "README.md"]
    + list((REPO / "docs").rglob("*.md"))
)
NOTES = REPO / "charts" / "fuellhorn" / "templates" / "NOTES.txt"

# Repo-relative Pfade mit Dateiendung; URLs und ../-Links sind durch das vorangehende Zeichen ausgeschlossen
PATH_TOKEN = re.compile(
    r"(?<![\w/.-])((?:app|scripts|docs|tests|charts|\.github)/[\w./-]+\.(?:py|md|sh|yaml|yml|css|js|toml|txt|ini))"
)
CODE_SEGMENT = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
# Kommandozeilen, die das fuellhorn-CLI aufrufen: optional Env-Zuweisungen, `uv run`, `docker exec …`
CLI_LINE = re.compile(
    r"^\s*(?:\$ )?(?:[A-Z_]+=\S+\s+)*"
    r"(?:uv run |docker exec \S+ |docker compose exec (?:-e \S+ )*\S+ |kubectl exec \S+ -- )?"
    r"fuellhorn ([a-z][a-z-]*)",
    re.MULTILINE,
)
STALE_SNIPPETS = [
    "create_admin.py",
    "uv run mypy",
    "tests/test_models.py",
    '"/static/solarpunk-theme.css"',
    "ci-guidelines/solarpunk-theme.css",
    "Kubernetes 1.19",
    "--version 0.2.0",
    "targetRevision: 0.2.0",
    "Kategorien (optional, Multi-Select)",
    "beim ersten Start",
]


def _cli_commands() -> set[str]:
    """Die Befehle, die app/cli.py tatsächlich verteilt."""
    source = (REPO / "app" / "cli.py").read_text(encoding="utf-8")
    return set(re.findall(r'command == "([a-z-]+)"', source))


def _code_segments(text: str) -> str:
    return "\n".join(CODE_SEGMENT.findall(text))


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: str(p.relative_to(REPO)))
def test_documented_paths_exist(doc: Path) -> None:
    text = doc.read_text(encoding="utf-8")
    missing = sorted({token for token in PATH_TOKEN.findall(text) if not (REPO / token).exists()})

    assert missing == []


@pytest.mark.parametrize("doc", [*DOC_FILES, NOTES], ids=lambda p: str(p.relative_to(REPO)))
def test_documented_cli_commands_exist(doc: Path) -> None:
    """``fuellhorn <befehl>`` auf Kommandozeilen in Code-Blöcken muss ein Befehl aus app/cli.py sein."""
    text = doc.read_text(encoding="utf-8")
    segments = _code_segments(text) if doc.suffix == ".md" else text
    unknown = sorted({cmd for cmd in CLI_LINE.findall(segments) if cmd not in _cli_commands()})

    assert unknown == []


def test_cli_line_pattern_recognises_the_documented_forms() -> None:
    sample = (
        "ADMIN_PASSWORD=x uv run fuellhorn create-admin\n"
        "docker compose exec -e ADMIN_PASSWORD=x app fuellhorn create-admin\n"
        "docker exec fuellhorn-app fuellhorn migrate\n"
        "fuellhorn seed shelf-life-defaults\n"
        "helm install fuellhorn oci://ghcr.io/jensens/fuellhorn\n"
    )

    assert CLI_LINE.findall(sample) == ["create-admin", "create-admin", "migrate", "seed"]


@pytest.mark.parametrize("snippet", STALE_SNIPPETS)
def test_known_stale_snippets_are_gone(snippet: str) -> None:
    offenders = [
        str(doc.relative_to(REPO)) for doc in [*DOC_FILES, NOTES] if snippet in doc.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_helm_notes_point_to_the_cli_for_the_first_admin() -> None:
    assert "fuellhorn create-admin" in NOTES.read_text(encoding="utf-8")


def test_chart_has_no_unreferenced_configmap() -> None:
    """Die ConfigMap renderte DB_*-Werte, die kein Template einbindet und keine App-Variable liest."""
    templates = REPO / "charts" / "fuellhorn" / "templates"
    referenced = any(
        "configMapKeyRef" in path.read_text(encoding="utf-8") or "configMapRef" in path.read_text(encoding="utf-8")
        for path in templates.glob("*.yaml")
    )

    assert referenced or not (templates / "configmap.yaml").exists()
