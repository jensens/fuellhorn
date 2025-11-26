"""Freeze Times Page - Gefrierzeit-Konfiguration (Admin).

Based on Issue #79: Settings Page aufteilen.
Extracted from settings.py - freeze time configuration management.
"""

from ...auth import Permission
from ...auth import require_permissions
from ...auth.dependencies import get_current_user
from ...database import get_session
from ...models.category import Category
from ...models.freeze_time_config import FreezeTimeConfig
from ...models.freeze_time_config import ItemType
from ...services import category_service
from ...services import freeze_time_service
from ..components import create_mobile_page_container
from nicegui import ui
from sqlmodel import Session
from sqlmodel import select


# German labels for ItemType
ITEM_TYPE_LABELS: dict[ItemType, str] = {
    ItemType.PURCHASED_FRESH: "Frisch gekauft",
    ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
    ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft, eingefroren",
    ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
    ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
}

# Reverse mapping for select options
ITEM_TYPE_OPTIONS: dict[str, ItemType] = {v: k for k, v in ITEM_TYPE_LABELS.items()}


@ui.page("/admin/freeze-times")
@require_permissions(Permission.CONFIG_MANAGE)
def freeze_times_page() -> None:
    """Freeze time configuration page (Admin only)."""
    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin/settings")).props(
                "flat round color=gray-7"
            )
            ui.label("Gefrierzeiten").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Section header with "Neu" button
        with ui.row().classes("w-full items-center justify-between mb-3"):
            ui.label("Gefrierzeit-Konfiguration").classes("text-h6 font-semibold")
            ui.button("Neu", icon="add", on_click=lambda: _open_create_dialog()).props("color=primary size=sm")

        _render_config_list()


def _render_config_list() -> None:
    """Render the list of freeze time configurations."""
    with next(get_session()) as session:
        configs = freeze_time_service.get_all_freeze_time_configs(session)

        if not configs:
            # Empty state
            with ui.card().classes("w-full p-4 bg-gray-50"):
                ui.label("Keine Gefrierzeit-Konfigurationen vorhanden").classes("text-gray-600")
        else:
            # Group configs by ItemType
            configs_by_type: dict[ItemType, list[FreezeTimeConfig]] = {}
            for config in configs:
                if config.item_type not in configs_by_type:
                    configs_by_type[config.item_type] = []
                configs_by_type[config.item_type].append(config)

            # Display grouped configs
            for item_type in ItemType:
                if item_type not in configs_by_type:
                    continue

                type_configs = configs_by_type[item_type]
                type_label = ITEM_TYPE_LABELS.get(item_type, item_type.value)

                # ItemType header
                ui.label(type_label).classes("text-subtitle1 font-medium mt-4 mb-2")

                # Config cards for this type
                for config in type_configs:
                    _render_config_card(session, config)


