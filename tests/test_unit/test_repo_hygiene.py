"""Repo-Hygiene-Guards (Issue #401): Ignore-Dateien, pre-commit = CI-Werkzeuge, keine Altlasten im Root."""

from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[2]


def _lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_gitignore_has_no_duplicate_rules() -> None:
    rules = _lines(REPO / ".gitignore")
    duplicates = sorted({rule for rule in rules if rules.count(rule) > 1})

    assert duplicates == []


def test_gitignore_covers_stray_databases_and_worktrees() -> None:
    rules = _lines(REPO / ".gitignore")

    assert "*.db" in rules, "Test-/Seed-Datenbanken im Root dürfen git status nicht verschmutzen"
    assert ".worktrees/" in rules, "scripts/dev-server.sh erkennt .worktrees/<name>"


def test_dockerignore_names_only_existing_project_files() -> None:
    """Einträge ohne Wildcard/Negation müssen im Repo existieren; Laufzeitpfade sind erlaubt."""
    runtime_only = {
        ".git",
        ".venv",
        "__pycache__",
        "venv/",
        "ENV/",
        "env/",
        ".eggs/",
        "dist/",
        "build/",
        ".pytest_cache",
        ".coverage",
        "htmlcov/",
        ".env",
        ".env.local",
        ".ruff_cache",
        ".mypy_cache",
        ".vscode/",
        ".idea/",
        "data/",
        ".claude/",
        ".worktrees/",
    }
    rules = [rule for rule in _lines(REPO / ".dockerignore") if not re.search(r"[*!?\[]", rule)]
    missing = sorted(rule for rule in rules if rule not in runtime_only and not (REPO / rule.rstrip("/")).exists())

    assert missing == []


def test_dockerignore_excludes_design_sources_and_docs() -> None:
    rules = _lines(REPO / ".dockerignore")

    assert "ci-guidelines/" in rules
    assert "docs/" in rules


def test_precommit_uses_the_ci_toolchain() -> None:
    config = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "mypy" not in config
    assert "uv run ty check" in config
    assert "uv run ruff" in config


def test_root_has_no_redundant_admin_script_or_empty_alembic_dir() -> None:
    assert not (REPO / "create_admin.py").exists()
    assert not (REPO / "alembic").exists()


def test_wheel_does_not_force_include_an_unread_alembic_ini() -> None:
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")

    assert "force-include" not in pyproject


def test_ci_guidelines_keep_no_zip_duplicates() -> None:
    assert sorted((REPO / "ci-guidelines").glob("*.zip")) == []
