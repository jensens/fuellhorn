"""UI Tests for Location Chip Group component."""

from app.models.location import Location
from app.models.location import LocationType
from nicegui.testing import User
from sqlmodel import Session


async def test_location_chips_page_loads(user: User) -> None:
    """Test that location chips page loads without error."""
    await user.open("/test/location-chips")

    # Verify page loads
    await user.should_see("Location Chips Test")


async def test_location_chips_displays_locations(user: User, isolated_test_database) -> None:
    """Test that location chips are displayed when locations exist."""
    # Create test location in database
    with Session(isolated_test_database) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()

    await user.open("/test/location-chips")

    # Verify page loads
    await user.should_see("Location Chips Test")

    # Verify location is visible
    await user.should_see("Tiefkühltruhe")


async def test_location_chips_preselected_value(user: User) -> None:
    """Test that preselected value page loads correctly."""
    await user.open("/test/location-chips-preselected")

    # Verify the page loads
    await user.should_see("Location Chips Test (Preselected)")


async def test_location_chips_shows_selection(user: User) -> None:
    """Test that initially no selection is shown."""
    await user.open("/test/location-chips")

    # Initially no selection
    await user.should_see("Selected: None")
