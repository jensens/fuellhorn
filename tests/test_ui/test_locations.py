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
    isolated_test_database,
) -> None:
    """Test that locations page displays locations with name and type."""
    # Create test locations
    with Session(isolated_test_database) as session:
        loc1 = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,  # admin user from fixture
        )
        loc2 = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        loc3 = Location(
            name="Speisekammer",
            location_type=LocationType.AMBIENT,
            created_by=1,
        )
        session.add(loc1)
        session.add(loc2)
        session.add(loc3)
        session.commit()

    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should see locations
    await logged_in_user.should_see("Tiefkühltruhe")
    await logged_in_user.should_see("Kühlschrank")
    await logged_in_user.should_see("Speisekammer")


async def test_locations_page_shows_location_types(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that locations page displays location type badges."""
    # Create test locations with different types
    with Session(isolated_test_database) as session:
        loc1 = Location(
            name="Gefrierschrank",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        loc2 = Location(
            name="Kühlfach",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        session.add(loc1)
        session.add(loc2)
        session.commit()

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
    isolated_test_database,
) -> None:
    """Test that locations page shows active/inactive status."""
    # Create test locations with different status
    with Session(isolated_test_database) as session:
        loc_active = Location(
            name="Aktiver Lagerort",
            location_type=LocationType.AMBIENT,
            is_active=True,
            created_by=1,
        )
        loc_inactive = Location(
            name="Inaktiver Lagerort",
            location_type=LocationType.AMBIENT,
            is_active=False,
            created_by=1,
        )
        session.add(loc_active)
        session.add(loc_inactive)
        session.commit()

    # Navigate to locations page (already logged in via fixture)
    await logged_in_user.open("/admin/locations")

    # Should see both locations
    await logged_in_user.should_see("Aktiver Lagerort")
    await logged_in_user.should_see("Inaktiver Lagerort")
    # Inactive location should show "Inaktiv" badge
    await logged_in_user.should_see("Inaktiv")


# === Issue #26: Edit Location Tests ===


async def test_locations_page_shows_edit_button(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that each location has an edit button."""
    # Create a test location
    with Session(isolated_test_database) as session:
        loc = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(loc)
        session.commit()

    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Should see the location
    await logged_in_user.should_see("Tiefkühltruhe")

    # Should have an edit button (icon button with 'edit' icon)
    edit_button = logged_in_user.find("edit")
    assert edit_button is not None


async def test_edit_dialog_opens_with_prefilled_form(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that clicking edit opens dialog with pre-filled form."""
    # Create a test location
    with Session(isolated_test_database) as session:
        loc = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            description="Hauptkühlschrank",
            created_by=1,
        )
        session.add(loc)
        session.commit()

    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the edit button
    logged_in_user.find("edit").click()

    # Should see the edit dialog with pre-filled data
    await logged_in_user.should_see("Lagerort bearbeiten")
    await logged_in_user.should_see("Kühlschrank")


async def test_edit_location_validation_empty_name(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test that empty name shows validation error."""
    # Create a test location
    with Session(isolated_test_database) as session:
        loc = Location(
            name="Speisekammer",
            location_type=LocationType.AMBIENT,
            created_by=1,
        )
        session.add(loc)
        session.commit()

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
    isolated_test_database,
) -> None:
    """Test that duplicate name shows validation error."""
    # Create two test locations
    with Session(isolated_test_database) as session:
        loc1 = Location(
            name="Gefrierschrank",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        loc2 = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        session.add(loc1)
        session.add(loc2)
        session.commit()

    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the first edit button (for Gefrierschrank)
    logged_in_user.find("edit").click()

    # Wait for dialog
    await logged_in_user.should_see("Lagerort bearbeiten")

    # Clear and try to change name to existing name (Kühlschrank)
    logged_in_user.find(marker="name-input").clear()
    logged_in_user.find(marker="name-input").type("Kühlschrank")

    # Click save
    logged_in_user.find("Speichern").click()

    # Should show duplicate error
    await logged_in_user.should_see("bereits vorhanden")


async def test_edit_location_success(
    logged_in_user: TestUser,
    isolated_test_database,
) -> None:
    """Test successful location edit."""
    # Create a test location
    with Session(isolated_test_database) as session:
        loc = Location(
            name="Alter Name",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(loc)
        session.commit()

    # Navigate to locations page
    await logged_in_user.open("/admin/locations")

    # Click the edit button
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
    await logged_in_user.should_not_see("Alter Name")
