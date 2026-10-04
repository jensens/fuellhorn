"""Tests: Entnahmen brauchen immer einen Nutzer (Issue #367).

``mark_item_consumed`` und ``withdraw_partial`` legten ohne ``user_id`` still keinen
Withdrawal an. Der Artikel verschwand dann aus der aktiven Liste UND aus "Entnommene"
(Inner-Join auf withdrawal) und war nicht mehr auffindbar.
"""

from app.models import Item
from app.models import ItemType
from app.models import LocationType
from app.models import User
from app.services import item_service
from app.services import location_service
from datetime import date
from datetime import timedelta
import pytest
from sqlmodel import Session


@pytest.fixture(name="item")
def item_fixture(session: Session, test_admin: User) -> Item:
    assert test_admin.id is not None
    location = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, test_admin.id)
    return item_service.create_item(
        session,
        product_name="Joghurt",
        best_before_date=date.today() + timedelta(days=5),
        quantity=4,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,  # type: ignore[arg-type]
        created_by=test_admin.id,
    )


def test_mark_item_consumed_requires_user(session: Session, item: Item) -> None:
    """Ohne Nutzer ist 'alles entnehmen' nicht möglich (kein stilles Überspringen des Audit-Trails)."""
    assert item.id is not None
    with pytest.raises(TypeError):
        item_service.mark_item_consumed(session, item.id)  # type: ignore[call-arg]


def test_withdraw_partial_requires_user(session: Session, item: Item) -> None:
    """Ohne Nutzer ist keine Teilentnahme möglich."""
    assert item.id is not None
    with pytest.raises(TypeError):
        item_service.withdraw_partial(session, item.id, 1)  # type: ignore[call-arg]


def test_consumed_item_is_listed_under_consumed_items(session: Session, item: Item, test_admin: User) -> None:
    """Ein komplett entnommener Artikel bleibt über 'Entnommene' auffindbar."""
    assert item.id is not None and test_admin.id is not None
    item_service.mark_item_consumed(session, item.id, test_admin.id)
    assert [i.id for i in item_service.get_consumed_items(session)] == [item.id]
