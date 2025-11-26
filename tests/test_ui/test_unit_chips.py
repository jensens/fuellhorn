"""UI Tests for Unit Chip Group component."""

from nicegui.testing import User


async def test_unit_chips_displays_all_units(user: User) -> None:
    """Test that all 6 units are displayed."""
    await user.open("/test/unit-chips")

    # Verify all unit labels are visible
    await user.should_see("g")
    await user.should_see("kg")
    await user.should_see("ml")
    await user.should_see("l")
    await user.should_see("Stück")
    await user.should_see("Packung")


async def test_unit_chips_preselected_value(user: User) -> None:
    """Test that preselected value is displayed correctly."""
    await user.open("/test/unit-chips-preselected")

    # The page has "kg" preselected
    await user.should_see("kg")


async def test_unit_chips_page_title(user: User) -> None:
    """Test that the test page has correct title."""
    await user.open("/test/unit-chips")
    await user.should_see("Unit Chips Test")
