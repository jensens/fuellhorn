"""Recently Added Section Component for Dashboard.

Issue #248: Show last N recently added items with relative date and location icon.

Based on mockup:
┌─────────────────────────────────────────┐
│ Tomatensoße        Heute    🧊 TK   │
│ Apfelmus           Gestern  🏠 Vorr │
│ Hackfleisch        Mo       🧊 TK   │
└─────────────────────────────────────────┘
"""

from ...models.item import Item
from ...models.location import Location
from ...models.location import LocationType
from ...services import item_service
from ...services.expiry_service import get_entered_dates
from ..theme import Colors
from ..theme.icons import create_icon
from ..utils.date_utils import format_relative_date
from .item_card import get_location_icon_name
from collections.abc import Callable
from nicegui import ui
from sqlmodel import Session
from sqlmodel import col
from sqlmodel import select


# Location type abbreviations (German)
LOCATION_TYPE_ABBR: dict[LocationType, str] = {
    LocationType.FROZEN: "TK",
    LocationType.CHILLED: "Kühl",
    LocationType.AMBIENT: "Vorr",
}


def get_location_abbreviation(location: Location) -> str:
    """Get abbreviated location name based on type.

    For recognized types returns short abbreviation,
    otherwise returns first 4 characters of location name.
    """
    return LOCATION_TYPE_ABBR.get(location.location_type, location.name[:4])


def create_recently_added_row(
    item: Item,
    location: Location,
    on_click: Callable[[Item], None] | None = None,
) -> None:
    """Create a compact row for a recently added item.

    Layout: [Name] [Relative Date] [Location Icon + Abbr]

    Args:
        item: The item to display
        location: The item's storage location
        on_click: Optional callback when row is clicked
    """
    location_color = location.color or Colors.DEFAULT_GRAY
    icon_name = get_location_icon_name(location.location_type)
    location_abbr = get_location_abbreviation(location)
    relative_date = format_relative_date(item.created_at)

    # Row container with click handler
    row_classes = (
        "flex items-center justify-between min-h-[44px] py-2 px-3 cursor-pointer hover:bg-gray-50 rounded-lg "
        "transition-colors"
    )

    with (
        ui.element("div")
        .classes(row_classes)
        .mark(f"recent-item-{item.id}")
        .on("click", lambda: on_click(item) if on_click else None)
    ):
        # Left: Product name (truncated) + entered dates (Issue #342)
        with ui.column().classes("gap-0 flex-1 mr-3").style("min-width: 0;"):
            ui.label(item.product_name).classes("text-sm text-charcoal font-medium truncate")
            entered = " · ".join(f"{label} {value:%d.%m.%Y}" for label, value in get_entered_dates(item))
            if entered:
                ui.label(entered).classes("text-xs text-stone truncate")

        # Center: Relative date
        ui.label(relative_date).classes("text-xs text-stone whitespace-nowrap mr-3")

        # Right: Location icon + abbreviation
        with ui.row().classes("items-center gap-1 flex-shrink-0"):
            create_icon(icon_name, size="14px").style(f"color: {location_color};")
            ui.label(location_abbr).classes("text-xs text-stone")


def create_recently_added_section(
    session: Session,
    limit: int = 5,
    on_item_click: Callable[[Item], None] | None = None,
) -> None:
    """Create the 'Kürzlich hinzugefügt' section for the dashboard.

    Shows last N recently added items in a compact list format.
    Section is hidden when no items exist.

    Args:
        session: Database session
        limit: Maximum number of items to show (default 5)
        on_item_click: Optional callback when an item is clicked
    """
    # Get recently added items
    recently_added = item_service.get_recently_added_items(session, limit=limit)

    # Hide section if no items
    if not recently_added:
        return

    # Section title
    ui.label("Kürzlich hinzugefügt").classes("sp-page-title text-base mb-3 mt-6")

    # Lagerorte aller Zeilen in einer Abfrage statt einer pro Zeile (#393)
    location_ids = {item.location_id for item in recently_added}
    locations = {
        location.id: location
        for location in session.exec(select(Location).where(col(Location.id).in_(location_ids))).all()
    }

    # Compact card container for the list
    with ui.card().classes("sp-dashboard-card w-full p-0 overflow-hidden"):
        for item in recently_added:
            location = locations.get(item.location_id) or Location(
                id=item.location_id,
                name=f"Lagerort {item.location_id}",
                location_type=LocationType.AMBIENT,
                created_by=1,
            )

            # Default click handler: open the edit page (there is no detail page, Issue #366)
            def handle_click(i: Item = item) -> None:
                if on_item_click:
                    on_item_click(i)
                else:
                    ui.navigate.to(f"/items/{i.id}/edit")

            create_recently_added_row(item, location, on_click=handle_click)
