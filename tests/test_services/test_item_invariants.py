"""Service-Invarianten für create_item/update_item (Issue #385).

Vorher validierte nur das UI (``wizard_validation.py``): der Service speicherte
``quantity <= 0``, leere Namen, eingefrorene Artikel ohne Einfrierdatum,
Lagerorte mit falscher Lagerart und Kategorien ohne passende Haltbarkeit.
``Field(gt=0)`` am Modell wirkt bei ``table=True`` nicht.
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
from datetime import date
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(session: Session, test_admin: User) -> dict:
    """Lagerorte aller Lagerarten und Kategorien mit/ohne passende Haltbarkeit."""
    assert test_admin.id is not None
    freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    cellar = Location(name="Keller", location_type=LocationType.AMBIENT, created_by=test_admin.id)
    frozen_cat = Category(name="Suppen", created_by=test_admin.id)
    ambient_cat = Category(name="Marmelade", created_by=test_admin.id)
    bare_cat = Category(name="Milchprodukte (frisch)", created_by=test_admin.id)
    session.add_all([freezer, fridge, cellar, frozen_cat, ambient_cat, bare_cat])
    session.commit()
    for obj in (freezer, fridge, cellar, frozen_cat, ambient_cat, bare_cat):
        session.refresh(obj)
    assert frozen_cat.id is not None and ambient_cat.id is not None
    session.add(
        CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=2, months_max=6)
    )
    session.add(
        CategoryShelfLife(category_id=ambient_cat.id, storage_type=StorageType.AMBIENT, months_min=6, months_max=12)
    )
    session.commit()
    return {
        "admin": test_admin,
        "freezer": freezer,
        "fridge": fridge,
        "cellar": cellar,
        "frozen_cat": frozen_cat,
        "ambient_cat": ambient_cat,
        "bare_cat": bare_cat,
    }


def _create(session: Session, world: dict, **overrides):
    """Gültiger PURCHASED_FRESH-Artikel im Kühlschrank; Felder per overrides verändern."""
    values = dict(
        session=session,
        product_name="Milch",
        best_before_date=date(2027, 1, 15),
        quantity=1.0,
        unit="l",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=world["fridge"].id,
        created_by=world["admin"].id,
        category_id=world["bare_cat"].id,
    )
    values.update(overrides)
    return item_service.create_item(**values)


class TestCreateItemBasics:
    def test_valid_item_is_created_and_name_trimmed(self, session: Session, world: dict) -> None:
        item = _create(session, world, product_name="  Milch  ")
        assert item.id is not None
        assert item.product_name == "Milch"

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_blank_product_name_rejected(self, session: Session, world: dict, name) -> None:
        with pytest.raises(ServiceValidationError, match="Produktname"):
            _create(session, world, product_name=name)

    @pytest.mark.parametrize("quantity", [0, -5, -0.5])
    def test_non_positive_quantity_rejected(self, session: Session, world: dict, quantity) -> None:
        with pytest.raises(ServiceValidationError, match="Menge"):
            _create(session, world, quantity=quantity)

    def test_blank_unit_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Einheit"):
            _create(session, world, unit="  ")

    def test_nothing_is_persisted_on_error(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError):
            _create(session, world, quantity=0)
        assert item_service.get_all_items(session) == []


class TestLocationCompatibility:
    def test_fresh_item_in_freezer_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Lagerort 'Tiefkühltruhe'"):
            _create(session, world, location_id=world["freezer"].id)

    def test_frozen_item_in_fridge_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Lagerort 'Kühlschrank'"):
            _create(
                session,
                world,
                item_type=ItemType.PURCHASED_FROZEN,
                location_id=world["fridge"].id,
                category_id=world["frozen_cat"].id,
            )

    def test_unknown_location_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ValueError, match="not found"):
            _create(session, world, location_id=9999)

    def test_fresh_item_allowed_in_cellar_and_fridge(self, session: Session, world: dict) -> None:
        _create(session, world, location_id=world["cellar"].id)
        _create(session, world, location_id=world["fridge"].id)
        assert len(item_service.get_all_items(session)) == 2


class TestFreezeDate:
    @pytest.mark.parametrize("item_type", [ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN])
    def test_frozen_types_require_freeze_date(self, session: Session, world: dict, item_type: ItemType) -> None:
        with pytest.raises(ServiceValidationError, match="Einfrierdatum"):
            _create(
                session,
                world,
                item_type=item_type,
                location_id=world["freezer"].id,
                category_id=world["frozen_cat"].id,
                freeze_date=None,
            )

    def test_homemade_frozen_before_production_date_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Produktionsdatum"):
            _create(
                session,
                world,
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=world["freezer"].id,
                category_id=world["frozen_cat"].id,
                best_before_date=date(2026, 9, 2),
                freeze_date=date(2026, 9, 1),
            )

    def test_purchased_frozen_needs_no_freeze_date(self, session: Session, world: dict) -> None:
        item = _create(
            session,
            world,
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=world["freezer"].id,
            category_id=world["frozen_cat"].id,
        )
        assert item.freeze_date is None


class TestCategoryShelfLife:
    def test_frozen_item_with_category_without_frozen_shelf_life_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Kategorie 'Marmelade'"):
            _create(
                session,
                world,
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=world["freezer"].id,
                category_id=world["ambient_cat"].id,
                best_before_date=date(2026, 9, 1),
                freeze_date=date(2026, 9, 2),
            )

    def test_preserved_item_without_category_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ServiceValidationError, match="Kategorie"):
            _create(
                session,
                world,
                item_type=ItemType.HOMEMADE_PRESERVED,
                location_id=world["cellar"].id,
                category_id=None,
            )

    def test_unknown_category_rejected(self, session: Session, world: dict) -> None:
        with pytest.raises(ValueError, match="not found"):
            _create(session, world, category_id=9999)

    def test_preserved_item_with_matching_category_created(self, session: Session, world: dict) -> None:
        item = _create(
            session,
            world,
            item_type=ItemType.HOMEMADE_PRESERVED,
            location_id=world["cellar"].id,
            category_id=world["ambient_cat"].id,
        )
        assert item.category_id == world["ambient_cat"].id


class TestUpdateItem:
    def test_type_change_to_incompatible_location_rejected(self, session: Session, world: dict) -> None:
        item = _create(
            session,
            world,
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=world["freezer"].id,
            category_id=world["frozen_cat"].id,
        )
        assert item.id is not None

        with pytest.raises(ServiceValidationError, match="Lagerort 'Tiefkühltruhe'"):
            item_service.update_item(session, item.id, item_type=ItemType.PURCHASED_FRESH)

        session.refresh(item)
        assert item.item_type == ItemType.PURCHASED_FROZEN

    def test_partial_update_validates_merged_state(self, session: Session, world: dict) -> None:
        item = _create(session, world)
        assert item.id is not None

        with pytest.raises(ServiceValidationError, match="Menge"):
            item_service.update_item(session, item.id, quantity=0)
        with pytest.raises(ServiceValidationError, match="Produktname"):
            item_service.update_item(session, item.id, product_name="   ")

    def test_valid_update_trims_name_and_moves_item(self, session: Session, world: dict) -> None:
        item = _create(session, world)
        assert item.id is not None

        updated = item_service.update_item(session, item.id, product_name=" Vollmilch ", location_id=world["cellar"].id)

        assert updated.product_name == "Vollmilch"
        assert updated.location_id == world["cellar"].id
