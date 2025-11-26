"""UI Tests for Categories Page (Admin).

Issue #20: Categories Liste
Issue #21: Kategorie erstellen
Issue #22: Kategorie bearbeiten
Issue #23: Kategorie löschen
"""

from app.models.category import Category
from app.models.user import User
from nicegui.testing import User as TestUser
from sqlmodel import Session


async def test_categories_page_renders_for_admin(logged_in_user: TestUser) -> None:
    """Test that categories page renders for admin users."""
    # Navigate to categories page (already logged in via fixture)
    await logged_in_user.open("/admin/categories")

    # Check page elements
    await logged_in_user.should_see("Kategorien")


async def test_categories_page_shows_empty_state(logged_in_user: TestUser) -> None:
    """Test that categories page shows empty state when no categories exist."""
    # Navigate to categories page (already logged in via fixture)
    await logged_in_user.open("/admin/categories")

    # Should show empty state message
    await logged_in_user.should_see("Keine Kategorien vorhanden")


async def test_categories_page_displays_categories(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that categories page displays categories with name and color."""
    # Create test categories
    with Session(isolated_test_database) as session:
        cat1 = Category(
            name="Gemüse",
            color="#00FF00",
            created_by=1,  # admin user from fixture
        )
        cat2 = Category(
            name="Fleisch",
            color="#FF0000",
            created_by=1,
        )
        session.add(cat1)
        session.add(cat2)
        session.commit()

    # Navigate to categories page (already logged in via fixture)
    await logged_in_user.open("/admin/categories")

    # Should see categories
    await logged_in_user.should_see("Gemüse")
    await logged_in_user.should_see("Fleisch")


async def test_categories_page_requires_auth(user: TestUser) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access categories without login
    await user.open("/admin/categories")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_categories_page_requires_admin_permission(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that regular users are redirected (no CONFIG_MANAGE permission)."""
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

    # Try to navigate to categories page
    await user.open("/admin/categories")

    # Regular user should be redirected to dashboard (should not see "Kategorien" header)
    # They should see the dashboard or a permission error
    await user.should_not_see("Kategorien verwalten")


# =============================================================================
# Issue #21: Category Creation Tests
# =============================================================================


async def test_categories_page_has_new_category_button(user: TestUser) -> None:
    """Test that categories page has 'Neue Kategorie' button."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Should see "Neue Kategorie" button
    await user.should_see("Neue Kategorie")


async def test_new_category_button_opens_dialog(user: TestUser) -> None:
    """Test that clicking 'Neue Kategorie' opens a dialog with form."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find("Neue Kategorie").click()

    # Should see dialog with form fields
    await user.should_see("Neue Kategorie erstellen")
    await user.should_see("Name")


async def test_create_category_success(user: TestUser, isolated_test_database) -> None:
    """Test that creating a category works correctly."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find("Neue Kategorie").click()

    # Fill in the form
    user.find("Name").type("Gemüse")

    # Click save
    user.find("Speichern").click()

    # Should see success notification and category in list
    await user.should_see("Gemüse")


async def test_create_category_validation_name_required(user: TestUser) -> None:
    """Test that category name is required."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find("Neue Kategorie").click()

    # Try to save without entering name
    user.find("Speichern").click()

    # Should see error message
    await user.should_see("Name ist erforderlich")


async def test_create_category_validation_unique_name(user: TestUser, isolated_test_database) -> None:
    """Test that duplicate category names are rejected."""
    # Create a category first
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Fleisch",
            created_by=1,  # admin user from fixture
        )
        session.add(cat)
        session.commit()

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find("Neue Kategorie").click()

    # Try to create category with duplicate name
    user.find("Name").type("Fleisch")
    user.find("Speichern").click()

    # Should see error message about duplicate
    await user.should_see("bereits vorhanden")


# =============================================================================
# Issue #22: Category Edit Tests
# =============================================================================


async def test_categories_page_has_edit_buttons(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that each category card has an edit button."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Gemüse",
            color="#00FF00",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Should see the category
    await logged_in_user.should_see("Gemüse")


async def test_edit_button_opens_dialog(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that clicking edit button opens dialog with pre-filled form."""
    # Create a category to edit
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Obst",
            color="#FF5733",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button for the category (using marker)
    logged_in_user.find(marker="edit-Obst").click()

    # Should see dialog with pre-filled values
    await logged_in_user.should_see("Kategorie bearbeiten")
    await logged_in_user.should_see("Obst")


async def test_edit_category_change_name(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that category name can be changed."""
    # Create a category to edit
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Altername",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Altername").click()

    # Clear and change name
    logged_in_user.find(marker="edit-name").clear()
    logged_in_user.find(marker="edit-name").type("Neuername")

    # Save
    logged_in_user.find("Speichern").click()

    # Should see updated name in list
    await logged_in_user.should_see("Neuername")
    await logged_in_user.should_not_see("Altername")


async def test_edit_category_validation_name_required(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that category name is required when editing."""
    # Create a category to edit
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Testkategorie",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Testkategorie").click()

    # Clear the name field
    logged_in_user.find(marker="edit-name").clear()

    # Try to save without name
    logged_in_user.find("Speichern").click()

    # Should see error message
    await logged_in_user.should_see("Name ist erforderlich")


async def test_edit_category_validation_unique_name(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that duplicate category names are rejected when editing."""
    # Create two categories
    with Session(isolated_test_database) as session:
        cat1 = Category(
            name="Fleisch",
            created_by=1,
        )
        cat2 = Category(
            name="Fisch",
            created_by=1,
        )
        session.add(cat1)
        session.add(cat2)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button for Fisch
    logged_in_user.find(marker="edit-Fisch").click()

    # Try to rename to existing name
    logged_in_user.find(marker="edit-name").clear()
    logged_in_user.find(marker="edit-name").type("Fleisch")

    # Save
    logged_in_user.find("Speichern").click()

    # Should see error message about duplicate
    await logged_in_user.should_see("bereits vorhanden")


async def test_edit_category_cancel_closes_dialog(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that cancel button closes the dialog without saving."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Milchprodukte",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Milchprodukte").click()

    # Should see dialog
    await logged_in_user.should_see("Kategorie bearbeiten")

    # Click cancel
    logged_in_user.find("Abbrechen").click()

    # Dialog should be closed, original name should still be there
    await logged_in_user.should_see("Milchprodukte")


# =============================================================================
# Issue #23: Category Delete Tests
# =============================================================================


async def test_categories_page_has_delete_buttons(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that each category card has a delete button."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="Löschbar",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Should see the category
    await logged_in_user.should_see("Löschbar")


async def test_delete_button_opens_confirmation_dialog(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="ZuLöschen",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-ZuLöschen").click()

    # Should see confirmation dialog
    await logged_in_user.should_see("Kategorie löschen")
    await logged_in_user.should_see("ZuLöschen")


async def test_delete_category_success(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that deleting a category works correctly."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="WirdGelöscht",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-WirdGelöscht").click()

    # Confirm deletion
    logged_in_user.find("Löschen").click()

    # Category should be gone
    await logged_in_user.should_not_see("WirdGelöscht")


async def test_delete_category_cancel(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that canceling delete keeps the category."""
    # Create a category
    with Session(isolated_test_database) as session:
        cat = Category(
            name="NichtLöschen",
            created_by=1,
        )
        session.add(cat)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-NichtLöschen").click()

    # Cancel deletion
    logged_in_user.find("Abbrechen").click()

    # Category should still be there
    await logged_in_user.should_see("NichtLöschen")
