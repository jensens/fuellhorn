"""UI Tests for Wizard Back Button - Issue #48.

Test that wizard UI renders correctly.

NOTE: Full back-button behavior (data preservation across steps) is tested
in E2E tests (tests/test_e2e/test_wizard.py) because NiceGUI's testing
framework cannot trigger form validation bindings programmatically.

See:
- test_wizard_back_button_preserves_data
- test_wizard_back_button_roundtrip_preserves_summary
"""

from app.models import Location
from app.models.location import LocationType
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="location_in_db")
def location_in_db_fixture(isolated_test_database) -> Location:
    """Create a location in the test database."""
    with Session(isolated_test_database) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)
        return location


async def test_wizard_shows_step1_initially(logged_in_user: User, location_in_db: Location) -> None:
    """Test that wizard starts at Step 1."""
    # Navigate to wizard (already logged in via fixture)
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")
    await logged_in_user.should_see("Basisinformationen")
    await logged_in_user.should_see("Produktname")


async def test_wizard_shows_weiter_button(logged_in_user: User, location_in_db: Location) -> None:
    """Test that wizard shows Weiter button on Step 1."""
    # Navigate to wizard (already logged in via fixture)
    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Weiter")
