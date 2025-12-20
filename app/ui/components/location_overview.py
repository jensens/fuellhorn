"""Location Overview Component for Dashboard.

Issue #246: Horizontal scrollable location chips with icons and item counts.
"""

from ...models.location import Location
from ...models.location import LocationType
from collections.abc import Sequence
from nicegui import ui


def get_location_type_icon(location_type: LocationType) -> str:
    """Get Material icon name for a location type.

    Args:
        location_type: The type of storage location

    Returns:
        Material icon name string
    """
    icons = {
        LocationType.FROZEN: "ac_unit",
        LocationType.CHILLED: "kitchen",
        LocationType.AMBIENT: "home",
    }
    return icons.get(location_type, "inventory_2")


def create_location_overview_chips(
    locations: Sequence[Location],
    item_counts: dict[int, int],
) -> ui.element:
    """Create horizontal scrollable location overview chips.

    Args:
        locations: List of Location objects from the database
        item_counts: Dictionary mapping location_id to item count

    Returns:
        The container element with all chips
    """
    # Horizontal scroll container
    with (
        ui.row()
        .classes("w-full overflow-x-auto flex-nowrap gap-3 pb-2")
        .style("scroll-snap-type: x mandatory;") as container
    ):
        for location in locations:
            if location.id is None:
                continue

            loc_id: int = location.id
            count = item_counts.get(loc_id, 0)
            icon = get_location_type_icon(location.location_type)
            color = location.color or "#6B7280"

            # Location chip card
            with (
                ui.card()
                .classes("sp-location-chip cursor-pointer flex-shrink-0")
                .style(f"scroll-snap-align: start; border-left: 3px solid {color};")
                .on(
                    "click",
                    lambda _, lid=loc_id: ui.navigate.to(f"/items?location={lid}"),
                )
            ):
                with ui.column().classes("items-center gap-1 p-3 min-w-[70px]"):
                    ui.icon(icon).classes("text-2xl text-stone")
                    ui.label(location.name).classes("text-xs font-medium text-charcoal whitespace-nowrap")
                    ui.label(str(count)).classes("text-lg font-bold text-leaf")

    return container