def _render_config_card(session: Session, config: FreezeTimeConfig) -> None:
    """Render a single freeze time config as a card with edit/delete buttons."""
    # Get category name if category-specific
    category_name = None
    if config.category_id:
        category = session.exec(select(Category).where(Category.id == config.category_id)).first()
        if category:
            category_name = category.name

    # Store config_id for closure
    config_id = config.id

    with ui.card().classes("w-full mb-2"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("flex-1"):
                if category_name:
                    ui.label(category_name).classes("font-medium")
                    ui.label(f"{config.freeze_time_months} Monate").classes("text-sm text-gray-600")
                else:
                    ui.label("Standard (Global)").classes("font-medium text-gray-500")
                    ui.label(f"{config.freeze_time_months} Monate").classes("text-sm text-gray-600")

            # Edit and delete buttons
            with ui.row().classes("gap-1"):
                ui.button(
                    icon="edit",
                    on_click=lambda cid=config_id: _open_edit_dialog(cid),
                ).props("flat round color=primary size=sm")
                ui.button(
                    icon="delete",
                    on_click=lambda cid=config_id: _open_delete_dialog(cid),
                ).props("flat round color=negative size=sm")


def _open_create_dialog() -> None:
    """Open dialog to create a new freeze time configuration."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Neue Gefrierzeit-Konfiguration").classes("text-h6 font-semibold mb-4")

        # Item type select
        item_type_options = list(ITEM_TYPE_OPTIONS.keys())
        item_type_select = ui.select(
            label="Artikel-Typ",
            options=item_type_options,
            value=item_type_options[0],
        ).classes("w-full mb-2")

        # Category select (optional)
        with next(get_session()) as session:
            categories = category_service.get_all_categories(session)
            category_options = {c.name: c.id for c in categories}
            category_options_list = ["(Global)"] + list(category_options.keys())

        category_select = ui.select(
            label="Kategorie",
            options=category_options_list,
            value="(Global)",
        ).classes("w-full mb-2")

        # Months input (1-24)
        months_input = ui.number(
            label="Monate (1-24)",
            value=6,
            min=1,
            max=24,
        ).classes("w-full mb-4")

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def save_config() -> None:
                item_type = ITEM_TYPE_OPTIONS[item_type_select.value]
                category_id = (
                    category_options.get(category_select.value) if category_select.value != "(Global)" else None
                )
                months = int(months_input.value) if months_input.value else 6

                # Validate months range
                if months < 1 or months > 24:
                    ui.notify("Monate muss zwischen 1 und 24 liegen", type="negative")
                    return

                try:
                    current_user = get_current_user()
                    if current_user is None or current_user.id is None:
                        ui.notify("Nicht angemeldet", type="negative")
                        return
                    with next(get_session()) as session:
                        freeze_time_service.create_freeze_time_config(
                            session=session,
                            item_type=item_type,
                            freeze_time_months=months,
                            created_by=current_user.id,
                            category_id=category_id,
                        )
                    ui.notify("Konfiguration erstellt", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/freeze-times")
                except ValueError as e:
                    ui.notify(str(e), type="negative")

            ui.button("Speichern", on_click=save_config).props("color=primary")

    dialog.open()


def _open_edit_dialog(config_id: int) -> None:
    """Open dialog to edit an existing freeze time configuration."""
    with next(get_session()) as session:
        config = freeze_time_service.get_freeze_time_config(session, config_id)
        current_item_type_label = ITEM_TYPE_LABELS[config.item_type]
        current_months = config.freeze_time_months

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-md"):
        ui.label("Gefrierzeit bearbeiten").classes("text-h6 font-semibold mb-4")

        # Item type (read-only display)
        ui.label(f"Artikel-Typ: {current_item_type_label}").classes("text-gray-600 mb-2")

        # Months input (1-24)
        months_input = ui.number(
            label="Monate (1-24)",
            value=current_months,
            min=1,
            max=24,
        ).classes("w-full mb-4")

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def update_config() -> None:
                months = int(months_input.value) if months_input.value else 6

                # Validate months range
                if months < 1 or months > 24:
                    ui.notify("Monate muss zwischen 1 und 24 liegen", type="negative")
                    return

                try:
                    with next(get_session()) as session:
                        freeze_time_service.update_freeze_time_config(
                            session=session,
                            id=config_id,
                            freeze_time_months=months,
                        )
                    ui.notify("Konfiguration aktualisiert", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/freeze-times")
                except ValueError as e:
                    ui.notify(str(e), type="negative")

            ui.button("Speichern", on_click=update_config).props("color=primary")

    dialog.open()


def _open_delete_dialog(config_id: int) -> None:
    """Open confirmation dialog to delete a freeze time configuration."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-sm"):
        ui.label("Löschen bestätigen").classes("text-h6 font-semibold mb-4")
        ui.label("Möchten Sie diese Konfiguration wirklich löschen?").classes("mb-4")

        # Buttons
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")

            def delete_config() -> None:
                try:
                    with next(get_session()) as session:
                        freeze_time_service.delete_freeze_time_config(session=session, id=config_id)
                    ui.notify("Konfiguration gelöscht", type="positive")
                    dialog.close()
                    ui.navigate.to("/admin/freeze-times")
                except ValueError as e:
                    ui.notify(str(e), type="negative")

            ui.button("Löschen", on_click=delete_config).props("color=negative")

    dialog.open()
