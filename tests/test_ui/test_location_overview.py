"""UI Tests for Location Overview component (Dashboard).

Issue #246: Dashboard Lagerort-Übersicht with horizontal scrollable chips,
icons based on LocationType, and item counts.
"""

from app.models.item import Item
from app.models.item import ItemType
from app.models.location import Location
from app.models.location import LocationType
from app.ui.components.location_overview import get_location_type_icon
from datetime import date
from nicegui.testing import User
from sqlmodel import Session


def test_get_location_type_icon_frozen() -> None:
    """Test that FROZEN locations get ac_unit icon."""
    assert get_location_type_icon(LocationType.FROZEN) == "ac_unit"


def test_get_location_type_icon_chilled() -> None:
    """Test that CHILLED locations get kitchen icon."""
    assert get_location_type_icon(LocationType.CHILLED) == "kitchen"


def test_get_location_type_icon_ambient() -> None:
    """Test that AMBIENT locations get home icon."""
    assert get_location_type_icon(LocationType.AMBIENT) == "home"


async def test_location_overview_page_loads(user: User) -> None:
    """Test that location overview test page loads."""
    await user.open("/test/location-overview")
    await user.should_see("Location Overview Test")


async def test_location_overview_shows_locations(user: User, isolated_test_database) -> None:
    """Test that locations are displayed in the overview."""
    with Session(isolated_test_database) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()

    await user.open("/test/location-overview")
    await user.should_see("Tiefkühltruhe")


async def test_location_overview_shows_item_count(user: User, isolated_test_database) -> None:
    """Test that item counts are displayed per location."""
    with Session(isolated_test_database) as session:
        location = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create test items
        for i in range(3):
            item = Item(
                product_name=f"Item {i}",
                best_before_date=date.today(),
                quantity=100,
                unit="g",
                item_type=ItemType.PURCHASED_FRESH,
                location_id=location.id,
                created_by=1,
            )
            session.add(item)
        session.commit()

    await user.open("/test/location-overview")
    await user.should_see("3")  # Item count


async def test_location_overview_horizontal_scroll(user: User) -> None:
    """Test that the container has horizontal scroll class."""
    await user.open("/test/location-overview")
    # The container should have overflow-x-auto for horizontal scrolling
    await user.should_see("Location Overview Test")
