"""UI Tests: Swipe "Alles entnehmen" auf Vorratsliste und Dashboard (Issue #367).

Vorher: der Swipe-Handler rief ``mark_item_consumed`` ohne Nutzer, es entstand kein
Withdrawal, der Artikel war weder aktiv noch unter "Entnommene" zu finden, es gab
keine Rückfrage und kein Fehlerhandling.
"""

from app.models import Item
from app.models import ItemType
from app.models import LocationType
from app.models import Withdrawal
from app.services import item_service
from app.services import location_service
from datetime import date
from datetime import timedelta
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


SWIPE_ALLES = {"detail": {"action": "alles"}}


@pytest.fixture(name="yoghurt_id")
def yoghurt_id_fixture(isolated_test_database) -> int:
    """Joghurt mit MHD in 2 Tagen (erscheint auch unter 'Bald ablaufend')."""
    with Session(isolated_test_database) as session:
        fridge = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, created_by=1)
        item = item_service.create_item(
            session,
            product_name="Joghurt",
            best_before_date=date.today() + timedelta(days=2),
            quantity=4,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,  # type: ignore[arg-type]
            created_by=1,
        )
        assert item.id is not None
        return item.id


def _withdrawals(db, item_id: int) -> list[Withdrawal]:
    with Session(db) as session:
        return list(session.exec(select(Withdrawal).where(Withdrawal.item_id == item_id)).all())


async def _swipe_consume_all(user: User, item_id: int) -> None:
    user.find(marker=f"swipe-item-{item_id}").trigger("swipeaction", SWIPE_ALLES)
    await user.should_see("Alles entnehmen?")
    user.find(marker="consume-all-confirm").click()


async def test_items_swipe_consume_all_records_withdrawal_for_current_user(
    logged_in_user: User, isolated_test_database, yoghurt_id: int
) -> None:
    """Nach Rückfrage wird der Artikel verbraucht und ein Withdrawal mit dem Nutzer angelegt."""
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Joghurt")
    await _swipe_consume_all(logged_in_user, yoghurt_id)
    await logged_in_user.should_see("komplett entnommen")

    withdrawals = _withdrawals(isolated_test_database, yoghurt_id)
    assert [(w.quantity, w.withdrawn_by) for w in withdrawals] == [(4.0, 1)]
    with Session(isolated_test_database) as session:
        assert session.get(Item, yoghurt_id).is_consumed is True  # type: ignore[union-attr]


async def test_items_swipe_consume_all_can_be_cancelled(
    logged_in_user: User, isolated_test_database, yoghurt_id: int
) -> None:
    """Abbrechen im Dialog entnimmt nichts."""
    await logged_in_user.open("/items")
    logged_in_user.find(marker=f"swipe-item-{yoghurt_id}").trigger("swipeaction", SWIPE_ALLES)
    await logged_in_user.should_see("Alles entnehmen?")
    logged_in_user.find(marker="consume-all-cancel").click()

    assert _withdrawals(isolated_test_database, yoghurt_id) == []
    with Session(isolated_test_database) as session:
        assert session.get(Item, yoghurt_id).is_consumed is False  # type: ignore[union-attr]


async def test_dashboard_swipe_consume_all_records_withdrawal(
    logged_in_user: User, isolated_test_database, yoghurt_id: int
) -> None:
    """Derselbe Pfad vom Dashboard aus."""
    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Joghurt")
    await _swipe_consume_all(logged_in_user, yoghurt_id)

    assert [w.withdrawn_by for w in _withdrawals(isolated_test_database, yoghurt_id)] == [1]


async def test_swipe_consume_all_on_deleted_item_shows_message(
    logged_in_user: User, isolated_test_database, yoghurt_id: int
) -> None:
    """Wurde der Artikel inzwischen gelöscht, gibt es eine Meldung statt eines Tracebacks."""
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Joghurt")
    with Session(isolated_test_database) as session:
        item_service.delete_item(session, yoghurt_id)

    await _swipe_consume_all(logged_in_user, yoghurt_id)
    await logged_in_user.should_see("nicht mehr vorhanden")
