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
