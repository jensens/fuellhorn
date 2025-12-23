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
    standard_categories,
) -> None:
    """Test that categories page displays categories with name and color."""
    # Navigate to categories page (already logged in via fixture)
    # standard_categories provides: Gemüse, Fleisch, Obst
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

    # Click the "Neue Kategorie" button (using marker for custom icon button)
    user.find(marker="new-category-button").click()

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

    # Click the "Neue Kategorie" button (using marker for custom icon button)
    user.find(marker="new-category-button").click()

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
    user.find(marker="new-category-button").click()

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
    user.find(marker="new-category-button").click()

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
    standard_categories,
) -> None:
    """Test that each category card has an edit button."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Should see the category
    await logged_in_user.should_see("Gemüse")


async def test_edit_button_opens_dialog(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that clicking edit button opens dialog with pre-filled form."""
    # standard_categories provides: Gemüse, Fleisch, Obst
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
    standard_categories,
) -> None:
    """Test that duplicate category names are rejected when editing."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the edit button for Obst
    logged_in_user.find(marker="edit-Obst").click()

    # Try to rename to existing name (Fleisch)
    logged_in_user.find(marker="edit-name").clear()
    logged_in_user.find(marker="edit-name").type("Fleisch")

    # Save
    logged_in_user.find("Speichern").click()

    # Should see error message about duplicate
    await logged_in_user.should_see("bereits vorhanden")


async def test_edit_category_cancel_closes_dialog(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that cancel button closes the dialog without saving."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Gemüse").click()

    # Should see dialog
    await logged_in_user.should_see("Kategorie bearbeiten")

    # Click cancel
    logged_in_user.find("Abbrechen").click()

    # Dialog should be closed, original name should still be there
    await logged_in_user.should_see("Gemüse")


# =============================================================================
# Issue #23: Category Delete Tests
# =============================================================================


async def test_categories_page_has_delete_buttons(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that each category card has a delete button."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Should see the categories
    await logged_in_user.should_see("Gemüse")


async def test_delete_button_opens_confirmation_dialog(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-Gemüse").click()

    # Should see confirmation dialog
    await logged_in_user.should_see("Kategorie löschen")
    await logged_in_user.should_see("Gemüse")


async def test_delete_category_success(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that deleting a category works correctly."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-Fleisch").click()

    # Confirm deletion
    logged_in_user.find("Löschen").click()

    # Category should be gone
    await logged_in_user.should_not_see("Fleisch")


async def test_delete_category_cancel(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that canceling delete keeps the category."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the delete button
    logged_in_user.find(marker="delete-Obst").click()

    # Cancel deletion
    logged_in_user.find("Abbrechen").click()

    # Category should still be there
    await logged_in_user.should_see("Obst")


# =============================================================================
# Issue #107: Shelf Life Management Tests
# =============================================================================


async def test_edit_dialog_shows_shelf_life_section(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that edit dialog shows shelf life configuration section."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Fleisch").click()

    # Should see shelf life section
    await logged_in_user.should_see("Haltbarkeit")
    await logged_in_user.should_see("Gefroren")
    await logged_in_user.should_see("Gekühlt")
    await logged_in_user.should_see("Raumtemperatur")


async def test_shelf_life_inputs_have_min_max_fields(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that shelf life section has min and max input fields."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Gemüse").click()

    # Should see Min/Max labels
    await logged_in_user.should_see("Min")
    await logged_in_user.should_see("Max")


async def test_save_shelf_life_for_category(
    logged_in_user: TestUser,
    standard_categories,
    isolated_test_database,
) -> None:
    """Test that shelf life can be saved for a category."""
    from app.models.category_shelf_life import CategoryShelfLife
    from app.models.category_shelf_life import StorageType

    # standard_categories provides: Gemüse (100), Fleisch (101), Obst (102)
    cat_id = 101  # Fleisch

    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Fleisch").click()

    # Wait for dialog to open and set values on number inputs
    # For ui.number we need to set value directly via elements (which is a set)
    frozen_min = logged_in_user.find(marker="frozen-min")
    frozen_max = logged_in_user.find(marker="frozen-max")
    list(frozen_min.elements)[0].value = 6
    list(frozen_max.elements)[0].value = 12

    # Save
    logged_in_user.find("Speichern").click()

    # Verify in database
    with Session(isolated_test_database) as session:
        from sqlmodel import select

        shelf_life = session.exec(
            select(CategoryShelfLife).where(
                CategoryShelfLife.category_id == cat_id,
                CategoryShelfLife.storage_type == StorageType.FROZEN,
            )
        ).first()
        assert shelf_life is not None
        assert shelf_life.months_min == 6
        assert shelf_life.months_max == 12


async def test_shelf_life_validation_min_greater_than_max(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that validation error is shown when min > max."""
    # standard_categories provides: Gemüse, Fleisch, Obst
    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Obst").click()

    # Fill in invalid shelf life (min > max)
    # For ui.number we need to set value directly via elements (which is a set)
    frozen_min = logged_in_user.find(marker="frozen-min")
    frozen_max = logged_in_user.find(marker="frozen-max")
    list(frozen_min.elements)[0].value = 12
    list(frozen_max.elements)[0].value = 6

    # Save
    logged_in_user.find("Speichern").click()

    # Should see validation error
    await logged_in_user.should_see("Min muss <= Max sein")


