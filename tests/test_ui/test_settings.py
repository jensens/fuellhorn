"""UI Tests for Settings Page - Gefrierzeit-Konfiguration."""

from app.models.category import Category
from app.models.freeze_time_config import FreezeTimeConfig
from app.models.freeze_time_config import ItemType
from nicegui.testing import User
from sqlmodel import Session


async def test_settings_page_renders_for_admin(user: User) -> None:
    """Test that settings page renders correctly for admin users."""
    # Login as admin (created by isolated_test_database fixture)
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to settings
    await user.open("/admin/settings")

    # Check page elements
    await user.should_see("Einstellungen")
    await user.should_see("Gefrierzeit-Konfiguration")


async def test_settings_page_shows_freeze_time_configs(user: User, isolated_test_database) -> None:
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

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to settings
    await user.open("/admin/settings")

    # Should see the config
    await user.should_see("12 Monate")


async def test_settings_page_groups_by_item_type(user: User, isolated_test_database) -> None:
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

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to settings
    await user.open("/admin/settings")

    # Should see item type headers (German labels)
    await user.should_see("Selbst eingefroren")  # HOMEMADE_FROZEN
    await user.should_see("Frisch gekauft, eingefroren")  # PURCHASED_THEN_FROZEN


async def test_settings_page_shows_category_specific_configs(user: User, isolated_test_database) -> None:
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

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to settings
    await user.open("/admin/settings")

    # Should see category name
    await user.should_see("Fleisch")
    await user.should_see("6 Monate")


async def test_settings_page_requires_auth(user: User) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access settings without login
    await user.open("/admin/settings")
    # Should redirect to login
    await user.should_see("Anmelden")


async def test_settings_page_shows_empty_state(user: User) -> None:
    """Test that settings page shows message when no configs exist."""
    # Login as admin (no configs created)
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to settings
    await user.open("/admin/settings")

    # Should see empty state message
    await user.should_see("Keine Gefrierzeit-Konfigurationen vorhanden")


# =============================================================================
# CRUD Tests (Issue #33)
# =============================================================================


async def test_settings_page_has_add_button(user: User) -> None:
    """Test that settings page has a 'Neu' button for creating new configs."""
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.open("/admin/settings")
    await user.should_see("Neu")


async def test_add_button_opens_create_dialog(user: User) -> None:
    """Test that clicking 'Neu' button opens a create dialog."""
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.open("/admin/settings")
    user.find("Neu").click()
    await user.should_see("Neue Gefrierzeit-Konfiguration")


async def test_config_card_has_edit_button(user: User, isolated_test_database) -> None:
    """Test that config cards have edit buttons."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.open("/admin/settings")
    await user.should_see("edit")


async def test_config_card_has_delete_button(user: User, isolated_test_database) -> None:
    """Test that config cards have delete buttons."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.open("/admin/settings")
    await user.should_see("delete")


async def test_delete_button_opens_confirmation_dialog(user: User, isolated_test_database) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    with Session(isolated_test_database) as session:
        config = FreezeTimeConfig(
            item_type=ItemType.HOMEMADE_FROZEN,
            freeze_time_months=12,
            created_by=1,
        )
        session.add(config)
        session.commit()
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()
    await user.open("/admin/settings")
    user.find("delete").click()
    await user.should_see("Löschen bestätigen")
