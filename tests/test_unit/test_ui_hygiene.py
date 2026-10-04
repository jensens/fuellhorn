"""Hygiene-Guards für app/ui (Issue #399).

- Der im Review benannte tote Code bleibt entfernt (manuelle Liste statt vulture).
- Farben in app/ui kommen aus ``theme/tokens.py`` bzw. CSS-Variablen (``var(--sp-…)``).
- Jede Theme-Klasse, die Python oder JavaScript setzt, ist in ``solarpunk-theme.css`` definiert.
"""

import importlib
from pathlib import Path
import pytest
import re


APP = Path(__file__).resolve().parents[2] / "app"
UI = APP / "ui"
CSS = (APP / "static" / "css" / "solarpunk-theme.css").read_text(encoding="utf-8")
JS_FILES = list((APP / "static" / "js").glob("*.js"))

REMOVED_MODULES = ["app.ui.components.expiry_badge"]
REMOVED_SYMBOLS: dict[str, list[str]] = {
    "app.ui.components.swipe_card": [
        "reset_swipe_card",
        "reset_all_swipe_cards",
        "handle_swipe_event",
        "event_receiver",
    ],
    "app.ui.components.item_card": ["get_status_text_class"],
    "app.ui.components.category_chips": ["create_category_chip_group", "_group_by_parent"],
    "app.ui.validation.wizard_validation": ["requires_category", "_requires_category", "validate_category"],
    "app.ui.theme.tokens": ["STATUS_COLORS", "STATUS_HEX_COLORS"],
    "app.ui.theme.colors": ["hex_to_rgb", "with_alpha"],
    "app.auth.dependencies": ["get_current_user_from_request", "require_api_permission"],
    "app.ui.components": [
        "create_expiry_badge",
        "create_status_icon",
        "get_status_text_color",
        "get_status_text_class",
        "reset_swipe_card",
        "reset_all_swipe_cards",
        "create_category_chip_group",
    ],
    "app.ui.theme": ["STATUS_COLORS", "STATUS_HEX_COLORS", "hex_to_rgb", "with_alpha"],
    "app.ui.validation": ["requires_category", "validate_category"],
}


def test_removed_modules_stay_removed() -> None:
    for name in REMOVED_MODULES:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(name)


@pytest.mark.parametrize(("module", "symbols"), REMOVED_SYMBOLS.items(), ids=list(REMOVED_SYMBOLS))
def test_removed_symbols_stay_removed(module: str, symbols: list[str]) -> None:
    mod = importlib.import_module(module)

    assert [name for name in symbols if hasattr(mod, name)] == []


# --- Farben ------------------------------------------------------------------------------

HEX_LITERAL = re.compile(r"#[0-9A-Fa-f]{6}\b")
FOREIGN_CSS_VAR = re.compile(r"var\(--(?!sp-)")
TOKENS_FILE = UI / "theme" / "tokens.py"


def _ui_python_files() -> list[Path]:
    return sorted(p for p in UI.rglob("*.py") if "__pycache__" not in p.parts and "test_pages" not in p.parts)


def test_ui_colors_come_from_tokens() -> None:
    """Hex-Literale nur in tokens.py; alle anderen Stellen referenzieren Colors.* (#399)."""
    offenders = [
        f"{path.relative_to(APP)}:{lineno}: {line.strip()}"
        for path in _ui_python_files()
        if path != TOKENS_FILE
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if HEX_LITERAL.search(line)
    ]

    assert offenders == []


def test_ui_css_variables_use_the_theme_prefix() -> None:
    """``var(--stone)`` o.ä. greift nie; die Variablen heißen ``--sp-…``."""
    offenders = [
        f"{path.relative_to(APP)}:{lineno}: {line.strip()}"
        for path in _ui_python_files()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if FOREIGN_CSS_VAR.search(line)
    ]

    assert offenders == []


# --- CSS-Klassen ------------------------------------------------------------------------------

PALETTE = set(re.findall(r"^\s*--sp-([a-z0-9-]+):", CSS, re.MULTILINE))
CLASSES_CALL = re.compile(r"\.classes\(\s*(?:(?:add|remove|replace)\s*=\s*)?[fr]?\"([^\"]*)\"", re.DOTALL)
CLASSLIST_CALL = re.compile(r"classList\.(?:add|remove|toggle)\(([^)]*)\)")
CUSTOM_PREFIXES = ("sp-", "swiped-", "swipe-card", "bottom-sheet", "expiry-badge")


def _is_theme_class(token: str) -> bool:
    """Klassen, die nur unser CSS definieren kann (Tailwind/Quasar-Klassen bleiben außen vor)."""
    if token.startswith(CUSTOM_PREFIXES):
        return True
    match = re.fullmatch(r"(?:hover:)?(?:text|bg|border)-([a-z0-9-]+)", token)
    return bool(match) and match.group(1) in PALETTE


def _used_theme_classes() -> dict[str, set[str]]:
    used: dict[str, set[str]] = {}
    for path in _ui_python_files():
        for literal in CLASSES_CALL.findall(path.read_text(encoding="utf-8")):
            for token in literal.split():
                if "{" not in token and _is_theme_class(token):
                    used.setdefault(token, set()).add(str(path.relative_to(APP)))
    for path in JS_FILES:
        for arglist in CLASSLIST_CALL.findall(path.read_text(encoding="utf-8")):
            for token in re.findall(r"['\"]([^'\"]+)['\"]", arglist):
                if _is_theme_class(token):
                    used.setdefault(token, set()).add(str(path.relative_to(APP)))
    return used


def _is_defined(token: str) -> bool:
    selector = re.escape("." + token.replace(":", "\\:"))
    return re.search(rf"{selector}(?![\w-])", CSS) is not None


def test_every_used_theme_class_is_defined_in_css() -> None:
    used = _used_theme_classes()
    assert "sp-chip" in used, "Extraktion muss die bekannten Chip-Klassen finden"

    undefined = {token: sorted(files) for token, files in used.items() if not _is_defined(token)}

    assert undefined == {}
