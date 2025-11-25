"""Settings Page - Gefrierzeit-Konfiguration (Admin).

Based on Issue #32: Settings Page to display freeze time configurations.
"""

from ...auth import Permission
from ...auth import require_permissions
from ...database import get_session
from ...models.category import Category
from ...models.freeze_time_config import FreezeTimeConfig
from ...models.freeze_time_config import ItemType
from ...services import freeze_time_service
from ..components import create_bottom_nav
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


@ui.page("/admin/settings")
@require_permissions(Permission.CONFIG_MANAGE)
def settings() -> None:
    """Settings page for freeze time configuration (Admin only)."""

    # Header
    with ui.row().classes("w-full items-center justify-between p-4 bg-white border-b border-gray-200"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/dashboard")).props("flat round color=gray-7")
            ui.label("Einstellungen").classes("text-h5 font-bold text-primary")

    # Main content with bottom nav spacing
    with create_mobile_page_container():
        # Freeze time configuration section
        ui.label("Gefrierzeit-Konfiguration").classes("text-h6 font-semibold mb-3")

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

    # Bottom Navigation
    create_bottom_nav(current_page="settings")


def _render_config_card(session: Session, config: FreezeTimeConfig) -> None:
    """Render a single freeze time config as a card."""
    # Get category name if category-specific
    category_name = None
    if config.category_id:
        category = session.exec(select(Category).where(Category.id == config.category_id)).first()
        if category:
            category_name = category.name

    with ui.card().classes("w-full mb-2"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("flex-1"):
                if category_name:
                    ui.label(category_name).classes("font-medium")
                    ui.label(f"{config.freeze_time_months} Monate").classes("text-sm text-gray-600")
                else:
                    ui.label("Standard (Global)").classes("font-medium text-gray-500")
                    ui.label(f"{config.freeze_time_months} Monate").classes("text-sm text-gray-600")
