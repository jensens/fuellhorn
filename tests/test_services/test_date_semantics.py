"""Datums-Semantik für PURCHASED_THEN_FROZEN (Issue #387).

Entscheidung (Variante b): Für "frisch gekauft → eingefroren" ist das Einfrierdatum
das einzige erfasste Datum; ``best_before_date`` spiegelt es (statt still den
Erfassungstag zu speichern). Der Service erzwingt das für create und update.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import item_service
from app.ui.validation import validate_freeze_date
from datetime import date
import pytest
from sqlmodel import Session


@pytest.fixture(name="freezer_world")
def freezer_world_fixture(session: Session, test_admin: User) -> dict:
    assert test_admin.id is not None
    freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    category = Category(name="Fleisch", created_by=test_admin.id)
    session.add_all([freezer, category])
    session.commit()
    session.refresh(freezer)
    session.refresh(category)
    assert category.id is not None
    session.add(CategoryShelfLife(category_id=category.id, storage_type=StorageType.FROZEN, months_min=3, months_max=6))
    session.commit()
    return {"admin": test_admin.id, "freezer": freezer.id, "category": category.id}


def _create_then_frozen(session: Session, world: dict, *, best_before: date, freeze: date):
    return item_service.create_item(
        session=session,
        product_name="Hackfleisch",
        best_before_date=best_before,
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_THEN_FROZEN,
        location_id=world["freezer"],
        created_by=world["admin"],
        category_id=world["category"],
        freeze_date=freeze,
    )


class TestPurchasedThenFrozenMirrorsFreezeDate:
    def test_create_sets_best_before_to_freeze_date(self, session: Session, freezer_world: dict) -> None:
        item = _create_then_frozen(session, freezer_world, best_before=date(2026, 10, 4), freeze=date(2026, 9, 30))

        assert item.freeze_date == date(2026, 9, 30)
        assert item.best_before_date == date(2026, 9, 30)

    def test_update_of_freeze_date_moves_best_before_along(self, session: Session, freezer_world: dict) -> None:
        item = _create_then_frozen(session, freezer_world, best_before=date(2026, 10, 4), freeze=date(2026, 9, 30))
        assert item.id is not None

        updated = item_service.update_item(session, item.id, freeze_date=date(2026, 10, 1))

        assert updated.best_before_date == date(2026, 10, 1)

    def test_type_change_to_purchased_then_frozen_mirrors_existing_freeze_date(
        self, session: Session, freezer_world: dict
    ) -> None:
        item = item_service.create_item(
            session=session,
            product_name="Suppe",
            best_before_date=date(2026, 9, 1),
            quantity=1,
            unit="l",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=freezer_world["freezer"],
            created_by=freezer_world["admin"],
            category_id=freezer_world["category"],
            freeze_date=date(2026, 9, 2),
        )
        assert item.id is not None

        updated = item_service.update_item(session, item.id, item_type=ItemType.PURCHASED_THEN_FROZEN)

        assert updated.best_before_date == date(2026, 9, 2)

    def test_other_types_keep_their_own_best_before_date(self, session: Session, freezer_world: dict) -> None:
        item = item_service.create_item(
            session=session,
            product_name="Suppe",
            best_before_date=date(2026, 9, 1),
            quantity=1,
            unit="l",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=freezer_world["freezer"],
            created_by=freezer_world["admin"],
            category_id=freezer_world["category"],
            freeze_date=date(2026, 9, 2),
        )
        assert item.best_before_date == date(2026, 9, 1)


class TestValidateFreezeDatePerType:
    """Vergangenes Einfrierdatum: nur bei HOMEMADE_FROZEN zählt die Reihenfolge zum Produktionsdatum."""

    ENTRY_DAY = date(2026, 10, 4)
    YESTERDAY = date(2026, 10, 3)

    @pytest.mark.parametrize(
        "item_type",
        [
            ItemType.PURCHASED_FRESH,
            ItemType.PURCHASED_FROZEN,
            ItemType.PURCHASED_THEN_FROZEN,
            ItemType.HOMEMADE_PRESERVED,
        ],
    )
    def test_past_freeze_date_is_valid(self, item_type: ItemType) -> None:
        assert validate_freeze_date(self.YESTERDAY, item_type, self.ENTRY_DAY) is None

    def test_homemade_frozen_rejects_freeze_before_production(self) -> None:
        error = validate_freeze_date(self.YESTERDAY, ItemType.HOMEMADE_FROZEN, self.ENTRY_DAY)
        assert error is not None and "Produktionsdatum" in error

    def test_homemade_frozen_accepts_freeze_on_production_day(self) -> None:
        assert validate_freeze_date(self.ENTRY_DAY, ItemType.HOMEMADE_FROZEN, self.ENTRY_DAY) is None
