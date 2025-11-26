"""UI Tests for ItemType Chip Group component."""

from nicegui.testing import User


async def test_item_type_chips_displays_all_types(user: User) -> None:
    """Test that all 5 item types are displayed."""
    await user.open("/test/item-type-chips")

    # Verify all item type labels are visible
    await user.should_see("Frisch eingekauft")
    await user.should_see("TK-Ware gekauft")
    await user.should_see("eingefroren")  # Part of "Frisch gekauft → eingefroren"
    await user.should_see("Selbst eingefroren")
    await user.should_see("Selbst eingemacht")


async def test_item_type_chips_preselected_value(user: User) -> None:
    """Test that preselected value is displayed correctly."""
    await user.open("/test/item-type-chips-preselected")

    # The page has HOMEMADE_FROZEN preselected
    await user.should_see("Selbst eingefroren")


async def test_item_type_chips_page_title(user: User) -> None:
    """Test that the test page has correct title."""
    await user.open("/test/item-type-chips")
    await user.should_see("ItemType Chips Test")


async def test_item_type_chips_initial_selection_label(user: User) -> None:
    """Test that initial selection label is shown."""
    await user.open("/test/item-type-chips")
    # Initially no selection
    await user.should_see("Selected: None")
