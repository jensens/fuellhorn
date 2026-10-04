"""Tests: Lösch-Guards in den Services (Issue #379).

Vorher prüften die Services keine Referenzen: In PostgreSQL endete das Löschen
referenzierter Kategorien/Benutzer in rohen IntegrityErrors (bei Kategorien nach
Teillöschung der Haltbarkeiten), in SQLite ohne Fremdschlüssel entstanden Waisen.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.models.user import Role
from app.services import auth_service
from app.services import category_service
from app.services import location_service
from datetime import date
import pytest
from sqlmodel import Session
from sqlmodel import select


def _location(session: Session, admin: User, name: str = "Kühlschrank", active: bool = True) -> Location:
    location = Location(name=name, location_type=LocationType.CHILLED, created_by=admin.id, is_active=active)
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def _category(session: Session, admin: User, name: str = "Gemüse", parent_id: int | None = None) -> Category:
    category = Category(name=name, created_by=admin.id, parent_id=parent_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _item(session: Session, admin: User, location: Location, category: Category | None = None, **kwargs) -> Item:
    item = Item(
        product_name="Testartikel",
        best_before_date=date(2027, 1, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        category_id=category.id if category else None,
        created_by=admin.id,
        **kwargs,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


class TestDeleteCategory:
    def test_refuses_category_used_by_items(self, session: Session, test_admin: User) -> None:
        location = _location(session, test_admin)
        category = _category(session, test_admin)
        _item(session, test_admin, location, category)

        with pytest.raises(ValueError, match="1 Artikel"):
            category_service.delete_category(session, category.id)

        assert category_service.get_category(session, category.id) is not None

    def test_refuses_category_with_children(self, session: Session, test_admin: User) -> None:
        parent = _category(session, test_admin, "Fleisch")
        _category(session, test_admin, "Rindfleisch", parent_id=parent.id)

        with pytest.raises(ValueError, match="Unterkategorie"):
            category_service.delete_category(session, parent.id)

    def test_deletes_category_with_its_shelf_lives_in_one_go(self, session: Session, test_admin: User) -> None:
        category = _category(session, test_admin)
        session.add(
            CategoryShelfLife(category_id=category.id, storage_type=StorageType.FROZEN, months_min=1, months_max=2)
        )
        session.commit()

        category_service.delete_category(session, category.id)

        assert session.exec(select(Category).where(Category.id == category.id)).first() is None
        assert session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == category.id)).all() == []


class TestDeleteLocation:
    def test_refuses_location_in_use_and_points_to_deactivation(self, session: Session, test_admin: User) -> None:
        location = _location(session, test_admin)
        _item(session, test_admin, location, is_consumed=True)

        with pytest.raises(ValueError, match="in Verwendung.*1 Artikel.*eaktivier"):
            location_service.delete_location(session, location.id)

    def test_deletes_unused_location(self, session: Session, test_admin: User) -> None:
        location = _location(session, test_admin)

        location_service.delete_location(session, location.id)

        assert session.exec(select(Location).where(Location.id == location.id)).first() is None

    def test_inactive_location_is_hidden_from_item_type_selection(self, session: Session, test_admin: User) -> None:
        _location(session, test_admin, "Aktiv", active=True)
        _location(session, test_admin, "Stillgelegt", active=False)

        names = [loc.name for loc in location_service.get_locations_for_item_type(session, ItemType.PURCHASED_FRESH)]

        assert names == ["Aktiv"]

    def test_inactive_location_stays_selectable_when_item_already_lives_there(
        self, session: Session, test_admin: User
    ) -> None:
        inactive = _location(session, test_admin, "Stillgelegt", active=False)

        names = [
            loc.name
            for loc in location_service.get_locations_for_item_type(
                session, ItemType.PURCHASED_FRESH, include_location_id=inactive.id
            )
        ]

        assert names == ["Stillgelegt"]


class TestDeleteUser:
    def test_refuses_user_with_references(self, session: Session, test_admin: User) -> None:
        user = auth_service.create_user(
            session, username="erfasser", email="erfasser@example.com", password="geheim-123", role=Role.USER
        )
        location = _location(session, test_admin)
        _item(session, user, location)

        with pytest.raises(ValueError, match="erfasser.*1 Artikel.*eaktivier"):
            auth_service.delete_user(session, user.id)

        assert auth_service.get_user(session, user.id) is not None

    def test_deletes_user_without_references(self, session: Session) -> None:
        user = auth_service.create_user(
            session, username="neuling", email="neuling@example.com", password="geheim-123", role=Role.USER
        )

        auth_service.delete_user(session, user.id)

        assert session.exec(select(User).where(User.id == user.id)).first() is None
