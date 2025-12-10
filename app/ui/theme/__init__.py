"""Solarpunk Theme Module.

This module provides centralized theme utilities, design tokens, and color
functions for the Füllhorn application.

Usage:
    from app.ui.theme import get_contrast_text_color, COLORS, ITEM_TYPE_COLORS

    # Get contrast text color for a background
    text_color = get_contrast_text_color("#4A7C59")

    # Access color tokens
    primary_color = COLORS.FERN

    # Get item type color
    color = ITEM_TYPE_COLORS[ItemType.PURCHASED_FRESH]
"""

from .colors import add_theme_css
from .colors import get_contrast_text_color
from .colors import hex_to_rgb
from .colors import with_alpha
from .icons import ICON_CATEGORIES
from .icons import create_icon
from .icons import get_icon_svg
from .icons import get_icon_svg_inline
from .icons import icon_exists
from .icons import list_icons
from .tokens import COLORS
from .tokens import ITEM_TYPE_COLORS
from .tokens import STATUS_COLORS
from .tokens import STATUS_HEX_COLORS
from .tokens import Colors


__all__ = [
    # Theme loading
    "add_theme_css",
    # Color utilities
    "get_contrast_text_color",
    "hex_to_rgb",
    "with_alpha",
    # Icon system
    "create_icon",
    "get_icon_svg",
    "get_icon_svg_inline",
    "icon_exists",
    "ICON_CATEGORIES",
    "list_icons",
    # Design tokens
    "Colors",
    "COLORS",
    "ITEM_TYPE_COLORS",
    "STATUS_COLORS",
    "STATUS_HEX_COLORS",
]
