"""UI Tests for Category Chip Group component."""

from app.models.category import Category
from nicegui.testing import User
from sqlmodel import Session


async def test_category_chips_page_loads(user: User) -> None:
    """Test that category chips page loads without error."""
    await user.open("/test/category-chips")

    # Verify page loads
    await user.should_see("Category Chips Test")


async def test_category_chips_displays_categories(user: User, isolated_test_database) -> None:
    """Test that category chips are displayed when categories exist."""
    # Create test category in database
    with Session(isolated_test_database) as session:
        category = Category(
            name="Testkat Obst",
            color="#4A7C59",
            created_by=1,
        )
        session.add(category)
        session.commit()

    await user.open("/test/category-chips")

    # Verify page loads
    await user.should_see("Category Chips Test")

    # Verify category is visible
    await user.should_see("Testkat Obst")


async def test_category_chips_preselected_value(user: User) -> None:
    """Test that preselected value page loads correctly."""
    await user.open("/test/category-chips-preselected")

    # Verify the page loads
    await user.should_see("Category Chips Test (Preselected)")


async def test_category_chips_shows_selection(user: User) -> None:
    """Test that initially no selection is shown."""
    await user.open("/test/category-chips")

    # Initially no selection
    await user.should_see("Selected: None")


async def test_category_chips_standalone_group_gets_heading_next_to_groups(user: User) -> None:
    """Ungrouped categories get their own heading when real groups exist (#457)."""
    await user.open("/test/category-chips-grouped")

    await user.should_see("Fleisch")
    await user.should_see("Sonstiges")
    await user.should_see("Gemüse")


async def test_category_chips_only_standalone_has_no_heading(user: User, isolated_test_database) -> None:
    """Without any groups, ungrouped categories stay without heading (#457)."""
    with Session(isolated_test_database) as session:
        session.add(Category(name="Testkat Obst", color="#4A7C59", created_by=1))
        session.commit()

    await user.open("/test/category-chips")

    await user.should_see("Testkat Obst")
    await user.should_not_see("Sonstiges")
