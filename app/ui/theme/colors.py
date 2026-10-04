"""Centralized color utilities for the Solarpunk theme.

This module provides color manipulation and contrast calculation functions
used throughout the UI. All color-related utilities should be imported from here.
"""

from .tokens import Colors
from functools import lru_cache


@lru_cache(maxsize=256)
def get_contrast_text_color(hex_color: str) -> str:
    """Return optimal text color (white or dark) for given background.

    Uses WCAG relative luminance formula to determine optimal text color
    for accessibility. Results are cached for performance with dynamic
    database colors.

    Args:
        hex_color: Hex color string (with or without # prefix)

    Returns:
        "white" for dark backgrounds, Colors.NEUTRAL_DARK for light backgrounds
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return Colors.NEUTRAL_TEXT  # Default dark gray

    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
    return "white" if luminance < 0.5 else Colors.NEUTRAL_DARK


def add_theme_css() -> None:
    """Add Solarpunk theme CSS to the current page.

    Call this at the beginning of each page function to load the theme CSS.
    Must be called within a NiceGUI page context (inside @ui.page function).

    Example:
        @ui.page("/my-page")
        def my_page():
            add_theme_css()
            ui.label("Hello World")
    """
    from nicegui import ui

    ui.add_head_html('<link rel="stylesheet" href="/static/css/solarpunk-theme.css">')
