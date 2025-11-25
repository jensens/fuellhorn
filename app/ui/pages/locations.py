"""Locations Page - Admin page for managing storage locations (Mobile-First).

Based on Issue #24: Locations Page - Liste aller Lagerorte
Issue #25: Locations Page - Lagerort erstellen
Issue #26: Locations Page - Lagerort bearbeiten
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.location import Location
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
        # Section header with "Neuer Lagerort" button
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Lagerorte verwalten").classes("text-h6 font-semibold")
            ui.button("Neuer Lagerort", icon="add", on_click=_open_create_dialog).props("color=primary size=sm")

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
                            # Type badge, status and edit button
                            with ui.row().classes("items-center gap-2"):
                                # Type badge
                                ui.badge(
                                    _get_location_type_label(location.location_type),
                                    color=_get_location_type_color(location.location_type),
                                ).classes("text-xs")
                                # Inactive badge (if not active)
                                if not location.is_active:
                                    ui.badge("Inaktiv", color="red").classes("text-xs")
                                # Edit button
                                ui.button(
                                    icon="edit",
                                    on_click=lambda loc=location: _open_edit_dialog(loc),
                                ).props("flat round size=sm").classes("min-w-0")
            else:
                # Empty state
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full items-center py-8"):
                        ui.icon("place", size="48px").classes("text-gray-400 mb-2")
                        ui.label("Keine Lagerorte vorhanden").classes("text-gray-600 text-center")
                        ui.label("Lagerorte helfen beim Organisieren des Vorrats.").classes(
                            "text-sm text-gray-500 text-center"
                        )


def _open_edit_dialog(location: Location) -> None:
    """Open dialog to edit an existing location."""
    # Location type options
    type_options = {
        LocationType.FROZEN: "Gefroren",
        LocationType.CHILLED: "Gekühlt",
        LocationType.AMBIENT: "Raumtemperatur",
    }

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Lagerort bearbeiten").classes("text-h6 font-semibold mb-4")

        # Name input (required, pre-filled)
        name_input = (
            ui.input(
                label="Name",
                value=location.name,
            )
            .classes("w-full mb-2")
            .props("outlined")
            .mark("name-input")
        )

        # Location type select (pre-filled)
        type_select = (
            ui.select(
                label="Typ",
                options=type_options,
                value=location.location_type,
            )
            .classes("w-full mb-2")
            .props("outlined")
        )

        # Description input (optional, pre-filled)
        description_input = (
            ui.input(
                label="Beschreibung",
                value=location.description or "",
            )
            .classes("w-full mb-2")
            .props("outlined")
        )

        # Active status checkbox (pre-filled)
        is_active_checkbox = ui.checkbox(
            "Aktiv",
            value=location.is_active,
        ).classes("mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_location() -> None:
                """Validate and save the location changes."""
                name = name_input.value.strip() if name_input.value else ""
                location_type = type_select.value
                description = description_input.value.strip() if description_input.value else None
                is_active = is_active_checkbox.value

                # Validation: name is required
                if not name:
                    error_label.set_text("Name ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Safety check - location should always have an id from DB
                if location.id is None:
                    error_label.set_text("Ungültige Lagerort-ID")
                    error_label.set_visibility(True)
                    return

                try:
                    with next(get_session()) as session:
                        location_service.update_location(
                            session=session,
                            id=location.id,
                            name=name,
                            location_type=location_type,
                            description=description,
                            is_active=is_active,
                        )
                    ui.notify(f"Lagerort '{name}' aktualisiert", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/locations")
                except ValueError as e:
                    # Handle duplicate name error
                    error_msg = str(e)
                    if "already exists" in error_msg:
                        error_label.set_text(f"Lagerort '{name}' bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_location).props("color=primary")

    dialog.open()


def _open_create_dialog() -> None:
    """Open dialog to create a new location."""
    # Location type options
    type_options = {
        LocationType.FROZEN: "Gefroren",
        LocationType.CHILLED: "Gekühlt",
        LocationType.AMBIENT: "Raumtemperatur",
    }

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Neuen Lagerort erstellen").classes("text-h6 font-semibold mb-4")

        # Name input (required)
        name_input = (
            ui.input(
                label="Name",
                placeholder="z.B. Gefrierschrank",
            )
            .classes("w-full mb-2")
            .props("outlined")
            .mark("create-name-input")
        )

        # Location type select (default: FROZEN)
        type_select = (
            ui.select(
                label="Typ",
                options=type_options,
                value=LocationType.FROZEN,
            )
            .classes("w-full mb-2")
            .props("outlined")
        )

        # Description input (optional)
        description_input = (
            ui.input(
                label="Beschreibung",
                placeholder="Optional",
            )
            .classes("w-full mb-4")
            .props("outlined")
        )

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_location() -> None:
                """Validate and save the new location."""
                name = name_input.value.strip() if name_input.value else ""
                location_type = type_select.value
                description = description_input.value.strip() if description_input.value else None

                # Validation: name is required
                if not name:
                    error_label.set_text("Name ist erforderlich")
                    error_label.set_visibility(True)
                    return

                # Get current user for created_by
                current_user = get_current_user()
                if current_user is None or current_user.id is None:
                    error_label.set_text("Nicht angemeldet")
                    error_label.set_visibility(True)
                    return

                try:
                    with next(get_session()) as session:
                        location_service.create_location(
                            session=session,
                            name=name,
                            location_type=location_type,
                            created_by=current_user.id,
                            description=description,
                        )
                    ui.notify(f"Lagerort '{name}' erstellt", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/locations")
                except ValueError as e:
                    # Handle duplicate name error
                    error_msg = str(e)
                    if "already exists" in error_msg:
                        error_label.set_text(f"Lagerort '{name}' bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_location).props("color=primary")

    dialog.open()
