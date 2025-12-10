"""Bottom Navigation Bar - Mobile-First Navigation Component.

Based on UI_KONZEPT.md Section 4: Bottom Navigation (Mobile)
- 56px height
- Sticky at bottom
- 3 main items (Issue #83: removed 'Mehr')
- Active state with primary color
- Uses custom Solarpunk SVG icons
"""

from ..theme.icons import create_icon
from nicegui import ui
from typing import Any


def create_bottom_nav(current_page: str = "dashboard") -> None:
    """Create bottom navigation bar for mobile-first UI.

    Args:
        current_page: Current active page ("dashboard", "add", "inventory")
    """
    # Navigation items with custom icons and labels (Issue #83: only 3 items)
    nav_items = [
        {"id": "dashboard", "icon": "navigation/home", "label": "Übersicht", "route": "/dashboard"},
        {"id": "add", "icon": "navigation/add", "label": "Erfassen", "route": "/items/add"},
        {"id": "inventory", "icon": "navigation/inventory", "label": "Vorrat", "route": "/items"},
    ]

    # Bottom navigation container - sticky at bottom
    with (
        ui.row()
        .classes("sp-bottom-nav fixed bottom-0 left-0 right-0 justify-around items-center z-50")
        .style("height: 56px")
    ):
        for item in nav_items:
            is_active = item["id"] == current_page

            # Navigation button - 48x48px touch target
            active_class = "sp-nav-item active" if is_active else "sp-nav-item"
            with (
                ui.column()
                .classes(f"{active_class} items-center justify-center cursor-pointer flex-1 py-2 gap-0.5")
                .style("min-width: 48px; min-height: 48px")
                .on("click", lambda route=item["route"]: ui.navigate.to(route))
            ):
                # Custom SVG icon with active state
                icon_color = "text-fern" if is_active else "text-stone"
                create_icon(item["icon"], size="24px", classes=icon_color)

                # Label with active state (theme handles colors via .active class)
                label_color = "text-fern" if is_active else "text-stone"
                ui.label(item["label"]).classes(f"text-xs font-medium {label_color}")


def create_mobile_page_container() -> Any:
    """Create container for mobile page with bottom navigation spacing.

    Returns the column container that should be used for page content.
    Uses max-width: 800px for consistent layout across all pages (Issue #81).
    """
    # Main content area with max-width for desktop and padding for bottom nav (56px + 16px spacing)
    return ui.column().classes("w-full mx-auto p-4").style("max-width: 800px; padding-bottom: 72px")
