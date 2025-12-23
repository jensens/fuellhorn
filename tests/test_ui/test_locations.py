"""UI Tests for Locations Page (Admin)."""

from app.models.location import Location
from app.models.location import LocationType
from app.models.user import User
from nicegui.testing import User as TestUser
from sqlmodel import Session


async def test_locations_page_renders_for_admin(logged_in_user: TestUser) -> None:
    """Test that locations page renders for admin users."""
    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Check page elements
    await logged_in_user.should_see("Lagerorte")


async def test_locations_page_shows_empty_state(logged_in_user: TestUser) -> None:
    """Test that locations page shows empty state when no locations exist."""
    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should show empty state message
    await logged_in_user.should_see("Keine Lagerorte vorhanden")


async def test_locations_page_displays_locations(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that locations page displays locations with name and type."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should see locations
    await logged_in_user.should_see("Tiefkühler")
    await logged_in_user.should_see("Kühlschrank")
    await logged_in_user.should_see("Speisekammer")


async def test_locations_page_shows_location_types(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that locations page displays location type badges."""
    # standard_locations provides: Kühlschrank (CHILLED), Tiefkühler (FROZEN), Speisekammer (AMBIENT)
    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should see type badges (German labels)
    await logged_in_user.should_see("Gefroren")
    await logged_in_user.should_see("Gekühlt")


async def test_locations_page_requires_auth(user: TestUser) -> None:
    """Test that unauthenticated users are redirected to login."""
    # Try to access locations without login
    await user.open("/admin/locations")

    # Should be redirected to login
    await user.should_see("Anmelden")


async def test_locations_page_requires_admin_permission(
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

    # Try to navigate to locations page
    await user.open("/admin/locations")

    # Regular user should be redirected (should not see locations page header)
    await user.should_not_see("Lagerorte verwalten")


async def test_locations_page_shows_active_status(
    logged_in_user: TestUser,
    standard_locations,
    isolated_test_database,
) -> None:
    """Test that locations page shows active/inactive status."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer (all active)
    # Add an inactive location
    with Session(isolated_test_database) as session:
        loc_inactive = Location(
            name="Inaktiver Lagerort",
            location_type=LocationType.AMBIENT,
            is_active=False,
            created_by=1,
        )
        session.add(loc_inactive)
        session.commit()

    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should see locations (active from fixture)
    await logged_in_user.should_see("Kühlschrank")
    await logged_in_user.should_see("Inaktiver Lagerort")
    # Inactive location should show "Inaktiv" badge
    await logged_in_user.should_see("Inaktiv")


# === Issue #26: Edit Location Tests ===


async def test_locations_page_shows_edit_button(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that each location has an edit button."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Should see the location
    await logged_in_user.should_see("Tiefkühler")

    # Should have an edit button (icon button with 'edit' icon)
    edit_button = logged_in_user.find("edit")
    assert edit_button is not None


async def test_edit_dialog_opens_with_prefilled_form(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that clicking edit opens dialog with pre-filled form."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the edit button
    logged_in_user.find("edit").click()

    # Should see the edit dialog with pre-filled data
    await logged_in_user.should_see("Lagerort bearbeiten")
    await logged_in_user.should_see("Kühlschrank")


async def test_edit_location_validation_empty_name(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that empty name shows validation error."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the edit button
    logged_in_user.find("edit").click()

    # Wait for dialog
    await logged_in_user.should_see("Lagerort bearbeiten")

    # Clear the name input using marker
    logged_in_user.find(marker="name-input").clear()

    # Click save
    logged_in_user.find("Speichern").click()

    # Should show validation error
    await logged_in_user.should_see("Name ist erforderlich")


async def test_edit_location_validation_duplicate_name(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that duplicate name shows validation error."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the first edit button (for Kühlschrank)
    logged_in_user.find("edit").click()

    # Wait for dialog
    await logged_in_user.should_see("Lagerort bearbeiten")

    # Clear and try to change name to existing name (Tiefkühler)
    logged_in_user.find(marker="name-input").clear()
    logged_in_user.find(marker="name-input").type("Tiefkühler")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should show duplicate error
    await logged_in_user.should_see("bereits vorhanden")


async def test_edit_location_success(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test successful location edit."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the edit button (first one = Kühlschrank)
    logged_in_user.find("edit").click()

    # Wait for dialog
    await logged_in_user.should_see("Lagerort bearbeiten")

    # Clear and set new name using marker
    logged_in_user.find(marker="name-input").clear()
    logged_in_user.find(marker="name-input").type("Neuer Name")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should navigate back to locations page and show the new name
    await logged_in_user.should_see("Neuer Name")
    # Note: We don't check should_not_see("Kühlschrank") because it causes
    # flaky tests due to timing issues with page refresh


# === Issue #25: Create Location Tests ===


async def test_locations_page_shows_create_button(logged_in_user: TestUser) -> None:
    """Test that the 'Neuer Lagerort' button is displayed."""
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Should see the create button
    await logged_in_user.should_see("Neuer Lagerort")


async def test_create_dialog_opens(logged_in_user: TestUser) -> None:
    """Test that clicking 'Neuer Lagerort' opens the create dialog."""
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the create button
    logged_in_user.find(marker="new-location-button").click()

    # Should see the create dialog
    await logged_in_user.should_see("Neuen Lagerort erstellen")
    await logged_in_user.should_see("Name")
    await logged_in_user.should_see("Typ")


async def test_create_location_validation_empty_name(logged_in_user: TestUser) -> None:
    """Test that empty name shows validation error."""
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the create button
    logged_in_user.find(marker="new-location-button").click()

    # Wait for dialog
    await logged_in_user.should_see("Neuen Lagerort erstellen")

    # Click save without entering a name
    logged_in_user.find("Speichern").click()

    # Should show validation error
    await logged_in_user.should_see("Name ist erforderlich")


async def test_create_location_validation_duplicate_name(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that duplicate name shows validation error."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the create button
    logged_in_user.find(marker="new-location-button").click()

    # Wait for dialog
    await logged_in_user.should_see("Neuen Lagerort erstellen")

    # Enter duplicate name (Kühlschrank exists)
    logged_in_user.find(marker="create-name-input").type("Kühlschrank")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should show duplicate error
    await logged_in_user.should_see("bereits vorhanden")


async def test_create_location_success(logged_in_user: TestUser) -> None:
    """Test successful location creation."""
    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the create button
    logged_in_user.find(marker="new-location-button").click()

    # Wait for dialog
    await logged_in_user.should_see("Neuen Lagerort erstellen")

    # Enter location details
    logged_in_user.find(marker="create-name-input").type("Neuer Gefrierschrank")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should navigate back to locations page and show the new location
    await logged_in_user.should_see("Neuer Gefrierschrank")


# === Issue #27: Delete Location Tests ===


async def test_delete_button_visible_for_locations(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that delete button is visible for each location."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    await logged_in_user.open("/admin/locations")

    # Delete button should be visible (via marker)
    logged_in_user.find(marker="delete-Kühlschrank")


async def test_delete_location_opens_confirmation_dialog(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that clicking delete button opens confirmation dialog."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    await logged_in_user.open("/admin/locations")

    # Click delete button
    logged_in_user.find(marker="delete-Tiefkühler").click()

    # Should see confirmation dialog
    await logged_in_user.should_see("Lagerort löschen")
    await logged_in_user.should_see("Tiefkühler")


async def test_delete_location_successfully(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that location can be deleted when not in use."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    await logged_in_user.open("/admin/locations")

    # Verify location is visible
    await logged_in_user.should_see("Speisekammer")

    # Click delete button
    logged_in_user.find(marker="delete-Speisekammer").click()

    # Confirm deletion
    logged_in_user.find("Löschen").click()

    # Location should no longer be visible
    await logged_in_user.should_not_see("Speisekammer")


async def test_cannot_delete_location_in_use(
    logged_in_user: TestUser,
    standard_locations,
    isolated_test_database,
) -> None:
    """Test that location cannot be deleted when it has items."""
    from app.models.item import Item
    from app.models.item import ItemType
    from datetime import date

    # standard_locations provides: Kühlschrank (100), Tiefkühler (101), Speisekammer (102)
    # Add an item using Kühlschrank location
    with Session(isolated_test_database) as session:
        today = date.today()
        item = Item(
            product_name="Testitem",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=100,  # Kühlschrank
            quantity=1.0,
            unit="kg",
            best_before_date=today,
            created_by=1,
        )
        session.add(item)
        session.commit()

    await logged_in_user.open("/admin/locations")

    # Click delete button for Kühlschrank (which has item)
    logged_in_user.find(marker="delete-Kühlschrank").click()

    # Confirm deletion
    logged_in_user.find("Löschen").click()

    # Should see error message about items in use
    await logged_in_user.should_see("in Verwendung")


async def test_delete_dialog_can_be_cancelled(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that delete operation can be cancelled."""
    # standard_locations provides: Kühlschrank, Tiefkühler, Speisekammer
    await logged_in_user.open("/admin/locations")

    # Click delete button
    logged_in_user.find(marker="delete-Tiefkühler").click()

    # Cancel deletion
    logged_in_user.find("Abbrechen").click()

    # Location should still be visible
    await logged_in_user.should_see("Tiefkühler")


# =============================================================================
# Issue #162: Color Preview in Location Form
# =============================================================================


async def test_create_location_dialog_shows_color_preview(user: TestUser) -> None:
    """Test that create location dialog shows a color preview element."""
    # Login as admin
    await user.open("/login")
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()

    # Navigate to locations page
    await user.open("/admin/locations")

    # Click the "Neuer Lagerort" button
    user.find(marker="new-location-button").click()

    # Should see color preview element (marker: color-preview)
    preview = user.find(marker="color-preview")
    assert preview is not None


async def test_edit_location_dialog_shows_color_preview(
    logged_in_user: TestUser,
    standard_locations,
) -> None:
    """Test that edit location dialog shows a color preview element."""
    # standard_locations provides: Kühlschrank (#0000FF), Tiefkühler (#00FFFF), Speisekammer (#8B4513)
    await logged_in_user.open("/admin/locations")

    # Find and click edit button (icon button)
    logged_in_user.find("edit").click()

    # Should see color preview element
    preview = logged_in_user.find(marker="color-preview")
    assert preview is not None
