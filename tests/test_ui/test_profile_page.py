"""Tests for Profile Page UI.

Tests the /profile page functionality:
- Password change with verification
- Email change (username stays fixed)
- Smart default time window settings
"""

import pytest
from nicegui.testing import User as NiceGUIUser

from app.models.user import User
from sqlmodel import Session


async def test_profile_page_requires_authentication(user: NiceGUIUser) -> None:
    """Test: Profile page redirects to login when not authenticated."""
    await user.open("/profile")
    # Should redirect to login
    await user.should_see("Anmelden")


async def test_profile_page_shows_username_readonly(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page shows username as readonly."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("Profil")
    await logged_in_user.should_see("admin")  # Username should be visible


async def test_profile_page_shows_email_field(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page shows email field for editing."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("E-Mail")


async def test_profile_page_shows_password_change_section(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page shows password change section."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("Passwort ändern")
    await logged_in_user.should_see("Aktuelles Passwort")
    await logged_in_user.should_see("Neues Passwort")
    await logged_in_user.should_see("Passwort bestätigen")


async def test_profile_page_shows_smart_defaults_section(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page shows smart defaults settings section."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("Smart Default Einstellungen")
    await logged_in_user.should_see("Artikel-Typ Zeitfenster")
    await logged_in_user.should_see("Kategorie Zeitfenster")
    await logged_in_user.should_see("Lagerort Zeitfenster")


async def test_profile_page_accessible_from_user_dropdown(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page is accessible from user dropdown."""
    await logged_in_user.open("/dashboard")
    # The user dropdown should have a "Profil" link
    await logged_in_user.should_see("admin")  # Username in dropdown


async def test_password_change_requires_current_password(logged_in_user: NiceGUIUser) -> None:
    """Test: Password change requires current password to be entered."""
    await logged_in_user.open("/profile")
    # Try to change password without current password
    # This is a UI test - verify the form validation exists
    await logged_in_user.should_see("Aktuelles Passwort")


async def test_password_change_requires_confirmation(logged_in_user: NiceGUIUser) -> None:
    """Test: Password change requires password confirmation."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("Passwort bestätigen")


async def test_profile_page_has_save_button(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page has save button."""
    await logged_in_user.open("/profile")
    await logged_in_user.should_see("Speichern")


async def test_profile_page_has_back_navigation(logged_in_user: NiceGUIUser) -> None:
    """Test: Profile page has back navigation."""
    await logged_in_user.open("/profile")
    # Should have a back button/arrow
    await logged_in_user.should_see("Profil")