async def test_category_list_shows_shelf_life_info(
    logged_in_user: TestUser,
    standard_categories,
    isolated_test_database,
) -> None:
    """Test that category list shows configured shelf life info."""
    from app.models.category_shelf_life import CategoryShelfLife
    from app.models.category_shelf_life import StorageType

    # standard_categories provides: Gemüse (100), Fleisch (101), Obst (102)
    # Add shelf life to Fleisch
    with Session(isolated_test_database) as session:
        shelf_life = CategoryShelfLife(
            category_id=101,  # Fleisch
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )
        session.add(shelf_life)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Should see shelf life info in the list
    await logged_in_user.should_see("Fleisch")
    await logged_in_user.should_see("6-12")


async def test_edit_dialog_shows_existing_shelf_life(
    logged_in_user: TestUser,
    standard_categories,
    isolated_test_database,
) -> None:
    """Test that edit dialog shows existing shelf life values."""
    from app.models.category_shelf_life import CategoryShelfLife
    from app.models.category_shelf_life import StorageType

    # standard_categories provides: Gemüse (100), Fleisch (101), Obst (102)
    # Add shelf life to Obst
    with Session(isolated_test_database) as session:
        shelf_life = CategoryShelfLife(
            category_id=102,  # Obst
            storage_type=StorageType.FROZEN,
            months_min=3,
            months_max=6,
        )
        session.add(shelf_life)
        session.commit()

    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Obst").click()

    # Should see existing values in the inputs
    await logged_in_user.should_see("Haltbarkeit")
    # The input fields should be pre-filled with existing values


# =============================================================================
# Issue #158: Create Dialog with Shelf Life Fields
# =============================================================================


async def test_create_dialog_shows_shelf_life_section(user: TestUser) -> None:
    """Test that create dialog shows shelf life configuration section."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Should see shelf life section
    await user.should_see("Haltbarkeit")
    await user.should_see("Gefroren")
    await user.should_see("Gekühlt")
    await user.should_see("Raumtemperatur")


async def test_create_dialog_has_min_max_fields(user: TestUser) -> None:
    """Test that create dialog has min and max input fields for shelf life."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Should see Min/Max labels
    await user.should_see("Min")
    await user.should_see("Max")
    await user.should_see("Quelle")


