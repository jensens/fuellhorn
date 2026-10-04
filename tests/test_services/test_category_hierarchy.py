"""Kategorie-Hierarchie im Service: Guards, Haltbarkeits-Fallback, Filter-Expansion (Issue #395).

Vorher ließ sich ``parent_id`` nur per Seed/Migration setzen, Haltbarkeiten auf
Eltern waren tote Konfiguration (Kinder ohne eigenen Eintrag verschwanden aus dem
Wizard) und der Vorratsfilter mit einer Eltern-Kategorie fand nie etwas.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import category_service
from app.services import expiry_service
from app.services import item_service
from app.services import shelf_life_service
from app.services.errors import ServiceValidationError
from datetime import date
import pytest
from sqlmodel import Session


def _category(session: Session, name: str, admin_id: int, parent_id: int | None = None) -> Category:
    category = Category(name=name, created_by=admin_id, parent_id=parent_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _shelf_life(session: Session, category_id: int, storage_type: StorageType, months: tuple[int, int]) -> None:
    session.add(
        CategoryShelfLife(
            category_id=category_id, storage_type=storage_type, months_min=months[0], months_max=months[1]
        )
    )
    session.commit()


class TestParentGuards:
    def test_create_with_parent_sets_parent(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)

        beef = category_service.create_category(session, "Rindfleisch", test_admin.id, parent_id=meat.id)

        assert beef.parent_id == meat.id

    def test_update_assigns_and_clears_parent(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)
        beef = _category(session, "Rindfleisch", test_admin.id)
        assert beef.id is not None

        assert category_service.update_category(session, beef.id, parent_id=meat.id).parent_id == meat.id
        assert category_service.update_category(session, beef.id, name="Rind").parent_id == meat.id, (
            "UNSET lässt Parent"
        )
        assert category_service.update_category(session, beef.id, parent_id=None).parent_id is None

    def test_category_cannot_be_its_own_parent(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)
        assert meat.id is not None

        with pytest.raises(ServiceValidationError, match="selbst"):
            category_service.update_category(session, meat.id, parent_id=meat.id)

    def test_parent_must_be_top_level(self, session: Session, test_admin: User) -> None:
        """Nur eine Ebene: eine Kategorie mit Parent kann selbst kein Parent sein."""
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)
        beef = _category(session, "Rindfleisch", test_admin.id, parent_id=meat.id)
        steak = _category(session, "Steak", test_admin.id)
        assert steak.id is not None

        with pytest.raises(ServiceValidationError, match="eine Ebene"):
            category_service.update_category(session, steak.id, parent_id=beef.id)

    def test_category_with_children_cannot_get_a_parent(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        food = _category(session, "Lebensmittel", test_admin.id)
        meat = _category(session, "Fleisch", test_admin.id)
        _category(session, "Rindfleisch", test_admin.id, parent_id=meat.id)
        assert meat.id is not None

        with pytest.raises(ServiceValidationError, match="Unterkategorien"):
            category_service.update_category(session, meat.id, parent_id=food.id)

    def test_category_with_items_cannot_become_a_group(self, session: Session, test_admin: User) -> None:
        """Gruppen sind nicht wählbar; eine Kategorie mit Artikeln darf deshalb kein Parent werden."""
        assert test_admin.id is not None
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
        session.add(fridge)
        session.commit()
        session.refresh(fridge)
        assert fridge.id is not None
        dairy = _category(session, "Milchprodukte", test_admin.id)
        yoghurt = _category(session, "Joghurt", test_admin.id)
        assert dairy.id is not None and yoghurt.id is not None
        item_service.create_item(
            session,
            product_name="Milch",
            best_before_date=date(2027, 1, 1),
            quantity=1,
            unit="l",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,
            created_by=test_admin.id,
            category_id=dairy.id,
        )

        with pytest.raises(ServiceValidationError, match="Artikel"):
            category_service.update_category(session, yoghurt.id, parent_id=dairy.id)

    def test_unknown_parent_is_rejected(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        with pytest.raises(ValueError, match="not found"):
            category_service.create_category(session, "Rind", test_admin.id, parent_id=9999)


class TestShelfLifeFallback:
    @pytest.fixture(name="meat_group")
    def meat_group_fixture(self, session: Session, test_admin: User) -> dict[str, int]:
        """Fleisch (FROZEN 3–12) mit Rindfleisch (eigene FROZEN 9–12) und Wurst (ohne eigenen Eintrag)."""
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)
        beef = _category(session, "Rindfleisch", test_admin.id, parent_id=meat.id)
        sausage = _category(session, "Wurst", test_admin.id, parent_id=meat.id)
        assert meat.id is not None and beef.id is not None and sausage.id is not None
        _shelf_life(session, meat.id, StorageType.FROZEN, (3, 12))
        _shelf_life(session, beef.id, StorageType.FROZEN, (9, 12))
        return {"admin": test_admin.id, "meat": meat.id, "beef": beef.id, "sausage": sausage.id}

    def test_child_without_own_entry_inherits_parent_shelf_life(self, session: Session, meat_group: dict) -> None:
        inherited = shelf_life_service.get_shelf_life_with_fallback(session, meat_group["sausage"], StorageType.FROZEN)
        own = shelf_life_service.get_shelf_life_with_fallback(session, meat_group["beef"], StorageType.FROZEN)

        assert inherited is not None and (inherited.months_min, inherited.months_max) == (3, 12)
        assert own is not None and (own.months_min, own.months_max) == (9, 12)
        assert (
            shelf_life_service.get_shelf_life_with_fallback(session, meat_group["sausage"], StorageType.AMBIENT) is None
        )

    def test_wizard_offers_child_that_inherits_shelf_life(self, session: Session, meat_group: dict) -> None:
        """Vorher verschwand 'Wurst' kommentarlos aus dem Wizard."""
        names = {c.name for c in category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN)}

        assert names == {"Rindfleisch", "Wurst"}

    def test_expiry_uses_inherited_shelf_life(self, session: Session, meat_group: dict) -> None:
        freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=meat_group["admin"])
        session.add(freezer)
        session.commit()
        session.refresh(freezer)
        assert freezer.id is not None
        item = item_service.create_item(
            session,
            product_name="Bratwurst",
            best_before_date=date(2026, 9, 1),
            quantity=4,
            unit="Stück",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=freezer.id,
            created_by=meat_group["admin"],
            category_id=meat_group["sausage"],
            freeze_date=date(2026, 9, 1),
        )
        assert item.id is not None

        single = expiry_service.get_item_expiry_view(session, item, today=date(2026, 10, 4))
        bulk = expiry_service.get_expiry_views(session, [item], today=date(2026, 10, 4))[item.id]
        optimal, maximum, mhd = item_service.get_item_expiry_info(session, item.id)

        assert single.status == "ok" and single == bulk
        assert (optimal, maximum, mhd) == (date(2026, 12, 1), date(2027, 9, 1), None)


class TestExpandCategoryFilter:
    def test_parent_expands_to_children_and_itself(self, session: Session, test_admin: User) -> None:
        assert test_admin.id is not None
        meat = _category(session, "Fleisch", test_admin.id)
        beef = _category(session, "Rindfleisch", test_admin.id, parent_id=meat.id)
        pork = _category(session, "Schwein", test_admin.id, parent_id=meat.id)
        veg = _category(session, "Gemüse", test_admin.id)
        assert meat.id and beef.id and pork.id and veg.id

        assert category_service.expand_category_filter(session, {meat.id}) == {meat.id, beef.id, pork.id}
        assert category_service.expand_category_filter(session, {veg.id, beef.id}) == {veg.id, beef.id}
        assert category_service.expand_category_filter(session, set()) == set()
