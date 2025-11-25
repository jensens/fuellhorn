"""Locations Page - Admin page for managing storage locations (Mobile-First).

Based on Issue #24: Locations Page - Liste aller Lagerorte
"""

from ...auth import Permission
from ...auth import require_permissions
from ...database import get_session
from ...models.location import LocationType
from ...services import location_service
from ..components import create_mobile_page_container
from nicegui import ui


def _get_location_type_label(location_type: LocationType) -> str:
    """Get German label for location type."""
    labels = {
        LocationType.FROZEN: "Gefroren",
        LocationType.CHILLED: "Gekühlt",
        LocationType.AMBIENT: "Raumtemperatur",
    }
    return labels.get(location_type, str(location_type.value))


def _get_location_type_color(location_type: LocationType) -> str:
    """Get color for location type badge."""
    colors = {
        LocationType.FROZEN: "blue",
        LocationType.CHILLED: "cyan",
        LocationType.AMBIENT: "orange",
    }
    return colors.get(location_type, "gray")


def _get_location_type_icon(location_type: LocationType) -> str:
    """Get icon for location type."""
    icons = {
        LocationType.FROZEN: "ac_unit",
        LocationType.CHILLED: "kitchen",
        LocationType.AMBIENT: "shelves",
    }
    return icons.get(location_type, "place")


@ui.page("/admin/locations")
@require_permissions(Permission.CONFIG_MANAGE)
def locations_page() -> None:
    """Locations management page (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/settings")).props("flat round color=gray-7")
            ui.label("Lagerorte").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        ui.label("Lagerorte verwalten").classes("text-h6 font-semibold mb-3")

        with next(get_session()) as session:
            locations = location_service.get_all_locations(session)

            if locations:
                # Display locations as cards
                for location in locations:
                    with ui.card().classes("w-full mb-2"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                # Type icon
                                ui.icon(
                                    _get_location_type_icon(location.location_type),
                                    size="24px",
                                ).classes(f"text-{_get_location_type_color(location.location_type)}")
                                # Location name
                                ui.label(location.name).classes("font-medium text-lg")
                            # Type badge and status
                            with ui.row().classes("items-center gap-2"):
                                # Type badge
                                ui.badge(
                                    _get_location_type_label(location.location_type),
                                    color=_get_location_type_color(location.location_type),
                                ).classes("text-xs")
                                # Inactive badge (if not active)
                                if not location.is_active:
                                    ui.badge("Inaktiv", color="red").classes("text-xs")
            else:
                # Empty state
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full items-center py-8"):
                        ui.icon("place", size="48px").classes("text-gray-400 mb-2")
                        ui.label("Keine Lagerorte vorhanden").classes("text-gray-600 text-center")
                        ui.label("Lagerorte helfen beim Organisieren des Vorrats.").classes(
                            "text-sm text-gray-500 text-center"
                        )
