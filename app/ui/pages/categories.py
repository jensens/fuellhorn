"""Categories Page - Admin page for managing categories (Mobile-First).

Based on Issue #20: Categories Page - Liste aller Kategorien
Issue #21: Categories Page - Kategorie erstellen
Issue #22: Categories Page - Kategorie bearbeiten
Issue #23: Categories Page - Kategorie löschen
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...services import category_service
from ..components import create_mobile_page_container
from nicegui import ui


@ui.page("/admin/categories")
@require_permissions(Permission.CONFIG_MANAGE)
def categories_page() -> None:
    """Categories management page (Mobile-First)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin/settings")).props(
                "flat round color=gray-7"
            )
            ui.label("Kategorien").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Section header with "Neue Kategorie" button
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Kategorien verwalten").classes("text-h6 font-semibold")
            ui.button("Neue Kategorie", icon="add", on_click=_open_create_dialog).props("color=primary size=sm")

        _render_categories_list()


def _render_categories_list() -> None:
    """Render the list of categories."""
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)

        if categories:
            # Display categories as cards
            for category in categories:
                with ui.card().classes("w-full mb-2"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-3"):
                            # Color indicator
                            if category.color:
                                ui.element("div").classes("w-6 h-6 rounded-full").style(
                                    f"background-color: {category.color}"
                                )
                            else:
                                ui.element("div").classes("w-6 h-6 rounded-full bg-gray-300")
                            # Category name
                            ui.label(category.name).classes("font-medium text-lg")

                        # Right side: freeze time and edit button
                        with ui.row().classes("items-center gap-2"):
                            # Freeze time info (if set)
                            if category.freeze_time_months:
                                ui.label(f"{category.freeze_time_months} Mon.").classes("text-sm text-gray-600")

                            # Capture category data for the closures
                            cat_id = category.id
                            cat_name = category.name
                            cat_color = category.color
                            cat_freeze_time = category.freeze_time_months

                            # Edit button
                            ui.button(
                                icon="edit",
                                on_click=lambda cid=cat_id,
                                cn=cat_name,
                                cc=cat_color,
                                cft=cat_freeze_time: _open_edit_dialog(cid, cn, cc, cft),
                            ).props("flat round color=grey-7 size=sm").mark(f"edit-{cat_name}")

                            # Delete button
                            ui.button(
                                icon="delete",
                                on_click=lambda cid=cat_id, cn=cat_name: _open_delete_dialog(cid, cn),
                            ).props("flat round color=red-7 size=sm").mark(f"delete-{cat_name}")
        else:
            # Empty state
            with ui.card().classes("w-full"):
                with ui.column().classes("w-full items-center py-8"):
                    ui.icon("category", size="48px").classes("text-gray-400 mb-2")
                    ui.label("Keine Kategorien vorhanden").classes("text-gray-600 text-center")
                    ui.label("Kategorien helfen beim Organisieren des Vorrats.").classes(
                        "text-sm text-gray-500 text-center"
                    )


def _open_create_dialog() -> None:
    """Open dialog to create a new category."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Neue Kategorie erstellen").classes("text-h6 font-semibold mb-4")

        # Name input (required)
        name_input = ui.input(label="Name", placeholder="z.B. Gemüse").classes("w-full mb-2").props("outlined")

        # Color input (optional)
        color_input = ui.color_input(label="Farbe").classes("w-full mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_category() -> None:
                """Validate and save the new category."""
                name = name_input.value.strip() if name_input.value else ""
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
                        category_service.create_category(
                            session=session,
                            name=name,
                            created_by=current_user.id,
                            color=color,
                        )
                    ui.notify(f"Kategorie '{name}' erstellt", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/categories")
                except ValueError as e:
                    # Handle duplicate name error
                    error_msg = str(e)
                    if "already exists" in error_msg:
                        error_label.set_text(f"Kategorie '{name}' bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_category).props("color=primary")

    dialog.open()


def _open_edit_dialog(
    category_id: int,
    current_name: str,
    current_color: str | None,
    current_freeze_time: int | None,
) -> None:
    """Open dialog to edit an existing category."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Kategorie bearbeiten").classes("text-h6 font-semibold mb-4")

        # Name input (pre-filled)
        name_input = (
            ui.input(label="Name", value=current_name).classes("w-full mb-2").props("outlined").mark("edit-name")
        )

        # Color input (pre-filled)
        color_input = ui.color_input(label="Farbe", value=current_color or "").classes("w-full mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_changes() -> None:
                """Validate and save the category changes."""
                name = name_input.value.strip() if name_input.value else ""
                color = color_input.value if color_input.value else None

                # Validation: name is required
                if not name:
                    error_label.set_text("Name ist erforderlich")
                    error_label.set_visibility(True)
                    return

                try:
                    with next(get_session()) as session:
                        category_service.update_category(
                            session=session,
                            id=category_id,
                            name=name if name != current_name else None,
                            color=color,
                        )
                    ui.notify(f"Kategorie '{name}' aktualisiert", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/categories")
                except ValueError as e:
                    # Handle duplicate name error
                    error_msg = str(e)
                    if "already exists" in error_msg:
                        error_label.set_text(f"Kategorie '{name}' bereits vorhanden")
                    else:
                        error_label.set_text(error_msg)
                    error_label.set_visibility(True)

            ui.button("Speichern", on_click=save_changes).props("color=primary")

    dialog.open()


def _open_delete_dialog(category_id: int, category_name: str) -> None:
    """Open confirmation dialog to delete a category."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Kategorie löschen").classes("text-h6 font-semibold mb-4")

        # Warning message
        ui.label(f"Möchten Sie die Kategorie '{category_name}' wirklich löschen?").classes("mb-2")
        ui.label("Diese Aktion kann nicht rückgängig gemacht werden.").classes("text-sm text-red-600 mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def confirm_delete() -> None:
                """Perform the deletion."""
                try:
                    with next(get_session()) as session:
                        category_service.delete_category(session=session, id=category_id)
                    ui.notify("Kategorie gelöscht", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/categories")
                except Exception as e:
                    error_label.set_text(str(e))
                    error_label.set_visibility(True)

            ui.button("Löschen", on_click=confirm_delete).props("color=red")

    dialog.open()
