"""Tests: Entnahmen mit Dezimalmengen (Issue #365).

Mengen sind Floats. Ohne Rundung erreicht der Restbestand nie exakt 0 und die
letzte Entnahme wird wegen Binärbruch-Resten verweigert
(1,0 − 0,3 − 0,3 = 0,39999999999999997 < 0,4).
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


@pytest.fixture(name="make_item")
def make_item_fixture(session: Session, test_admin: User):
    """Factory für einen aktiven Artikel mit gegebener Menge."""
    assert test_admin.id is not None
    location = location_service.create_location(session, "Kühlschrank", LocationType.CHILLED, test_admin.id)
    assert location.id is not None

    def _make(quantity: float, unit: str = "l") -> Item:
        return item_service.create_item(
            session,
            product_name="Testartikel",
            best_before_date=date.today() + timedelta(days=30),
            quantity=quantity,
            unit=unit,
            item_type=ItemType.PURCHASED_FRESH,
            location_id=location.id,  # type: ignore[arg-type]
            created_by=test_admin.id,  # type: ignore[arg-type]
        )

    return _make


ADMIN_ID = 1  # test_admin ist der erste User der Test-DB


def _withdraw_all(session: Session, item: Item, *amounts: float) -> Item:
    assert item.id is not None
    for amount in amounts:
        item = item_service.withdraw_partial(session, item.id, amount, ADMIN_ID)
    return item


def test_withdrawals_summing_to_total_consume_item(session: Session, make_item) -> None:
    """1,0 l → 0,3 + 0,3 + 0,4: letzte Entnahme wird akzeptiert, Artikel ist verbraucht."""
    item = _withdraw_all(session, make_item(1.0), 0.3, 0.3, 0.4)
    assert (item.quantity, item.is_consumed) == (0, True)


def test_three_tenths_consume_item(session: Session, make_item) -> None:
    """0,3 → 3 × 0,1 endet bei 0 und verbraucht."""
    item = _withdraw_all(session, make_item(0.3), 0.1, 0.1, 0.1)
    assert (item.quantity, item.is_consumed) == (0, True)


def test_half_of_two_and_a_half_leaves_two(session: Session, make_item) -> None:
    """2,5 kg − 0,5 kg = 2,0 kg (nicht 1,5 durch Aufrunden auf 1)."""
    item = _withdraw_all(session, make_item(2.5, "kg"), 0.5)
    assert (item.quantity, item.is_consumed) == (2.0, False)


def test_remaining_quantity_is_rounded_to_three_decimals(session: Session, make_item) -> None:
    """Restmengen werden auf 3 Nachkommastellen gerundet gespeichert."""
    item = _withdraw_all(session, make_item(1.0), 0.333333)
    assert item.quantity == 0.667


def test_withdrawal_that_rounds_to_zero_is_rejected(session: Session, make_item) -> None:
    """Eine Menge unter der Auflösung (0,0004) ist keine Entnahme."""
    item = make_item(1.0)
    assert item.id is not None
    with pytest.raises(ValueError, match="positive"):
        item_service.withdraw_partial(session, item.id, 0.0004, ADMIN_ID)


def test_withdrawal_slightly_above_remaining_due_to_float_noise_is_allowed(session: Session, make_item) -> None:
    """Nach 0,7 Entnahme von 1,0 darf der Rest (0,3) entnommen werden, obwohl 1.0-0.7 binär 0.30000000000000004 ist."""
    item = _withdraw_all(session, make_item(1.0), 0.7, 0.3)
    assert (item.quantity, item.is_consumed) == (0, True)
