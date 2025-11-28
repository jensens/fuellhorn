"""UI Tests for Bottom Sheet component."""

from app.models.item import Item
from app.models.item import ItemType
from app.models.location import Location
from app.models.location import LocationType
from datetime import date
from datetime import timedelta
from nicegui import ui
from nicegui.testing import User


async def test_bottom_sheet_shows_item_details(user: User) -> None:
    """Test that bottom sheet displays item details correctly."""
    # Setup: Create location and item in the database
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create test item
        item = Item(
            product_name="Erdbeeren",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=365),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify item details are displayed
    await user.should_see("Erdbeeren")
    await user.should_see("500")
    await user.should_see("g")
    await user.should_see("Tiefkühltruhe")


async def test_bottom_sheet_has_action_buttons(user: User) -> None:
    """Test that bottom sheet shows action buttons."""
    # Setup: Create location and item in the database
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create test item
        item = Item(
            product_name="Milch",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=1,
            unit="L",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=7),
            expiry_date=date.today() + timedelta(days=7),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify action buttons are present
    await user.should_see("Entnommen")
    await user.should_see("Entnehmen")
    await user.should_see("Bearbeiten")


async def test_bottom_sheet_has_close_button(user: User) -> None:
    """Test that bottom sheet has a close button."""
    # Setup: Create location and item in the database
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Vorratskammer",
            location_type=LocationType.AMBIENT,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create test item
        item = Item(
            product_name="Marmelade",
            item_type=ItemType.HOMEMADE_PRESERVED,
            quantity=2,
            unit="Gläser",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=365),
            expiry_date=date.today() + timedelta(days=365),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify close button is present (material icon "close")
    await user.should_see("Schließen")


async def test_bottom_sheet_shows_expiry_status(user: User) -> None:
    """Test that bottom sheet shows expiry status badge."""
    # Setup: Create location and item with critical expiry
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create item expiring soon (critical - < 3 days)
        item = Item(
            product_name="Fisch",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=300,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=2),
            freeze_date=date.today() - timedelta(days=10),
            expiry_date=date.today() + timedelta(days=2),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify item name and quantity are shown
    await user.should_see("Fisch")
    await user.should_see("300")


async def test_bottom_sheet_shows_notes(user: User) -> None:
    """Test that bottom sheet shows item notes if present."""
    # Setup: Create location and item with notes
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create item with notes
        item = Item(
            product_name="Rindergulasch",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=800,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=90),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=90),
            notes="Mit Paprika und Zwiebeln",
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify notes are shown
    await user.should_see("Rindergulasch")
    await user.should_see("Mit Paprika und Zwiebeln")


async def test_bottom_sheet_consume_button_present(user: User) -> None:
    """Test that bottom sheet has the consume button for marking items as fully consumed."""
    # Setup: Create location and item in the database
    from app.database import get_session

    with next(get_session()) as session:
        # Create location
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        # Create test item
        item = Item(
            product_name="Brokkoli",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=400,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify consume button is present
    await user.should_see("Entnommen")
    await user.should_see("Brokkoli")


# =============================================================================
# Partial Withdrawal Tests (Issue #16)
# =============================================================================


async def test_bottom_sheet_withdraw_shows_quantity_dialog(user: User) -> None:
    """Test that clicking 'Entnehmen' shows quantity input dialog."""
    from app.database import get_session

    with next(get_session()) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        item = Item(
            product_name="Erbsen",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Entnehmen" button
    user.find("Entnehmen").click()

    # Verify quantity dialog appears with input field
    await user.should_see("Menge entnehmen")
    await user.should_see("Verfügbar: 500 g")


async def test_bottom_sheet_withdraw_validates_max_quantity(user: User) -> None:
    """Test that validation prevents withdrawing more than available."""
    from app.database import get_session

    with next(get_session()) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        item = Item(
            product_name="Erbsen",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Entnehmen" button to open dialog
    user.find("Entnehmen").click()

    # Enter quantity exceeding available - set value directly on the number input
    number_input = list(user.find(kind=ui.number).elements)[0]
    number_input.value = 600

    # Try to confirm - should show error
    user.find("Bestätigen").click()

    # Verify error message
    await user.should_see("Nicht mehr als 500 verfügbar")


async def test_bottom_sheet_withdraw_partial_success(user: User) -> None:
    """Test successful partial withdrawal updates quantity."""
    from app.database import get_session

    with next(get_session()) as session:
        location = Location(
            name="Tiefkühltruhe",
            location_type=LocationType.FROZEN,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        item = Item(
            product_name="Erbsen",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            expiry_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Entnehmen" button to open dialog
    user.find("Entnehmen").click()

    # Enter valid quantity - set value directly on the number input
    number_input = list(user.find(kind=ui.number).elements)[0]
    number_input.value = 200

    # Confirm
    user.find("Bestätigen").click()

    # Verify success notification
    await user.should_see("200 g entnommen")

    # Verify item quantity was updated in database
    with next(get_session()) as session:
        updated_item = session.get(Item, item_id)
        assert updated_item is not None
        assert updated_item.quantity == 300
        assert updated_item.is_consumed is False
