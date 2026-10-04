"""Doku-Guards (Issue #400): genannte Pfade existieren, CLI-Befehle gibt es, bekannte Altlasten sind weg."""

from pathlib import Path
import pytest
import re


REPO = Path(__file__).resolve().parents[2]
RELEASE_DOC = REPO / "RELEASE.md"
DOC_FILES = sorted(
    [REPO / "README.md", REPO / "CLAUDE.md", RELEASE_DOC, REPO / "charts" / "fuellhorn" / "README.md"]
    + list((REPO / "docs").rglob("*.md"))
)
NOTES = REPO / "charts" / "fuellhorn" / "templates" / "NOTES.txt"
RELEASE_WORKFLOW = REPO / ".github" / "workflows" / "release.yaml"

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


# --- Release-Dokumentation (Issue #454) -----------------------------------------------------

# Das Bash-Muster, mit dem helm-publish unzulässige Tags abweist
WORKFLOW_TAG_PATTERN = re.compile(r"=~\s*(\S+)\s*\]\]")
# Tags, die RELEASE.md in Befehlen vorschlägt
TAG_IN_COMMAND = re.compile(r"(?:gh release create|git tag(?:\s+-\S+)*)\s+v(\S+)")
# Veröffentlichungsziel im Workflow -> Begriff, der in RELEASE.md stehen muss
PUBLISH_TARGETS = {
    "test.pypi.org": "test.pypi.org",
    "pypa/gh-action-pypi-publish": "pypi",
    "ghcr.io": "ghcr.io",
    "helm push": "helm",
}


def _allowed_tag_pattern() -> re.Pattern[str]:
    """Holt das Versions-Muster aus dem Release-Workflow, damit die Doku nicht davon abdriftet."""
    match = WORKFLOW_TAG_PATTERN.search(RELEASE_WORKFLOW.read_text(encoding="utf-8"))
    assert match is not None, "Versions-Prüfung in release.yaml nicht gefunden"
    pattern = re.compile(match.group(1))
    # Selbstprüfung: das extrahierte Muster trennt erlaubte von unzulässigen Versionen
    assert pattern.fullmatch("1.0.0a9") and pattern.fullmatch("1.2.3")
    assert not pattern.fullmatch("1.0.0.dev1") and not pattern.fullmatch("1.0")
    return pattern


def test_release_doc_exists() -> None:
    assert RELEASE_DOC.is_file(), "RELEASE.md fehlt; der Release-Prozess steht sonst nur im Workflow"


def test_release_doc_tag_examples_match_the_workflow_pattern() -> None:
    """Ein Tag aus der Anleitung muss das Muster erfüllen, das release.yaml erzwingt."""
    pattern = _allowed_tag_pattern()
    tags = TAG_IN_COMMAND.findall(_code_segments(RELEASE_DOC.read_text(encoding="utf-8")))

    assert tags, "RELEASE.md nennt keinen Tag in einem Befehl"
    assert [tag for tag in tags if not pattern.fullmatch(tag)] == []


def test_release_doc_names_every_publish_target() -> None:
    """Kommt ein Ziel im Workflow vor, muss die Anleitung es nennen."""
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    doc = RELEASE_DOC.read_text(encoding="utf-8").lower()
    missing = sorted(term for marker, term in PUBLISH_TARGETS.items() if marker in workflow and term not in doc)

    assert missing == []


def test_readme_points_to_the_release_doc() -> None:
    assert "RELEASE.md" in (REPO / "README.md").read_text(encoding="utf-8")
