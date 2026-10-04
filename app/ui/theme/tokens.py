"""Design tokens for the Solarpunk theme.

This module defines all design tokens (colors, spacing, etc.) used in the app.
These values mirror the CSS custom properties in solarpunk-theme.css.

Usage:
    from app.ui.theme import COLORS, ITEM_TYPE_COLORS
"""

from ...models.item import ItemType


# =============================================================================
# Color Palette - Solarpunk Theme
# =============================================================================
# These values mirror the CSS custom properties in solarpunk-theme.css


class Colors:
    """Solarpunk color palette constants."""

    # Primary - Greens
    FERN = "#4A7C59"
    FERN_DARK = "#3D6A4A"
    FERN_LIGHT = "#5A8C69"
    MOSS = "#5C7F5C"
    LEAF = "#7CB342"
    LEAF_LIGHT = "#9DC46A"
    SAGE = "#9CAF88"
    SAGE_LIGHT = "#B8C9A8"

    # Secondary - Earth & Gold
    AMBER = "#E6A832"
    AMBER_DARK = "#D49A28"
    AMBER_LIGHT = "#F0BC52"
    HONEY = "#DAA520"
    TERRACOTTA = "#C17F59"

    # Neutrals
    CREAM = "#FAF7F0"
    OAT = "#F5F0E6"
    PARCHMENT = "#EDE8DB"
    STONE = "#A39E93"
    STONE_DARK = "#7D796F"
    CHARCOAL = "#3D3D3D"

    # Status
    STATUS_OK = "#7CB342"
    STATUS_WARNING = "#E6A832"
    STATUS_CRITICAL = "#E07A5F"
    STATUS_INFO = "#5BA3C6"

    # Neutrals für Chips, Vorschauen und Kontrasttext (entsprechen Tailwind gray-200/500/700/800)
    NEUTRAL_LIGHT = "#E5E7EB"
    DEFAULT_GRAY = "#6B7280"
    NEUTRAL_TEXT = "#374151"
    NEUTRAL_DARK = "#1F2937"


# Singleton instance for convenience
COLORS = Colors()


# =============================================================================
# Item Type Colors
# =============================================================================

ITEM_TYPE_COLORS: dict[ItemType, str] = {
    ItemType.PURCHASED_FRESH: Colors.LEAF,  # Leaf green
    ItemType.PURCHASED_FROZEN: Colors.STATUS_INFO,  # Info blue
    ItemType.PURCHASED_THEN_FROZEN: Colors.STATUS_INFO,  # Info blue
    ItemType.HOMEMADE_FROZEN: Colors.TERRACOTTA,  # Terracotta
    ItemType.HOMEMADE_PRESERVED: Colors.TERRACOTTA,  # Terracotta
}
