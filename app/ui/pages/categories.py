"""Categories Page - Admin page for managing categories (Mobile-First).

Based on Issue #20: Categories Page - Liste aller Kategorien
Issue #21: Categories Page - Kategorie erstellen
Issue #22: Categories Page - Kategorie bearbeiten
Issue #23: Categories Page - Kategorie löschen
Issue #107: Haltbarkeiten verwalten
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.category_shelf_life import StorageType
from ...services import category_service
from ...services import shelf_life_service
from ..components import create_mobile_page_container
from nicegui import ui


# Storage type labels for UI
STORAGE_TYPE_LABELS = {
    StorageType.FROZEN: "Gefroren",
    StorageType.CHILLED: "Gekühlt",
    StorageType.AMBIENT: "Raumtemperatur",
}


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


def _move_category_up(category_id: int) -> None:
    """Move a category up in the sort order."""
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)
        category_ids = [c.id for c in categories if c.id is not None]

        # Find current position
        try:
            current_index = category_ids.index(category_id)
        except ValueError:
            return

        # Can't move up if already first
        if current_index == 0:
            return

        # Swap with previous
        category_ids[current_index], category_ids[current_index - 1] = (
            category_ids[current_index - 1],
            category_ids[current_index],
        )

        # Update order in database
        category_service.update_category_order(session, category_ids)

    # Refresh page
    ui.navigate.to("/admin/categories")


def _move_category_down(category_id: int) -> None:
    """Move a category down in the sort order."""
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)
        category_ids = [c.id for c in categories if c.id is not None]

        # Find current position
        try:
            current_index = category_ids.index(category_id)
        except ValueError:
            return

        # Can't move down if already last
        if current_index >= len(category_ids) - 1:
            return

        # Swap with next
        category_ids[current_index], category_ids[current_index + 1] = (
            category_ids[current_index + 1],
            category_ids[current_index],
        )

        # Update order in database
        category_service.update_category_order(session, category_ids)

    # Refresh page
    ui.navigate.to("/admin/categories")


def _render_categories_list() -> None:
    """Render the list of categories with reorder buttons."""
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)

        if categories:
            # Display categories as cards with reorder buttons
            for index, category in enumerate(categories):
                # Get shelf lives for this category
                cat_id = category.id
                if cat_id is None:
                    continue
                shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(session, cat_id)
                shelf_life_dict = {sl.storage_type: sl for sl in shelf_lives}

                is_first = index == 0
                is_last = index == len(categories) - 1

                with ui.card().classes("w-full mb-2"):
                    with ui.row().classes("w-full items-center justify-between"):
                        # Left side: reorder buttons + color + name
                        with ui.row().classes("items-center gap-2"):
                            # Reorder buttons (up/down)
                            with ui.column().classes("gap-0"):
                                ui.button(
                                    icon="keyboard_arrow_up",
                                    on_click=lambda cid=cat_id: _move_category_up(cid),
                                ).props(f"flat round dense size=xs {'disabled' if is_first else ''}").classes(
                                    "h-5"
                                ).mark(f"move-up-{category.name}")
                                ui.button(
                                    icon="keyboard_arrow_down",
                                    on_click=lambda cid=cat_id: _move_category_down(cid),
                                ).props(f"flat round dense size=xs {'disabled' if is_last else ''}").classes(
                                    "h-5"
                                ).mark(f"move-down-{category.name}")

                            # Color indicator
                            if category.color:
                                ui.element("div").classes("w-6 h-6 rounded-full").style(
                                    f"background-color: {category.color}"
                                )
                            else:
                                ui.element("div").classes("w-6 h-6 rounded-full bg-gray-300")
                            # Category name
                            ui.label(category.name).classes("font-medium text-lg")

                        # Right side: shelf life info and buttons
                        with ui.row().classes("items-center gap-2"):
                            # Shelf life info (compact display)
                            _render_shelf_life_badges(shelf_life_dict)

                            # Capture category data for the closures
                            cat_name = category.name
                            cat_color = category.color

                            # Edit button
                            ui.button(
                                icon="edit",
                                on_click=lambda cid=cat_id, cn=cat_name, cc=cat_color: _open_edit_dialog(cid, cn, cc),
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


def _render_shelf_life_badges(shelf_life_dict: dict) -> None:
    """Render compact shelf life badges."""
    for storage_type in [StorageType.FROZEN, StorageType.CHILLED, StorageType.AMBIENT]:
        if storage_type in shelf_life_dict:
            sl = shelf_life_dict[storage_type]
            # Show as compact badge with icon
            icon = (
                "ac_unit"
                if storage_type == StorageType.FROZEN
                else ("kitchen" if storage_type == StorageType.CHILLED else "home")
            )
            with ui.row().classes("items-center gap-1"):
                ui.icon(icon, size="16px").classes("text-gray-500")
                ui.label(f"{sl.months_min}-{sl.months_max}").classes("text-xs text-gray-600")


def _open_create_dialog() -> None:
    """Open dialog to create a new category."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg"):
        ui.label("Neue Kategorie erstellen").classes("text-h6 font-semibold mb-4")

        # Name input (required)
        name_input = ui.input(label="Name", placeholder="z.B. Gemüse").classes("w-full mb-2").props("outlined")

        # Color input (optional)
        color_input = ui.color_input(label="Farbe").classes("w-full mb-4")

        # Shelf life section
        ui.label("Haltbarkeit (Monate)").classes("text-subtitle1 font-medium mb-2")

        # Store input references
        shelf_life_inputs: dict[StorageType, dict] = {}

        for storage_type in [StorageType.FROZEN, StorageType.CHILLED, StorageType.AMBIENT]:
            label = STORAGE_TYPE_LABELS[storage_type]

            with ui.row().classes("w-full items-center gap-2 mb-2"):
                ui.label(label).classes("w-28 text-sm")
                ui.label("Min").classes("text-xs text-gray-500")
                min_input = (
                    ui.number(
                        value=None,
                        min=1,
                        max=36,
                    )
                    .classes("w-16")
                    .props("dense outlined")
                    .mark(f"create-{storage_type.value}-min")
                )
                ui.label("Max").classes("text-xs text-gray-500")
                max_input = (
                    ui.number(
                        value=None,
                        min=1,
                        max=36,
                    )
                    .classes("w-16")
                    .props("dense outlined")
                    .mark(f"create-{storage_type.value}-max")
                )
                ui.label("Quelle").classes("text-xs text-gray-500")
                source_input = (
                    ui.input(
                        value="",
                        placeholder="URL",
                    )
                    .classes("flex-1")
                    .props("dense outlined")
                    .mark(f"create-{storage_type.value}-source")
                )

                shelf_life_inputs[storage_type] = {
                    "min": min_input,
                    "max": max_input,
                    "source": source_input,
                }

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

                # Validate shelf life min <= max
                for storage_type, inputs in shelf_life_inputs.items():
                    min_val = inputs["min"].value
                    max_val = inputs["max"].value

                    # Skip if both empty
                    if min_val is None and max_val is None:
                        continue

                    # Both must be set if one is set
                    if (min_val is None) != (max_val is None):
                        label = STORAGE_TYPE_LABELS[storage_type]
                        error_label.set_text(f"{label}: Min und Max müssen beide gesetzt sein")
                        error_label.set_visibility(True)
                        return

                    # Min must be <= Max
                    if min_val is not None and max_val is not None and min_val > max_val:
                        error_label.set_text("Min muss <= Max sein")
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
                        category = category_service.create_category(
                            session=session,
                            name=name,
                            created_by=current_user.id,
                            color=color,
                        )

                        # Save shelf lives if provided
                        if category.id is not None:
                            for storage_type, inputs in shelf_life_inputs.items():
                                min_val = inputs["min"].value
                                max_val = inputs["max"].value
                                source_val = inputs["source"].value.strip() if inputs["source"].value else None

                                if min_val is not None and max_val is not None:
                                    shelf_life_service.create_or_update_shelf_life(
                                        session=session,
                                        category_id=category.id,
                                        storage_type=storage_type,
                                        months_min=int(min_val),
                                        months_max=int(max_val),
                                        source_url=source_val,
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
) -> None:
    """Open dialog to edit an existing category with shelf life configuration."""
    # Load existing shelf lives
    with next(get_session()) as session:
        shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(session, category_id)
        existing_shelf_lives = {sl.storage_type: sl for sl in shelf_lives}

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg"):
        ui.label("Kategorie bearbeiten").classes("text-h6 font-semibold mb-4")

        # Name input (pre-filled)
        name_input = (
            ui.input(label="Name", value=current_name).classes("w-full mb-2").props("outlined").mark("edit-name")
        )

        # Color input (pre-filled)
        color_input = ui.color_input(label="Farbe", value=current_color or "").classes("w-full mb-4")

        # Shelf life section
        ui.label("Haltbarkeit (Monate)").classes("text-subtitle1 font-medium mb-2")

        # Store input references
        shelf_life_inputs: dict[StorageType, dict] = {}

        for storage_type in [StorageType.FROZEN, StorageType.CHILLED, StorageType.AMBIENT]:
            label = STORAGE_TYPE_LABELS[storage_type]
            existing = existing_shelf_lives.get(storage_type)

            with ui.row().classes("w-full items-center gap-2 mb-2"):
                ui.label(label).classes("w-28 text-sm")
                ui.label("Min").classes("text-xs text-gray-500")
                min_input = (
                    ui.number(
                        value=existing.months_min if existing else None,
                        min=1,
                        max=36,
                    )
                    .classes("w-16")
                    .props("dense outlined")
                    .mark(f"{storage_type.value}-min")
                )
                ui.label("Max").classes("text-xs text-gray-500")
                max_input = (
                    ui.number(
                        value=existing.months_max if existing else None,
                        min=1,
                        max=36,
                    )
                    .classes("w-16")
                    .props("dense outlined")
                    .mark(f"{storage_type.value}-max")
                )
                ui.label("Quelle").classes("text-xs text-gray-500")
                source_input = (
                    ui.input(
                        value=existing.source_url or "" if existing else "",
                        placeholder="URL",
                    )
                    .classes("flex-1")
                    .props("dense outlined")
                    .mark(f"{storage_type.value}-source")
                )

                shelf_life_inputs[storage_type] = {
                    "min": min_input,
                    "max": max_input,
                    "source": source_input,
                }

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

                # Validate shelf life min <= max
                for storage_type, inputs in shelf_life_inputs.items():
                    min_val = inputs["min"].value
                    max_val = inputs["max"].value

                    # Skip if both empty
                    if min_val is None and max_val is None:
                        continue

                    # Both must be set if one is set
                    if (min_val is None) != (max_val is None):
                        label = STORAGE_TYPE_LABELS[storage_type]
                        error_label.set_text(f"{label}: Min und Max müssen beide gesetzt sein")
                        error_label.set_visibility(True)
                        return

                    # Min must be <= Max
                    if min_val is not None and max_val is not None and min_val > max_val:
                        error_label.set_text("Min muss <= Max sein")
                        error_label.set_visibility(True)
                        return

                try:
                    with next(get_session()) as session:
                        # Update category
                        category_service.update_category(
                            session=session,
                            id=category_id,
                            name=name if name != current_name else None,
                            color=color,
                        )

                        # Update shelf lives
                        for storage_type, inputs in shelf_life_inputs.items():
                            min_val = inputs["min"].value
                            max_val = inputs["max"].value
                            source_val = inputs["source"].value.strip() if inputs["source"].value else None

                            existing = existing_shelf_lives.get(storage_type)

                            if min_val is not None and max_val is not None:
                                # Create or update
                                shelf_life_service.create_or_update_shelf_life(
                                    session=session,
                                    category_id=category_id,
                                    storage_type=storage_type,
                                    months_min=int(min_val),
                                    months_max=int(max_val),
                                    source_url=source_val,
                                )
                            elif existing and existing.id is not None:
                                # Delete if existed but now cleared
                                shelf_life_service.delete_shelf_life(session, existing.id)

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
                        # First delete all shelf lives for this category
                        shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(session, category_id)
                        for sl in shelf_lives:
                            if sl.id is not None:
                                shelf_life_service.delete_shelf_life(session, sl.id)

                        # Then delete the category
                        category_service.delete_category(session=session, id=category_id)
                    ui.notify("Kategorie gelöscht", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/categories")
                except Exception as e:
                    error_label.set_text(str(e))
                    error_label.set_visibility(True)

            ui.button("Löschen", on_click=confirm_delete).props("color=red")

    dialog.open()
