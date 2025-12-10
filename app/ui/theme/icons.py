"""Solarpunk Custom Icon System.

Provides access to 67 custom SVG icons organized by category:
- actions/: back, close, delete, edit, filter, save, search, sort, take-out
- categories/: bakery, beef, berries, bread, etc. (34 icons)
- item-types/: fresh, frozen-bought, frozen-home, frozen-self, preserved
- locations/: cellar, freezer-chest, freezer, fridge, pantry
- misc/: logout, notes, scale, settings, user
- navigation/: add, home, inventory
- status/: calendar, critical, expired, info, ok, warning

Usage:
    from app.ui.theme.icons import create_icon, get_icon_svg

    # Create inline SVG element
    create_icon("status/ok", size="24px", classes="text-green-500")

    # Get raw SVG content
    svg_content = get_icon_svg("navigation/home")
"""

from functools import lru_cache
from nicegui import ui
from pathlib import Path
from typing import Any


# Base path to icons directory
ICONS_PATH = Path(__file__).parent.parent.parent / "static" / "icons"


# Icon registry organized by category
ICON_CATEGORIES = {
    "actions": [
        "back",
        "close",
        "delete",
        "edit",
        "filter",
        "save",
        "search",
        "sort",
        "take-out",
    ],
    "categories": [
        "bakery",
        "beef",
        "berries",
        "bread",
        "butter",
        "cake",
        "cheese",
        "chutney",
        "compote",
        "fish",
        "fish-fatty",
        "fruit",
        "ground-meat",
        "herbs",
        "jam",
        "jelly",
        "ketchup",
        "meat",
        "milk",
        "mustard",
        "pesto",
        "pickles",
        "pork",
        "poultry",
        "puree",
        "ready-meal",
        "relish",
        "sauerkraut",
        "sausage",
        "soup",
        "syrup",
        "tomato-sauce",
        "vegetable",
        "yogurt",
    ],
    "item-types": [
        "fresh",
        "frozen-bought",
        "frozen-home",
        "frozen-self",
        "preserved",
    ],
    "locations": [
        "cellar",
        "freezer",
        "freezer-chest",
        "fridge",
        "pantry",
    ],
    "misc": [
        "logout",
        "notes",
        "scale",
        "settings",
        "user",
    ],
    "navigation": [
        "add",
        "home",
        "inventory",
    ],
    "status": [
        "calendar",
        "critical",
        "expired",
        "info",
        "ok",
        "warning",
    ],
}


@lru_cache(maxsize=128)
def get_icon_svg(name: str) -> str:
    """Get raw SVG content for an icon.

    Args:
        name: Icon name in format "category/icon-name" (e.g., "status/ok")

    Returns:
        SVG content as string

    Raises:
        FileNotFoundError: If icon file doesn't exist
    """
    icon_path = ICONS_PATH / f"{name}.svg"
    if not icon_path.exists():
        raise FileNotFoundError(f"Icon not found: {name}")
    return icon_path.read_text()


def get_icon_svg_inline(name: str, size: str = "24px") -> str:
    """Get SVG content with inline size attributes.

    Args:
        name: Icon name in format "category/icon-name"
        size: CSS size value for width and height

    Returns:
        SVG content with width/height attributes
    """
    svg = get_icon_svg(name)
    # Add width and height attributes after the opening svg tag
    # SVGs already have viewBox, so we just need to add dimensions
    return svg.replace(
        "<svg ",
        f'<svg width="{size}" height="{size}" ',
    )


def create_icon(
    name: str,
    size: str = "24px",
    classes: str = "",
) -> Any:
    """Create an inline SVG icon element.

    Uses NiceGUI's ui.html to render the SVG inline, allowing CSS color inheritance
    via currentColor. The SVG stroke/fill uses currentColor, so the icon color
    is controlled by the parent's text color class.

    Args:
        name: Icon name in format "category/icon-name" (e.g., "status/ok")
        size: CSS size value (e.g., "24px", "1.5rem")
        classes: Additional Tailwind/CSS classes for styling

    Returns:
        NiceGUI html element containing the SVG

    Example:
        create_icon("status/ok", size="20px", classes="text-green-500")
    """
    svg_content = get_icon_svg_inline(name, size)
    # Wrap in a span for consistent sizing and flexbox alignment
    html_content = f'<span class="inline-flex items-center justify-center">{svg_content}</span>'
    # sanitize=False required for SVG elements to render correctly
    return ui.html(html_content, sanitize=False).classes(classes)


def icon_exists(name: str) -> bool:
    """Check if an icon exists.

    Args:
        name: Icon name in format "category/icon-name"

    Returns:
        True if icon file exists
    """
    icon_path = ICONS_PATH / f"{name}.svg"
    return icon_path.exists()


def list_icons(category: str | None = None) -> list[str]:
    """List available icons.

    Args:
        category: Optional category to filter by

    Returns:
        List of icon names in "category/icon-name" format
    """
    if category:
        if category not in ICON_CATEGORIES:
            return []
        return [f"{category}/{name}" for name in ICON_CATEGORIES[category]]

    # Return all icons
    result: list[str] = []
    for cat, icons in ICON_CATEGORIES.items():
        result.extend(f"{cat}/{name}" for name in icons)
    return result
