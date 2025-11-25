"""Bottom Navigation Bar - Mobile-First Navigation Component.

Based on UI_KONZEPT.md Section 4: Bottom Navigation (Mobile)
- 56px height
- Sticky at bottom
- 4 main items
- Active state with primary color
"""

from nicegui import ui
from typing import Any


def create_bottom_nav(current_page: str = "dashboard") -> None:
    """Create bottom navigation bar for mobile-first UI.

    Args:
        current_page: Current active page ("dashboard", "add", "inventory", "more")
    """
    # Navigation items with icons and labels
    nav_items = [
        {"id": "dashboard", "icon": "home", "label": "Übersicht", "route": "/dashboard"},
        {"id": "add", "icon": "add_circle", "label": "Erfassen", "route": "/items/add"},
        {"id": "inventory", "icon": "inventory_2", "label": "Vorrat", "route": "/items"},
        {"id": "more", "icon": "more_horiz", "label": "Mehr", "route": "/settings"},
    ]

    # Bottom navigation container - sticky at bottom
    with (
        ui.row()
        .classes(
            "fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 justify-around items-center shadow-lg z-50"
        )
        .style("height: 56px")
    ):
        for item in nav_items:
            is_active = item["id"] == current_page

            # Navigation button - 48x48px touch target
            with (
                ui.column()
                .classes("items-center justify-center cursor-pointer flex-1 py-2 gap-0.5")
                .style("min-width: 48px; min-height: 48px")
                .on("click", lambda route=item["route"]: ui.navigate.to(route))
            ):
                # Icon with active state
                icon_color = "text-primary" if is_active else "text-gray-600"
                ui.icon(item["icon"], size="24px").classes(icon_color)

                # Label with active state
                label_classes = "text-xs font-medium" + (" text-primary" if is_active else " text-gray-600")
                ui.label(item["label"]).classes(label_classes)


def create_mobile_page_container() -> Any:
    """Create container for mobile page with bottom navigation spacing.

    Returns the column container that should be used for page content.
    """
    # Main content area with padding for bottom nav (56px + 16px spacing)
    return ui.column().classes("w-full p-4").style("padding-bottom: 72px")
