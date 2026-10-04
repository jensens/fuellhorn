"""update_item unterscheidet 'nicht übergeben' von 'auf None setzen' (Issue #386).

Vorher: ``if x is not None`` → Notiz, Einfrierdatum und Kategorie ließen sich
nie leeren; die Edit-View meldete trotzdem "gespeichert".
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import item_service
from app.services.errors import ServiceValidationError
from app.services.item_service import UNSET
from datetime import date
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(session: Session, test_admin: User) -> dict:
    assert test_admin.id is not None
    freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    frozen_cat = Category(name="Fertiggerichte", created_by=test_admin.id)
    bare_cat = Category(name="Milchprodukte", created_by=test_admin.id)
    session.add_all([freezer, fridge, frozen_cat, bare_cat])
    session.commit()
    for obj in (freezer, fridge, frozen_cat, bare_cat):
        session.refresh(obj)
    assert frozen_cat.id is not None
    session.add(
        CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=2, months_max=6)
    )
    session.commit()
    return {
        "admin": test_admin.id,
        "freezer": freezer.id,
        "fridge": fridge.id,
        "frozen_cat": frozen_cat.id,
        "bare_cat": bare_cat.id,
    }


def _milk(session: Session, world: dict, **overrides):
    values = dict(
        session=session,
        product_name="Milch",
        best_before_date=date(2027, 1, 15),
        quantity=1.0,
        unit="l",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=world["fridge"],
        created_by=world["admin"],
        category_id=world["bare_cat"],
        notes="alte Notiz",
    )
    values.update(overrides)
    return item_service.create_item(**values)


def test_unset_is_the_default_for_nullable_fields(session: Session, world: dict) -> None:
    item = _milk(session, world)
    assert item.id is not None

    updated = item_service.update_item(session, item.id, quantity=2)

    assert updated.notes == "alte Notiz"
    assert updated.category_id == world["bare_cat"]
    assert updated.quantity == 2


def test_notes_none_clears_notes(session: Session, world: dict) -> None:
    item = _milk(session, world)
    assert item.id is not None

    updated = item_service.update_item(session, item.id, notes=None)

    assert updated.notes is None


def test_explicit_unset_keeps_notes(session: Session, world: dict) -> None:
    item = _milk(session, world)
    assert item.id is not None

    updated = item_service.update_item(session, item.id, notes=UNSET)

    assert updated.notes == "alte Notiz"


def test_freeze_date_none_clears_freeze_date_when_type_no_longer_needs_it(session: Session, world: dict) -> None:
    pizza = _milk(
        session,
        world,
        product_name="Pizza",
        item_type=ItemType.PURCHASED_THEN_FROZEN,
        location_id=world["freezer"],
        category_id=world["frozen_cat"],
        freeze_date=date(2026, 9, 1),
    )
    assert pizza.id is not None

    updated = item_service.update_item(session, pizza.id, item_type=ItemType.PURCHASED_FROZEN, freeze_date=None)

    assert updated.item_type == ItemType.PURCHASED_FROZEN
    assert updated.freeze_date is None


def test_freeze_date_none_rejected_while_type_requires_it(session: Session, world: dict) -> None:
    pizza = _milk(
        session,
        world,
        product_name="Pizza",
        item_type=ItemType.PURCHASED_THEN_FROZEN,
        location_id=world["freezer"],
        category_id=world["frozen_cat"],
        freeze_date=date(2026, 9, 1),
    )
    assert pizza.id is not None

    with pytest.raises(ServiceValidationError, match="Einfrierdatum"):
        item_service.update_item(session, pizza.id, freeze_date=None)


def test_category_none_allowed_for_mhd_item(session: Session, world: dict) -> None:
    item = _milk(session, world)
    assert item.id is not None

    updated = item_service.update_item(session, item.id, category_id=None)

    assert updated.category_id is None
