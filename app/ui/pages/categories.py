"""Categories Page - Admin page for managing categories (Mobile-First).

Based on Issue #20: Categories Page - Liste aller Kategorien
Issue #21: Categories Page - Kategorie erstellen
Issue #22: Categories Page - Kategorie bearbeiten
Issue #23: Categories Page - Kategorie löschen
Issue #107: Haltbarkeiten verwalten
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.decorators import with_permission_check
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.category import Category
from ...models.category_shelf_life import StorageType
from ...services import category_service
from ...services import shelf_life_service
from ...services.sentinels import UNSET
from ...services.sentinels import Unset
from ..components import create_mobile_page_container
from ..components.errors import show_service_error
from ..theme.icons import create_icon
from collections import defaultdict
from nicegui import ui
from sqlmodel import Session


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

    # Header (Solarpunk theme)
    with ui.row().classes("sp-page-header w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2"):
            with (
                ui.button(on_click=lambda: ui.navigate.to("/admin/settings")).classes("sp-back-btn").props("flat round")
            ):
                create_icon("actions/back", size="24px")
            ui.label("Kategorien").classes("sp-page-title")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Section header with "Neue Kategorie" button (Solarpunk theme)
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Kategorien verwalten").classes("text-h6 font-semibold text-fern")
            with (
                ui.button(on_click=_open_create_dialog)
                .classes("sp-btn-primary")
                .props("size=sm")
                .mark("new-category-button")
            ):
                with ui.row().classes("items-center gap-2"):
                    create_icon("navigation/add", size="20px")
                    ui.label("Neue Kategorie")

        _render_categories_list()


def _sibling_ids(session: Session, category_id: int) -> list[int]:
    """IDs der Geschwister (gleicher Parent) in Sortierreihenfolge; Hoch/Runter bleibt in der Gruppe (#395)."""
    categories = category_service.get_all_categories(session)
    current = next((c for c in categories if c.id == category_id), None)
    if current is None:
        return []
    return [c.id for c in categories if c.parent_id == current.parent_id and c.id is not None]


def _parent_options(session: Session, exclude_id: int | None = None) -> dict[int, str]:
    """Wählbare Gruppen: Top-Level-Kategorien außer der bearbeiteten; 0 = keine Gruppe (#395)."""
    options: dict[int, str] = {0: "Keine Gruppe"}
    for category in category_service.get_all_categories(session):
        if category.id is not None and category.parent_id is None and category.id != exclude_id:
            options[category.id] = category.name
    return options


@with_permission_check(Permission.CONFIG_MANAGE)  # Laufzeit-Check, nicht nur beim Seitenaufbau (#381)
def _move_category_up(category_id: int) -> None:
    """Move a category up in the sort order (within its siblings)."""
    with next(get_session()) as session:
        category_ids = _sibling_ids(session, category_id)

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


@with_permission_check(Permission.CONFIG_MANAGE)
def _move_category_down(category_id: int) -> None:
    """Move a category down in the sort order (within its siblings)."""
    with next(get_session()) as session:
        category_ids = _sibling_ids(session, category_id)

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
    """Render the list of categories: top-level in order, children indented under their group (#395)."""
    with next(get_session()) as session:
        categories = category_service.get_all_categories(session)

        if not categories:
            # Empty state (Solarpunk theme)
            with ui.card().classes("sp-dashboard-card w-full"):
                with ui.column().classes("w-full items-center py-8"):
                    ui.icon("category", size="48px").classes("text-stone mb-2")
                    ui.label("Keine Kategorien vorhanden").classes("text-charcoal text-center")
                    ui.label("Kategorien helfen beim Organisieren des Vorrats.").classes(
                        "text-sm text-stone text-center"
                    )
            return

        children_by_parent: dict[int, list[Category]] = defaultdict(list)
        for category in categories:
            if category.parent_id is not None:
                children_by_parent[category.parent_id].append(category)
        top_level = [c for c in categories if c.parent_id is None]

        for index, category in enumerate(top_level):
            children = children_by_parent.get(category.id, []) if category.id is not None else []
            _render_category_row(
                session,
                category,
                is_first=index == 0,
                is_last=index == len(top_level) - 1,
                child_count=len(children),
            )
            for child_index, child in enumerate(children):
                _render_category_row(
                    session,
                    child,
                    is_first=child_index == 0,
                    is_last=child_index == len(children) - 1,
                    parent_name=category.name,
                )


def _render_category_row(
    session: Session,
    category: Category,
    *,
    is_first: bool,
    is_last: bool,
    child_count: int = 0,
    parent_name: str | None = None,
) -> None:
    """Eine Zeile der Admin-Liste; Kinder eingerückt und markiert, Gruppen mit Badge (#395)."""
    cat_id = category.id
    if cat_id is None:
        return
    shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(session, cat_id)
    shelf_life_dict = {sl.storage_type: sl for sl in shelf_lives}

    row = ui.element("div").classes("sp-admin-list-item w-full")
    if parent_name is not None:
        row.classes("ml-8").mark(f"child-of-{parent_name}-{category.name}")

    # Admin list item (Solarpunk theme)
    with row:
        # Left side: reorder buttons + color + name
        with ui.row().classes("items-center gap-3 flex-1"):
            # Reorder buttons (drag handle style); Hoch/Runter bewegt innerhalb der Geschwister
            with ui.column().classes("gap-0 sp-admin-drag"):
                ui.button(
                    icon="keyboard_arrow_up",
                    on_click=lambda cid=cat_id: _move_category_up(cid),
                ).props(f"flat round dense size=xs {'disabled' if is_first else ''}").classes("h-5").mark(
                    f"move-up-{category.name}"
                )
                ui.button(
                    icon="keyboard_arrow_down",
                    on_click=lambda cid=cat_id: _move_category_down(cid),
                ).props(f"flat round dense size=xs {'disabled' if is_last else ''}").classes("h-5").mark(
                    f"move-down-{category.name}"
                )

            # Color indicator (Solarpunk admin color dot)
            if category.color:
                ui.element("div").classes("sp-admin-color-dot").style(f"background-color: {category.color}")
            else:
                ui.element("div").classes("sp-admin-color-dot bg-oat")
            # Category name
            ui.label(category.name).classes("font-medium text-lg text-charcoal")
            if child_count:
                ui.label("Gruppe").classes(
                    "text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-oat text-charcoal"
                ).mark(f"group-badge-{category.name}")

        # Right side: shelf life info and buttons
        with ui.row().classes("items-center gap-2"):
            # Shelf life info (compact display)
            _render_shelf_life_badges(shelf_life_dict)

            # Capture category data for the closures
            cat_name = category.name
            cat_color = category.color
            cat_parent_id = category.parent_id

            # Action buttons (Solarpunk theme)
            with ui.row().classes("sp-admin-actions items-center gap-1"):
                # Edit button
                with (
                    ui.button(
                        on_click=lambda cid=cat_id,
                        cn=cat_name,
                        cc=cat_color,
                        cp=cat_parent_id,
                        cc_count=child_count: _open_edit_dialog(cid, cn, cc, cp, cc_count),
                    )
                    .props("flat round size=sm")
                    .classes("edit")
                    .mark(f"edit-{cat_name}")
                ):
                    create_icon("actions/edit", size="20px")

                # Delete button
                with (
                    ui.button(
                        on_click=lambda cid=cat_id, cn=cat_name: _open_delete_dialog(cid, cn),
                    )
                    .props("flat round size=sm")
                    .classes("delete")
                    .mark(f"delete-{cat_name}")
                ):
                    create_icon("actions/delete", size="20px")


def _render_shelf_life_badges(shelf_life_dict: dict) -> None:
    """Render compact shelf life badges (Solarpunk theme)."""
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
                ui.icon(icon, size="16px").classes("text-stone")
                ui.label(f"{sl.months_min}-{sl.months_max}").classes("text-xs text-stone")


def _open_create_dialog() -> None:
    """Open dialog to create a new category."""
    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-lg"):
        ui.label("Neue Kategorie erstellen").classes("text-h6 font-semibold mb-4 text-fern")

        # Name input (required)
        name_input = ui.input(label="Name", placeholder="z.B. Gemüse").classes("w-full mb-2").props("outlined")

        # Color input with preview
        with ui.row().classes("w-full items-center gap-2 mb-4"):
            color_input = ui.color_input(label="Farbe").classes("flex-1").mark("color-input")
            color_preview = (
                ui.element("div")
                .classes("w-10 h-10 rounded-lg border-2 border-gray-300")
                .style("background-color: #E5E7EB")
                .mark("color-preview")
            )
            color_input.on_value_change(
                lambda e: color_preview.style(
                    f"background-color: {e.value}" if e.value else "background-color: #E5E7EB"
                )
            )

        # Gruppe (Eltern-Kategorie, eine Ebene; #395)
        with next(get_session()) as session:
            parent_options = _parent_options(session)
        parent_select = (
            ui.select(parent_options, label="Gruppe", value=0)
            .classes("w-full mb-4")
            .props("outlined")
            .mark("create-parent")
        )

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

        # Buttons (Solarpunk theme)
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(Permission.CONFIG_MANAGE)
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
                            parent_id=parent_select.value or None,
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
                except Exception as e:
                    # Duplikate meldet der Service typisiert, Unerwartetes landet im Log (#382)
                    show_service_error(e, error_label)

            ui.button("Speichern", on_click=save_category).classes("sp-btn-primary")

    dialog.open()


def _open_edit_dialog(
    category_id: int,
    current_name: str,
    current_color: str | None,
    current_parent_id: int | None = None,
    child_count: int = 0,
) -> None:
    """Open dialog to edit an existing category with group and shelf life configuration."""
    # Load existing shelf lives
    with next(get_session()) as session:
        shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(session, category_id)
        existing_shelf_lives = {sl.storage_type: sl for sl in shelf_lives}
        parent_options = _parent_options(session, exclude_id=category_id)

    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-lg"):
        ui.label("Kategorie bearbeiten").classes("text-h6 font-semibold mb-4 text-fern")

        # Name input (pre-filled)
        name_input = (
            ui.input(label="Name", value=current_name).classes("w-full mb-2").props("outlined").mark("edit-name")
        )

        # Color input with preview (pre-filled)
        initial_color = current_color or ""
        with ui.row().classes("w-full items-center gap-2 mb-4"):
            color_input = ui.color_input(label="Farbe", value=initial_color).classes("flex-1").mark("color-input")
            color_preview = (
                ui.element("div")
                .classes("w-10 h-10 rounded-lg border-2 border-gray-300")
                .style(f"background-color: {initial_color}" if initial_color else "background-color: #E5E7EB")
                .mark("color-preview")
            )
            color_input.on_value_change(
                lambda e: color_preview.style(
                    f"background-color: {e.value}" if e.value else "background-color: #E5E7EB"
                )
            )

        # Gruppe (Eltern-Kategorie, eine Ebene; #395). Eine Gruppe kann selbst kein Kind werden.
        parent_select: ui.select | None = None
        if child_count:
            ui.label(f"Gruppe mit {child_count} Unterkategorien; kann selbst keiner Gruppe zugeordnet werden.").classes(
                "text-xs text-stone mb-4"
            )
        else:
            parent_select = (
                ui.select(parent_options, label="Gruppe", value=current_parent_id or 0)
                .classes("w-full mb-4")
                .props("outlined")
                .mark("edit-parent")
            )

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

        # Buttons (Solarpunk theme)
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(Permission.CONFIG_MANAGE)
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

                new_parent_id: int | None | Unset = UNSET
                if parent_select is not None:
                    new_parent_id = parent_select.value or None

                try:
                    with next(get_session()) as session:
                        # Update category
                        category_service.update_category(
                            session=session,
                            id=category_id,
                            name=name if name != current_name else None,
                            color=color,
                            parent_id=new_parent_id,
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
                except Exception as e:
                    # Duplikate meldet der Service typisiert, Unerwartetes landet im Log (#382)
                    show_service_error(e, error_label)

            ui.button("Speichern", on_click=save_changes).classes("sp-btn-primary")

    dialog.open()


def _open_delete_dialog(category_id: int, category_name: str) -> None:
    """Open confirmation dialog to delete a category."""
    with ui.dialog() as dialog, ui.card().classes("sp-dashboard-card w-full max-w-md"):
        ui.label("Kategorie löschen").classes("text-h6 font-semibold mb-4 text-fern")

        # Warning message
        ui.label(f"Möchten Sie die Kategorie '{category_name}' wirklich löschen?").classes("mb-2")
        ui.label("Diese Aktion kann nicht rückgängig gemacht werden.").classes("text-sm text-red-600 mb-4")

        # Error label (hidden by default)
        error_label = ui.label("").classes("text-red-600 text-sm mb-2")
        error_label.set_visibility(False)

        # Buttons (Solarpunk theme)
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).classes("sp-btn-ghost").props("flat")

            @with_permission_check(Permission.CONFIG_MANAGE)
            def confirm_delete() -> None:
                """Perform the deletion."""
                try:
                    with next(get_session()) as session:
                        # Der Service prüft Referenzen und löscht die Haltbarkeiten
                        # in derselben Transaktion (#379)
                        category_service.delete_category(session=session, id=category_id)
                    ui.notify("Kategorie gelöscht", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/categories")
                except Exception as e:
                    show_service_error(e, error_label)

            ui.button("Löschen", on_click=confirm_delete).classes("sp-btn-danger")

    dialog.open()
