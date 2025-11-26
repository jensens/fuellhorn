"""UI Tests for Freeze Times Page - Gefrierzeit-Konfiguration.

Issue #79: Settings Page aufteilen - Freeze Times extracted to separate page.
Based on Issue #32 and #33: Freeze time configuration management.
"""

from app.models.category import Category
from app.models.freeze_time_config import FreezeTimeConfig
from app.models.freeze_time_config import ItemType
from nicegui.testing import User
from sqlmodel import Session


async def test_freeze_times_page_renders_for_admin(logged_in_user: User) -> None:
    """Test that freeze times page renders correctly for admin users."""
    await logged_in_user.open("/admin/freeze-times")

    # Check page elements
    await logged_in_user.should_see("Gefrierzeiten")
    await logged_in_user.should_see("Gefrierzeit-Konfiguration")


async def test_freeze_times_page_requires_auth(user: User) -> None:
    """Test that unauthenticated users are redirected to login."""
    await user.open("/admin/freeze-times")
    await user.should_see("Anmelden")


async def test_freeze_times_page_shows_configs(logged_in_user: User, isolated_test_database) -> None:
    """Test that freeze times page shows freeze time configurations."""
    # Create test freeze time config
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")

    # Should see the config
    await logged_in_user.should_see("12 Monate")


async def test_freeze_times_page_groups_by_item_type(logged_in_user: User, isolated_test_database) -> None:
    """Test that freeze time configs are grouped by item type."""
    # Create test freeze time configs for different item types
    with Session(isolated_test_database) as session:
        config1 = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        config2 = FreezeTimeConfig(
            item_type=ItemType.PURCHASED_THEN_FROZEN,
            freeze_time_months=6,
            created_by=1,
        )
        session.add(config1)
        session.add(config2)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")

    # Should see item type headers (German labels)
    await logged_in_user.should_see("Selbst eingefroren")
    await logged_in_user.should_see("Frisch gekauft, eingefroren")


async def test_freeze_times_page_shows_category_specific_configs(logged_in_user: User, isolated_test_database) -> None:
    """Test that category-specific configs are displayed with category name."""
    with Session(isolated_test_database) as session:
        category = Category(
            name="Fleisch",
            created_by=1,
        )
        session.add(category)
        session.commit()
        session.refresh(category)

        config = FreezeTimeConfig(
            category_id=category.id,
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=6,
            created_by=1,
        )
        session.add(config)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")

    # Should see category name
    await logged_in_user.should_see("Fleisch")
    await logged_in_user.should_see("6 Monate")


async def test_freeze_times_page_shows_empty_state(logged_in_user: User) -> None:
    """Test that freeze times page shows message when no configs exist."""
    await logged_in_user.open("/admin/freeze-times")

    # Should see empty state message
    await logged_in_user.should_see("Keine Gefrierzeit-Konfigurationen vorhanden")


# =============================================================================
# CRUD Tests
# =============================================================================


async def test_freeze_times_page_has_add_button(logged_in_user: User) -> None:
    """Test that freeze times page has a 'Neu' button for creating new configs."""
    await logged_in_user.open("/admin/freeze-times")
    await logged_in_user.should_see("Neu")


async def test_add_button_opens_create_dialog(logged_in_user: User) -> None:
    """Test that clicking 'Neu' button opens a create dialog."""
    await logged_in_user.open("/admin/freeze-times")
    logged_in_user.find("Neu").click()
    await logged_in_user.should_see("Neue Gefrierzeit-Konfiguration")


async def test_config_card_has_edit_button(logged_in_user: User, isolated_test_database) -> None:
    """Test that config cards have edit buttons."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")
    await logged_in_user.should_see("edit")


async def test_config_card_has_delete_button(logged_in_user: User, isolated_test_database) -> None:
    """Test that config cards have delete buttons."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")
    await logged_in_user.should_see("delete")


async def test_delete_button_opens_confirmation_dialog(logged_in_user: User, isolated_test_database) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()

    await logged_in_user.open("/admin/freeze-times")
    logged_in_user.find("delete").click()
    await logged_in_user.should_see("Löschen bestätigen")