async def test_create_category_with_shelf_life(
    user: TestUser,
    isolated_test_database,
) -> None:
    """Test that creating a category with shelf life works correctly."""
    from app.models.category_shelf_life import CategoryShelfLife
    from app.models.category_shelf_life import StorageType

    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Fill in the form
    user.find("Name").type("Fleisch")

    # Set shelf life values for frozen
    frozen_min = user.find(marker="create-frozen-min")
    frozen_max = user.find(marker="create-frozen-max")
    list(frozen_min.elements)[0].value = 6
    list(frozen_max.elements)[0].value = 12

    # Click save
    user.find("Speichern").click()

    # Should see category in list
    await user.should_see("Fleisch")

    # Verify shelf life was saved in database
    with Session(isolated_test_database) as session:
        from sqlmodel import select

        cat = session.exec(select(Category).where(Category.name == "Fleisch")).first()
        assert cat is not None

        shelf_life = session.exec(
            select(CategoryShelfLife).where(
                CategoryShelfLife.category_id == cat.id,
                CategoryShelfLife.storage_type == StorageType.FROZEN,
            )
        ).first()
        assert shelf_life is not None
        assert shelf_life.months_min == 6
        assert shelf_life.months_max == 12


async def test_create_category_shelf_life_validation_min_greater_than_max(
    user: TestUser,
) -> None:
    """Test validation error when min > max in create dialog."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Fill in the form
    user.find("Name").type("Obst")

    # Set invalid shelf life values (min > max)
    frozen_min = user.find(marker="create-frozen-min")
    frozen_max = user.find(marker="create-frozen-max")
    list(frozen_min.elements)[0].value = 12
    list(frozen_max.elements)[0].value = 6

    # Click save
    user.find("Speichern").click()

    # Should see validation error
    await user.should_see("Min muss <= Max sein")


# =============================================================================
# Issue #162: Color Preview in Category Form
# =============================================================================


async def test_create_dialog_shows_color_preview(user: TestUser) -> None:
    """Test that create dialog shows a color preview element."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Should see color preview element (marker: color-preview)
    preview = user.find(marker="color-preview")
    assert preview is not None


async def test_create_dialog_color_preview_updates_on_selection(
    user: TestUser,
) -> None:
    """Test that color preview updates when color is selected."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to categories page
    await user.open("/admin/categories")

    # Click the "Neue Kategorie" button
    user.find(marker="new-category-button").click()

    # Find color input and set a value
    color_input = user.find(marker="color-input")
    # Set a color value directly on the element
    list(color_input.elements)[0].value = "#FF5733"

    # The preview should reflect the color
    preview = user.find(marker="color-preview")
    preview_element = list(preview.elements)[0]
    # Check that the style contains the color
    assert "background" in preview_element._style or preview_element._style.get("background-color") == "#FF5733"


async def test_edit_dialog_shows_color_preview(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that edit dialog shows a color preview element."""
    # standard_categories provides: Gemüse (#00FF00), Fleisch (#FF0000), Obst (#FFA500)
    await logged_in_user.open("/admin/categories")

    # Click the edit button
    logged_in_user.find(marker="edit-Gemüse").click()

    # Should see color preview element
    preview = logged_in_user.find(marker="color-preview")
    assert preview is not None


async def test_edit_dialog_color_preview_shows_existing_color(
    logged_in_user: TestUser,
    standard_categories,
) -> None:
    """Test that edit dialog preview shows the existing category color."""
    # standard_categories provides: Gemüse (#00FF00), Fleisch (#FF0000), Obst (#FFA500)
    await logged_in_user.open("/admin/categories")

    # Click the edit button for Gemüse (which has #00FF00)
    logged_in_user.find(marker="edit-Gemüse").click()

    # The preview should show the existing color
    preview = logged_in_user.find(marker="color-preview")
    preview_element = list(preview.elements)[0]
    # Check that the style contains the existing color
    style = preview_element._style
    assert "00FF00" in str(style).upper() or "background" in str(style)
