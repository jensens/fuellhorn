"""Locations Page - Admin page for managing storage locations (Mobile-First).

Based on Issue #24: Locations Page - Liste aller Lagerorte
Issue #25: Locations Page - Lagerort erstellen
Issue #26: Locations Page - Lagerort bearbeiten
Issue #27: Locations Page - Lagerort löschen
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.decorators import with_permission_check
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.location import Location
from ...models.location import LocationType
from ...services import item_types
from ...services import location_service
from ..components import create_mobile_page_container
from ..components.color_picker import create_color_picker
from ..components.confirm_delete import open_confirm_delete_dialog
from ..components.errors import show_service_error
from ..theme.icons import create_icon
from nicegui import ui


def _get_location_type_label(location_type: LocationType) -> str:
    """Get German label for location type (eine Quelle: services/item_types, #398)."""
    return item_types.LOCATION_TYPE_LABELS.get(location_type, str(location_type.value))


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

    # Header (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with (
                ui.button(on_click=lambda: ui.navigate.to("/admin/settings")).classes("sp-back-btn").props("flat round")
            ):
                create_icon("actions/back", size="24px")
            ui.label("Lagerorte").classes("sp-page-title")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Section header with "Neuer Lagerort" button (Solarpunk theme)
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Lagerorte verwalten").classes("text-h6 font-semibold text-fern")
            with (
                ui.button(on_click=_open_create_dialog)
                .classes("sp-btn-primary")
                .props("size=sm")
                .mark("new-location-button")
            ):
                with ui.row().classes("items-center gap-2"):
                    create_icon("navigation/add", size="20px")
                    ui.label("Neuer Lagerort")

        with next(get_session()) as session:
            locations = location_service.get_all_locations(session)

            if locations:
                # Display locations as admin list items (Solarpunk theme)
                for location in locations:
                    with ui.element("div").classes("sp-admin-list-item w-full"):
                        # Left side: color + name
                        with ui.row().classes("items-center gap-3 flex-1"):
                            # Color indicator (Solarpunk admin color dot)
                            if location.color:
                                ui.element("div").classes("sp-admin-color-dot").style(
                                    f"background-color: {location.color}"
                                )
                            else:
                                ui.icon(
                                    _get_location_type_icon(location.location_type),
                                    size="24px",
                                ).classes(f"text-{_get_location_type_color(location.location_type)}")
                            # Location name
                            ui.label(location.name).classes("font-medium text-lg text-charcoal")
                        # Right side: Type badge, status, edit and delete buttons
                        with ui.row().classes("items-center gap-2"):
                            # Type badge
                            ui.badge(
                                _get_location_type_label(location.location_type),
                                color=_get_location_type_color(location.location_type),
                            ).classes("text-xs")
                            # Inactive badge (if not active)
                            if not location.is_active:
                                ui.badge("Inaktiv", color="red").classes("text-xs")
                            # Action buttons (Solarpunk theme)
                            with ui.row().classes("sp-admin-actions items-center gap-1"):
                                # Edit button
                                with (
                                    ui.button(
                                        on_click=lambda loc=location: _open_edit_dialog(loc),
                                    )
                                    .props("flat round size=sm")
                                    .classes("edit min-w-0")
                                    .mark("edit")
                                ):
                                    create_icon("actions/edit", size="20px")
                                # Delete button
                                location_id = location.id
                                assert location_id is not None  # Loaded from DB
                                location_name = location.name
                                with (
                                    ui.button(
                                        on_click=lambda lid=location_id, ln=location_name: _open_delete_dialog(lid, ln),
                                    )
                                    .props("flat round size=sm")
                                    .classes("delete min-w-0")
                                    .mark(f"delete-{location_name}")
                                ):
                                    create_icon("actions/delete", size="20px")
            else:
                # Empty state (Solarpunk theme)
                with ui.card().classes("sp-dashboard-card w-full"):
                    with ui.column().classes("w-full items-center py-8"):
                        ui.icon("place", size="48px").classes("text-stone mb-2")
                        ui.label("Keine Lagerorte vorhanden").classes("text-charcoal text-center")
                        ui.label("Lagerorte helfen beim Organisieren des Vorrats.").classes(
                            "text-sm text-stone text-center"
                        )


def _open_edit_dialog(location: Location) -> None:
    """Open dialog to edit an existing location."""
    # Location type options
    type_options = dict(item_types.LOCATION_TYPE_LABELS)

    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-md"):
        ui.label("Lagerort bearbeiten").classes("text-h6 font-semibold mb-4 text-fern")

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

        color_input = create_color_picker(location.color)

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
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(Permission.CONFIG_MANAGE)  # Laufzeit-Check (#381)
            def save_location() -> None:
                """Validate and save the location changes."""
                name = name_input.value.strip() if name_input.value else ""
                location_type = type_select.value
                description = description_input.value.strip() if description_input.value else None
                color = color_input.value if color_input.value else None
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
                            color=color,
                        )
                    ui.notify(f"Lagerort '{name}' aktualisiert", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/locations")
                except Exception as e:
                    # Duplikate meldet der Service typisiert, Unerwartetes landet im Log (#382)
                    show_service_error(e, error_label)

            ui.button("Speichern", on_click=save_location).classes("sp-btn-primary")

    dialog.open()


def _open_create_dialog() -> None:
    """Open dialog to create a new location."""
    # Location type options
    type_options = dict(item_types.LOCATION_TYPE_LABELS)

    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-md"):
        ui.label("Neuen Lagerort erstellen").classes("text-h6 font-semibold mb-4 text-fern")

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
            .classes("w-full mb-2")
            .props("outlined")
        )

        color_input = create_color_picker()

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons (Solarpunk theme)
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(Permission.CONFIG_MANAGE)  # Laufzeit-Check (#381)
            def save_location() -> None:
                """Validate and save the new location."""
                name = name_input.value.strip() if name_input.value else ""
                location_type = type_select.value
                description = description_input.value.strip() if description_input.value else None
                color = color_input.value if color_input.value else None

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
                            color=color,
                        )
                    ui.notify(f"Lagerort '{name}' erstellt", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/locations")
                except Exception as e:
                    # Duplikate meldet der Service typisiert, Unerwartetes landet im Log (#382)
                    show_service_error(e, error_label)

            ui.button("Speichern", on_click=save_location).classes("sp-btn-primary")

    dialog.open()


def _open_delete_dialog(location_id: int, location_name: str) -> None:
    """Open confirmation dialog to delete a location."""

    def delete() -> None:
        with next(get_session()) as session:
            # Referenz-Prüfung liegt im Service (#379)
            location_service.delete_location(session=session, id=location_id)

    open_confirm_delete_dialog(
        title="Lagerort löschen",
        question=f"Möchten Sie den Lagerort '{location_name}' wirklich löschen?",
        permission=Permission.CONFIG_MANAGE,
        on_confirm=delete,
        success_message="Lagerort gelöscht",
        redirect="/admin/locations",
    )
