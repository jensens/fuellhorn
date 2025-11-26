"""UI Tests for Settings Page - Admin Navigation and System Defaults.

Issue #79: Settings Page aufteilen - Navigation zu Admin-Bereichen.
Issue #34: Smart Default Zeitfenster konfigurieren.
Issue #85: System-Defaults in DB speichern (Fallback für User ohne eigene Einstellungen).
"""

from nicegui.testing import User


async def test_settings_page_renders_for_admin(logged_in_user: User) -> None:
    """Test that settings page renders correctly for admin users."""
    await logged_in_user.open("/admin/settings")

    # Check page elements
    await logged_in_user.should_see("Einstellungen")


async def test_settings_page_requires_auth(user: User) -> None:
    """Test that unauthenticated users are redirected to login."""
    await user.open("/admin/settings")
    await user.should_see("Anmelden")


# =============================================================================
# Admin Navigation Tests (Issue #79)
# =============================================================================


async def test_settings_page_shows_admin_navigation(logged_in_user: User) -> None:
    """Test that settings page shows admin navigation section."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Verwaltung")


async def test_settings_page_shows_categories_link(logged_in_user: User) -> None:
    """Test that settings page has link to categories."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Kategorien")


async def test_settings_page_shows_locations_link(logged_in_user: User) -> None:
    """Test that settings page has link to locations."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Lagerorte")


async def test_settings_page_shows_users_link(logged_in_user: User) -> None:
    """Test that settings page has link to users."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Benutzer")


async def test_settings_page_shows_freeze_times_link(logged_in_user: User) -> None:
    """Test that settings page has link to freeze times."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Gefrierzeiten")


# =============================================================================
# System Default Zeitfenster Tests (Issue #34, #85)
# =============================================================================


async def test_settings_page_shows_smart_defaults_section(logged_in_user: User) -> None:
    """Test that settings page has a System Defaults section (renamed in #85)."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("System-Standardwerte")


async def test_settings_page_shows_item_type_time_window(logged_in_user: User) -> None:
    """Test that settings page shows item type time window input."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Artikel-Typ Zeitfenster")


async def test_settings_page_shows_category_time_window(logged_in_user: User) -> None:
    """Test that settings page shows category time window input."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Kategorie Zeitfenster")


async def test_settings_page_shows_location_time_window(logged_in_user: User) -> None:
    """Test that settings page shows location time window input."""
    await logged_in_user.open("/admin/settings")
    await logged_in_user.should_see("Lagerort Zeitfenster")
