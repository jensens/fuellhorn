"""Entnahmen sind atomar: kein Lost Update, kein zweites 'Alles entnehmen' (Issue #394).

Vorher war withdraw_partial Read-Modify-Write ohne Bedingung: zwei Nutzer sehen 5 Stück,
beide entnehmen 3, Endbestand 2, eine Entnahme still verloren. mark_item_consumed
schrieb auf bereits verbrauchten Artikeln eine Entnahme über 0 und meldete Erfolg.
"""

from app.models import Category
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import User
from app.models import Withdrawal
from app.services import item_service
from app.services.errors import AlreadyConsumedError
from app.services.errors import StaleStockError
from datetime import date
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="five_pieces")
def five_pieces_fixture(session: Session, test_admin: User) -> int:
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    dairy = Category(name="Milchprodukte", created_by=test_admin.id)
    session.add_all([fridge, dairy])
    session.commit()
    session.refresh(fridge)
    session.refresh(dairy)
    assert fridge.id is not None
    item = item_service.create_item(
        session,
        product_name="Joghurt",
        best_before_date=date(2027, 1, 1),
        quantity=5,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=fridge.id,
        created_by=test_admin.id,
        category_id=dairy.id,
    )
    assert item.id is not None
    return item.id


def _withdrawals(session: Session, item_id: int) -> list[Withdrawal]:
    return list(session.exec(select(Withdrawal).where(Withdrawal.item_id == item_id)).all())


class TestWithdrawPartialIsAtomic:
    def test_second_user_with_stale_stock_is_rejected(
        self, session: Session, test_admin: User, five_pieces: int
    ) -> None:
        """Akzeptanzkriterium: zwei Sessions, zweite Entnahme über Restbestand → Fehler, Bestand korrekt, ein Withdrawal."""
        assert test_admin.id is not None
        other = Session(session.get_bind())
        try:
            # Beide Nutzer haben das Sheet bei Bestand 5 geöffnet
            item_service.withdraw_partial(session, five_pieces, 3, test_admin.id, expected_quantity=5)

            with pytest.raises(StaleStockError, match="Bestand hat sich geändert"):
                item_service.withdraw_partial(other, five_pieces, 3, test_admin.id, expected_quantity=5)
        finally:
            other.close()

        session.expire_all()
        item = item_service.get_item(session, five_pieces)
        assert item.quantity == 2
        assert [w.quantity for w in _withdrawals(session, five_pieces)] == [3]

    def test_concurrent_change_between_read_and_write_is_detected(
        self, session: Session, test_admin: User, five_pieces: int, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auch ohne expected_quantity: ändert jemand den Bestand zwischen Lesen und Schreiben, greift die Bedingung."""
        assert test_admin.id is not None
        other = Session(session.get_bind())
        original_get_item = item_service.get_item

        def _read_then_someone_else_withdraws(sess: Session, item_id: int) -> Item:
            item = original_get_item(sess, item_id)
            if sess is session:
                item_service.withdraw_partial(other, item_id, 4, test_admin.id)
            return item

        monkeypatch.setattr(item_service, "get_item", _read_then_someone_else_withdraws)
        try:
            with pytest.raises(StaleStockError):
                item_service.withdraw_partial(session, five_pieces, 3, test_admin.id)
        finally:
            monkeypatch.undo()
            other.close()

        session.expire_all()
        assert item_service.get_item(session, five_pieces).quantity == 1
        assert [w.quantity for w in _withdrawals(session, five_pieces)] == [4]

    def test_normal_withdrawal_still_works(self, session: Session, test_admin: User, five_pieces: int) -> None:
        assert test_admin.id is not None
        item = item_service.withdraw_partial(session, five_pieces, 2.5, test_admin.id, expected_quantity=5)

        assert item.quantity == 2.5
        assert item.is_consumed is False
        assert [w.quantity for w in _withdrawals(session, five_pieces)] == [2.5]

    def test_stale_error_is_a_value_error_for_the_ui(self) -> None:
        assert issubclass(StaleStockError, ValueError)
        assert issubclass(AlreadyConsumedError, ValueError)


class TestMarkConsumedGuard:
    def test_second_consume_all_is_rejected_without_withdrawal(
        self, session: Session, test_admin: User, five_pieces: int
    ) -> None:
        """Akzeptanzkriterium: mark_item_consumed auf verbrauchtem Artikel → Fehler, kein Withdrawal."""
        assert test_admin.id is not None
        item_service.mark_item_consumed(session, five_pieces, test_admin.id)

        with pytest.raises(AlreadyConsumedError, match="bereits vollständig entnommen"):
            item_service.mark_item_consumed(session, five_pieces, test_admin.id)

        assert [w.quantity for w in _withdrawals(session, five_pieces)] == [5]

    def test_consume_all_with_stale_stock_is_rejected(
        self, session: Session, test_admin: User, five_pieces: int
    ) -> None:
        """'Alles entnehmen' bucht den Bestand, den der Nutzer gesehen hat; hat er sich geändert, kommt ein Fehler."""
        assert test_admin.id is not None
        other = Session(session.get_bind())
        try:
            item_service.withdraw_partial(other, five_pieces, 1, test_admin.id)
            with pytest.raises(StaleStockError):
                item_service.mark_item_consumed(session, five_pieces, test_admin.id, expected_quantity=5)
        finally:
            other.close()

        session.expire_all()
        assert item_service.get_item(session, five_pieces).quantity == 4
        assert [w.quantity for w in _withdrawals(session, five_pieces)] == [1]
