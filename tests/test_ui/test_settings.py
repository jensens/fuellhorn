"""UI Tests for Settings Page - Gefrierzeit-Konfiguration."""

from app.models.category import Category
from app.models.freeze_time_config import FreezeTimeConfig
from app.models.freeze_time_config import ItemType
from nicegui.testing import User
from sqlmodel import Session


async def test_settings_page_renders_for_admin(logged_in_user: User) -> None:
    """Test that settings page renders correctly for admin users."""
    # Navigate to settings (already logged in via fixture)
    await logged_in_user.open("/admin/settings")

    # Check page elements
    await logged_in_user.should_see("Einstellungen")
    await logged_in_user.should_see("Gefrierzeit-Konfiguration")


async def test_settings_page_shows_freeze_time_configs(
    logged_in_user: User, isolated_test_database
) -> None:
    """Test that settings page shows freeze time configurations."""
    # Create test freeze time config
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,  # admin user from fixture
        )
        session.add(config)
        session.commit()

    # Navigate to settings (already logged in via fixture)
    await logged_in_user.open("/admin/settings")

    # Should see the config
    await logged_in_user.should_see("12 Monate")


async def test_settings_page_groups_by_item_type(
    logged_in_user: User, isolated_test_database
) -> None:
    """Test that freeze time configs are grouped by item type."""
    # Create test freeze time configs for different item types
    with Session(isolated_test_database) as session:
        # Global config for homemade frozen
        config1 = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        # Global config for purchased then frozen
        config2 = FreezeTimeConfig(
            item_type=ItemType.PURCHASED_THEN_FROZEN,
            freeze_time_months=6,
            created_by=1,
        )
        session.add(config1)
        session.add(config2)
        session.commit()

    # Navigate to settings (already logged in via fixture)
    await logged_in_user.open("/admin/settings")

    # Should see item type headers (German labels)
    await logged_in_user.should_see("Selbst eingefroren")  # HOMEMADE_FROZEN
    await logged_in_user.should_see("Frisch gekauft, eingefroren")  # PURCHASED_THEN_FROZEN


async def test_settings_page_shows_category_specific_configs(
    logged_in_user: User, isolated_test_database
) -> None:
    """Test that category-specific configs are displayed with category name."""
    # Create test category and config
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

    # Navigate to settings (already logged in via fixture)
    await logged_in_user.open("/admin/settings")

    # Should see category name
    await logged_in_user.should_see("Fleisch")
    await logged_in_user.should_see("6 Monate")


async def test_settings_page_requires_auth(user: User) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access settings without login
    await user.open("/admin/settings")
    # Should redirect to login
    await user.should_see("Anmelden")


async def test_settings_page_shows_empty_state(logged_in_user: User) -> None:
    """Test that settings page shows message when no configs exist."""
    # Navigate to settings (already logged in, no configs created)
    await logged_in_user.open("/admin/settings")

    # Should see empty state message
    await logged_in_user.should_see("Keine Gefrierzeit-Konfigurationen vorhanden")


# =============================================================================
# CRUD Tests (Issue #33)
# =============================================================================


async def test_settings_page_has_add_button(logged_in_user: User) -> None:
    """Test that settings page has a 'Neu' button for creating new configs."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Neu")


async def test_add_button_opens_create_dialog(logged_in_user: User) -> None:
    """Test that clicking 'Neu' button opens a create dialog."""
    await logged_in_user.open("/admin/settings")
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
    await logged_in_user.open("/admin/settings")
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
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("delete")


async def test_delete_button_opens_confirmation_dialog(
    logged_in_user: User, isolated_test_database
) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()
    await logged_in_user.open("/admin/settings")
    logged_in_user.find("delete").click()
    await logged_in_user.should_see("Löschen bestätigen")
