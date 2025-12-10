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
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify action buttons are present with clear labels
    await user.should_see("Alles entnehmen")
    await user.should_see("Teilentnahme")
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
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    # Open test page with bottom sheet
    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify consume button is present with clear label
    await user.should_see("Alles entnehmen")
    await user.should_see("Brokkoli")


async def test_bottom_sheet_consume_marks_item_consumed(logged_in_user: User) -> None:
    """Test that clicking 'Alles entnehmen' marks the item as consumed."""
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
            product_name="Spinat",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await logged_in_user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Alles entnehmen" button (using marker for custom icon button)
    logged_in_user.find(marker="consume-button").click()

    # Verify success notification
    await logged_in_user.should_see("Spinat vollständig entnommen")

    # Verify item is marked as consumed in database
    with next(get_session()) as session:
        updated_item = session.get(Item, item_id)
        assert updated_item is not None
        assert updated_item.is_consumed is True


async def test_bottom_sheet_consume_creates_withdrawal_entry(logged_in_user: User) -> None:
    """Test that 'Alles entnehmen' creates a withdrawal entry for the full quantity."""
    from app.database import get_session
    from app.models.withdrawal import Withdrawal
    from sqlmodel import select

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
            product_name="Himbeeren",
            item_type=ItemType.HOMEMADE_FROZEN,
            quantity=350,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await logged_in_user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Alles entnehmen" button (using marker for custom icon button)
    logged_in_user.find(marker="consume-button").click()

    # Verify success notification
    await logged_in_user.should_see("Himbeeren vollständig entnommen")

    # Verify withdrawal entry was created in database
    with next(get_session()) as session:
        withdrawals = list(session.exec(select(Withdrawal).where(Withdrawal.item_id == item_id)).all())
        assert len(withdrawals) == 1
        assert withdrawals[0].quantity == 350
        assert withdrawals[0].withdrawn_by is not None


# =============================================================================
# Partial Withdrawal Tests (Issue #16)
# =============================================================================


async def test_bottom_sheet_withdraw_shows_quantity_dialog(user: User) -> None:
    """Test that clicking 'Teilentnahme' shows quantity input dialog."""
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
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Teilentnahme" button
    user.find("Teilentnahme").click()

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
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Teilentnahme" button to open dialog
    user.find("Teilentnahme").click()

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
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Teilentnahme" button to open dialog
    user.find("Teilentnahme").click()

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


async def test_bottom_sheet_withdraw_creates_withdrawal_entry(logged_in_user: User) -> None:
    """Test that partial withdrawal creates a withdrawal entry in database."""
    from app.database import get_session
    from app.models.withdrawal import Withdrawal
    from sqlmodel import select

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
            product_name="Brokkoli",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=800,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await logged_in_user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Teilentnahme" button to open dialog
    logged_in_user.find("Teilentnahme").click()

    # Enter valid quantity
    number_input = list(logged_in_user.find(kind=ui.number).elements)[0]
    number_input.value = 300

    # Confirm
    logged_in_user.find("Bestätigen").click()

    # Verify success notification
    await logged_in_user.should_see("300 g entnommen")

    # Verify withdrawal entry was created in database
    with next(get_session()) as session:
        withdrawals = list(session.exec(select(Withdrawal).where(Withdrawal.item_id == item_id)).all())
        assert len(withdrawals) == 1
        assert withdrawals[0].quantity == 300
        assert withdrawals[0].withdrawn_by is not None


# =============================================================================
# Edit Button Tests (Issue #176)
# =============================================================================


async def test_bottom_sheet_edit_button_calls_callback(user: User) -> None:
    """Test that clicking 'Bearbeiten' calls the on_edit callback."""
    from app.database import get_session

    with next(get_session()) as session:
        location = Location(
            name="Kühlschrank",
            location_type=LocationType.CHILLED,
            created_by=1,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        item = Item(
            product_name="Joghurt",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=1,
            unit="Becher",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=14),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Click on "Bearbeiten" button (using marker for custom icon button)
    user.find(marker="edit-button").click()

    # Verify on_edit callback was triggered (test page shows notify)
    await user.should_see("Bearbeiten: Joghurt")


# =============================================================================
# Withdrawal History Tests (Issue #168)
# =============================================================================


async def test_bottom_sheet_shows_withdrawal_history(user: User) -> None:
    """Test that bottom sheet shows withdrawal history when entries exist."""
    from app.database import get_session
    from app.models.user import User as UserModel
    from app.models.withdrawal import Withdrawal
    from datetime import datetime

    with next(get_session()) as session:
        # Create test user
        test_user = UserModel(
            username="testuser",
            password_hash="hash",
            email="testuser@example.com",
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_user_id = test_user.id

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
            product_name="Erbsen",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=300,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

        # Create withdrawal entry
        withdrawal = Withdrawal(
            item_id=item_id,
            quantity=200,
            withdrawn_at=datetime(2024, 6, 15, 14, 30),
            withdrawn_by=test_user_id,
        )
        session.add(withdrawal)
        session.commit()

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify history section is shown
    await user.should_see("Entnahme-Historie")
    await user.should_see("200")
    await user.should_see("testuser")


async def test_bottom_sheet_no_history_when_empty(user: User) -> None:
    """Test that bottom sheet doesn't show history section when no entries."""
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

        # Create test item with no withdrawals
        item = Item(
            product_name="Brokkoli",
            item_type=ItemType.PURCHASED_FROZEN,
            quantity=500,
            unit="g",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=180),
            freeze_date=date.today(),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify item is shown but no history section
    await user.should_see("Brokkoli")
    await user.should_not_see("Entnahme-Historie")


async def test_bottom_sheet_history_shows_multiple_entries(user: User) -> None:
    """Test that bottom sheet shows all withdrawal entries sorted by date."""
    from app.database import get_session
    from app.models.user import User as UserModel
    from app.models.withdrawal import Withdrawal
    from datetime import datetime

    with next(get_session()) as session:
        # Create test user
        test_user = UserModel(
            username="lagermeister",
            password_hash="hash",
            email="lagermeister@example.com",
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_user_id = test_user.id

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
            product_name="Joghurt",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=2,
            unit="Becher",
            location_id=location.id,
            best_before_date=date.today() + timedelta(days=14),
            created_by=1,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id

        # Create multiple withdrawal entries (older first, newer second)
        withdrawal1 = Withdrawal(
            item_id=item_id,
            quantity=1,
            withdrawn_at=datetime(2024, 6, 10, 10, 0),
            withdrawn_by=test_user_id,
        )
        withdrawal2 = Withdrawal(
            item_id=item_id,
            quantity=2,
            withdrawn_at=datetime(2024, 6, 15, 14, 30),
            withdrawn_by=test_user_id,
        )
        session.add(withdrawal1)
        session.add(withdrawal2)
        session.commit()

    await user.open(f"/test/bottom-sheet/{item_id}")

    # Verify history section shows all entries
    await user.should_see("Entnahme-Historie")
    await user.should_see("lagermeister")
