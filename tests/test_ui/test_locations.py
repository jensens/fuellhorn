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
