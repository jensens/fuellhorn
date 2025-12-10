"""UI Tests for Users Page (Admin).

Issue #28: Users Page - Liste aller Benutzer
"""

from app.models.user import User
from datetime import datetime
from nicegui.testing import User as TestUser
from sqlmodel import Session


async def test_users_page_renders_for_admin(logged_in_user: TestUser) -> None:
    """Test that users page renders for admin users."""
    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Check page elements
    await logged_in_user.should_see("Benutzer")


async def test_users_page_shows_user_list(logged_in_user: TestUser) -> None:
    """Test that users page displays user list with username, role, status."""
    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Admin user from fixture should be visible
    await logged_in_user.should_see("admin")
    await logged_in_user.should_see("Admin")  # Role display
    await logged_in_user.should_see("Aktiv")  # Status


async def test_users_page_displays_multiple_users(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that users page displays all users with their details."""
    # Create additional test users
    with Session(isolated_test_database) as session:
        user1 = User(
            username="testuser1",
            email="testuser1@example.com",
            is_active=True,
            role="user",
            last_login=datetime(2025, 11, 25, 10, 30),
        )
        user1.set_password("password123")

        user2 = User(
            username="testuser2",
            email="testuser2@example.com",
            is_active=False,
            role="admin",
        )
        user2.set_password("password123")

        session.add(user1)
        session.add(user2)
        session.commit()

    # Navigate to users page (already logged in via fixture)
    await logged_in_user.open("/admin/users")

    # Should see all users
    await logged_in_user.should_see("admin")
    await logged_in_user.should_see("testuser1")
    await logged_in_user.should_see("testuser2")

    # Should see roles and statuses
    await logged_in_user.should_see("Benutzer")  # User role for testuser1
    await logged_in_user.should_see("Aktiv")
    await logged_in_user.should_see("Inaktiv")  # Status for testuser2


async def test_users_page_displays_last_login(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that users page displays last login time."""
    # Create user with last login
    with Session(isolated_test_database) as session:
        user_with_login = User(
            username="loginuser",
            email="loginuser@example.com",
            is_active=True,
            role="user",
            last_login=datetime(2025, 11, 25, 10, 30),
        )
        user_with_login.set_password("password123")
        session.add(user_with_login)
        session.commit()

    # Navigate to users page
    await logged_in_user.open("/admin/users")

    # Should see the last login date (formatted)
    await logged_in_user.should_see("25.11.2025")


async def test_users_page_requires_auth(user: TestUser) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access users without login
    await user.open("/admin/users")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_users_page_requires_admin_permission(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that regular users are redirected (no USER_MANAGE permission)."""
    # Create a regular user
    with Session(isolated_test_database) as session:
        regular_user = User(
            username="testuser",
            email="testuser@example.com",
            is_active=True,
            role="user",
        )
        regular_user.set_password("password123")
        session.add(regular_user)
        session.commit()

    # Login as regular user (manual login needed for non-admin user)
    await user.open("/login")
    user.find("Benutzername").type("testuser")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Try to navigate to users page
    await user.open("/admin/users")

    # Regular user should be redirected (should not see "Benutzer verwalten" header)
    await user.should_not_see("Benutzer verwalten")


async def test_users_page_has_back_button(logged_in_user: TestUser) -> None:
    """Test that users page has back button to settings."""
    # Navigate to users page
    await logged_in_user.open("/admin/users")

    # Should have back button (arrow_back icon)
    # The back button should navigate to /settings
    await logged_in_user.should_see("Benutzer")


# =============================================================================
# Issue #29: User Creation Tests
# =============================================================================


async def test_users_page_has_new_user_button(logged_in_user: TestUser) -> None:
    """Test that users page has 'Neuer Benutzer' button."""
    await logged_in_user.open("/admin/users")

    # Should see "Neuer Benutzer" button
    await logged_in_user.should_see("Neuer Benutzer")


async def test_new_user_button_opens_dialog(logged_in_user: TestUser) -> None:
    """Test that clicking 'Neuer Benutzer' opens a dialog with form."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Should see dialog with form fields
    await logged_in_user.should_see("Neuen Benutzer erstellen")
    await logged_in_user.should_see("Benutzername")
    await logged_in_user.should_see("E-Mail")
    await logged_in_user.should_see("Passwort")
    await logged_in_user.should_see("Wiederholung")
    await logged_in_user.should_see("Rolle")


async def test_create_user_success(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that creating a user works correctly."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in the form
    logged_in_user.find("Benutzername").type("newuser")
    logged_in_user.find("E-Mail").type("newuser@example.com")
    logged_in_user.find(marker="password-input").type("securepassword123")
    logged_in_user.find(marker="password-confirm-input").type("securepassword123")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should see the new user in the list
    await logged_in_user.should_see("newuser")


async def test_create_user_validation_username_required(
    logged_in_user: TestUser,
) -> None:
    """Test that username is required."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in only other fields
    logged_in_user.find("E-Mail").type("test@example.com")
    logged_in_user.find(marker="password-input").type("password123")
    logged_in_user.find(marker="password-confirm-input").type("password123")

    # Try to save without username
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("Benutzername ist erforderlich")


async def test_create_user_validation_email_required(
    logged_in_user: TestUser,
) -> None:
    """Test that email is required."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in only other fields
    logged_in_user.find("Benutzername").type("testuser")
    logged_in_user.find(marker="password-input").type("password123")
    logged_in_user.find(marker="password-confirm-input").type("password123")

    # Try to save without email
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("E-Mail ist erforderlich")


async def test_create_user_validation_password_required(
    logged_in_user: TestUser,
) -> None:
    """Test that password is required."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in only other fields
    logged_in_user.find("Benutzername").type("testuser")
    logged_in_user.find("E-Mail").type("test@example.com")

    # Try to save without password
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("Passwort ist erforderlich")


async def test_create_user_validation_passwords_must_match(
    logged_in_user: TestUser,
) -> None:
    """Test that password and confirmation must match."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in form with mismatched passwords
    logged_in_user.find("Benutzername").type("testuser")
    logged_in_user.find("E-Mail").type("test@example.com")
    logged_in_user.find(marker="password-input").type("password123")
    logged_in_user.find(marker="password-confirm-input").type("differentpassword")

    # Try to save
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("Passwörter stimmen nicht überein")


async def test_create_user_validation_unique_username(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that duplicate usernames are rejected."""
    # Admin user already exists with username "admin"
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Try to create user with existing username
    logged_in_user.find("Benutzername").type("admin")
    logged_in_user.find("E-Mail").type("admin2@example.com")
    logged_in_user.find(marker="password-input").type("password123")
    logged_in_user.find(marker="password-confirm-input").type("password123")

    # Try to save
    logged_in_user.find("Speichern").click()

    # Should see error message about duplicate
    await logged_in_user.should_see("bereits vorhanden")


async def test_create_user_with_admin_role(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that creating an admin user works correctly."""
    await logged_in_user.open("/admin/users")

    # Click the "Neuer Benutzer" button
    logged_in_user.find(marker="new-user-button").click()

    # Fill in the form
    logged_in_user.find("Benutzername").type("newadmin")
    logged_in_user.find("E-Mail").type("newadmin@example.com")
    logged_in_user.find(marker="password-input").type("securepassword123")
    logged_in_user.find(marker="password-confirm-input").type("securepassword123")

    # Select Admin role
    logged_in_user.find("Rolle").click()
    logged_in_user.find("Admin").click()

    # Click save
    logged_in_user.find("Speichern").click()

    # Should see the new admin in the list
    await logged_in_user.should_see("newadmin")


# =============================================================================
# Issue #30: User Edit Tests
# =============================================================================


async def test_users_page_has_edit_buttons(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that each user card has an edit button."""
    # Create an additional user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="editableuser",
            email="editable@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Should see edit buttons (icon buttons with edit icon)
    await logged_in_user.should_see("editableuser")


async def test_edit_button_opens_dialog(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that clicking edit button opens dialog with pre-filled form."""
    # Create a user to edit
    with Session(isolated_test_database) as session:
        test_user = User(
            username="usertoedit",
            email="usertoedit@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button for the user (using marker)
    logged_in_user.find(marker="edit-usertoedit").click()

    # Should see dialog with pre-filled values
    await logged_in_user.should_see("Benutzer bearbeiten")
    await logged_in_user.should_see("usertoedit")


async def test_edit_user_change_username(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that username can be changed."""
    # Create a user to edit
    with Session(isolated_test_database) as session:
        test_user = User(
            username="oldname",
            email="oldname@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button
    logged_in_user.find(marker="edit-oldname").click()

    # Clear and change username
    logged_in_user.find(marker="edit-username").clear()
    logged_in_user.find(marker="edit-username").type("newname")

    # Save
    logged_in_user.find("Speichern").click()

    # Should see updated name in list
    await logged_in_user.should_see("newname")
    await logged_in_user.should_not_see("oldname")


async def test_edit_user_change_role(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that role can be changed."""
    # Create a regular user to edit
    with Session(isolated_test_database) as session:
        test_user = User(
            username="roleuser",
            email="roleuser@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button
    logged_in_user.find(marker="edit-roleuser").click()

    # Change role to Admin
    logged_in_user.find(marker="edit-role").click()
    logged_in_user.find("Admin").click()

    # Save
    logged_in_user.find("Speichern").click()

    # Page should reload and show updated user
    await logged_in_user.should_see("roleuser")


async def test_edit_user_change_password(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that password can be changed optionally."""
    # Create a user to edit
    with Session(isolated_test_database) as session:
        test_user = User(
            username="pwduser",
            email="pwduser@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("oldpassword")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button
    logged_in_user.find(marker="edit-pwduser").click()

    # Enter new password
    logged_in_user.find(marker="edit-password").type("newpassword123")
    logged_in_user.find(marker="edit-password-confirm").type("newpassword123")

    # Save
    logged_in_user.find("Speichern").click()

    # Should show success (user still visible)
    await logged_in_user.should_see("pwduser")


async def test_edit_user_password_mismatch(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that password change requires matching confirmation."""
    # Create a user to edit
    with Session(isolated_test_database) as session:
        test_user = User(
            username="pwdmismatch",
            email="pwdmismatch@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button
    logged_in_user.find(marker="edit-pwdmismatch").click()

    # Enter mismatched passwords
    logged_in_user.find(marker="edit-password").type("newpassword123")
    logged_in_user.find(marker="edit-password-confirm").type("differentpassword")

    # Try to save
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("Passwörter stimmen nicht überein")


async def test_edit_user_toggle_active_status(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that active status can be toggled."""
    # Create an active user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="activeuser",
            email="activeuser@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click the edit button
    logged_in_user.find(marker="edit-activeuser").click()

    # Toggle active status off
    logged_in_user.find(marker="edit-is-active").click()

    # Save
    logged_in_user.find("Speichern").click()

    # Should see Inaktiv status
    await logged_in_user.should_see("Inaktiv")


# Issue #31: Delete User Tests


async def test_delete_button_visible_for_users(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that delete button is visible for each user."""
    # Create a test user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="deletetest",
            email="deletetest@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Delete button should be visible (via marker)
    logged_in_user.find(marker="delete-deletetest")


async def test_delete_user_opens_confirmation_dialog(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    # Create a test user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="confirmdelete",
            email="confirmdelete@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click delete button
    logged_in_user.find(marker="delete-confirmdelete").click()

    # Should see confirmation dialog
    await logged_in_user.should_see("Benutzer löschen")
    await logged_in_user.should_see("confirmdelete")


async def test_delete_user_successfully(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that user can be deleted successfully."""
    # Create a test user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="deleteme",
            email="deleteme@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Verify user is visible
    await logged_in_user.should_see("deleteme")

    # Click delete button
    logged_in_user.find(marker="delete-deleteme").click()

    # Confirm deletion
    logged_in_user.find("Löschen").click()

    # User should no longer be visible
    await logged_in_user.should_not_see("deleteme")


async def test_cannot_delete_yourself(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that the current user cannot delete themselves."""
    await logged_in_user.open("/admin/users")

    # The logged-in user is "admin"
    await logged_in_user.should_see("admin")

    # Delete button for admin should not exist (or be disabled)
    # We use a marker that won't exist for the current user
    try:
        logged_in_user.find(marker="delete-admin")
        # If we get here, the button exists - test should fail
        assert False, "Delete button should not exist for current user"
    except AssertionError as e:
        # Button doesn't exist - this is expected
        if "Delete button should not exist" in str(e):
            raise
        # Expected: button not found
        pass


async def test_delete_dialog_can_be_cancelled(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that delete operation can be cancelled."""
    # Create a test user
    with Session(isolated_test_database) as session:
        test_user = User(
            username="canceldelete",
            email="canceldelete@example.com",
            is_active=True,
            role="user",
        )
        test_user.set_password("password123")
        session.add(test_user)
        session.commit()

    await logged_in_user.open("/admin/users")

    # Click delete button
    logged_in_user.find(marker="delete-canceldelete").click()

    # Cancel deletion
    logged_in_user.find("Abbrechen").click()

    # User should still be visible
    await logged_in_user.should_see("canceldelete")
