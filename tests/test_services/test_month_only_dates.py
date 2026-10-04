"""Monatsgenaue Daten: Frist bis Monatsende, Rechenbasis am Monatsersten (Issues #346, #347).

Gespeichert wird immer der 1. des Monats plus ein Kennzeichen. Ein MHD „03/2026“ läuft am
31.03. ab, ein Herstellungs- oder Einfrierdatum „03/2026“ rechnet dagegen ab dem 1. März:
Die Haltbarkeit endet damit früher und die Warnung liegt auf der sicheren Seite.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import expiry_calculator
from app.services import expiry_service
from app.services import item_service
from datetime import date
import pytest
from sqlmodel import Session


class TestMonthHelpers:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (date(2026, 3, 1), date(2026, 3, 31)),
            (date(2026, 4, 1), date(2026, 4, 30)),
            (date(2026, 2, 1), date(2026, 2, 28)),
            (date(2028, 2, 1), date(2028, 2, 29)),
            (date(2026, 12, 1), date(2026, 12, 31)),
        ],
    )
    def test_end_of_month(self, value: date, expected: date) -> None:
        assert expiry_calculator.end_of_month(value) == expected

    def test_effective_deadline_shifts_only_month_only_dates(self) -> None:
        assert expiry_calculator.effective_deadline(date(2026, 3, 1), month_only=True) == date(2026, 3, 31)
        assert expiry_calculator.effective_deadline(date(2026, 3, 1), month_only=False) == date(2026, 3, 1)


def test_dates_are_day_precise_by_default() -> None:
    assert Item.model_fields["best_before_month_only"].default is False
    assert Item.model_fields["freeze_date_month_only"].default is False


@pytest.fixture(name="world")
def world_fixture(session: Session, test_admin: User) -> dict[str, int]:
    """Kühlschrank, Truhe und Speis; eine AMBIENT- und eine FROZEN-Kategorie mit 6 bis 12 Monaten."""
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    pantry = Location(name="Speis", location_type=LocationType.AMBIENT, created_by=test_admin.id)
    dairy = Category(name="Milchprodukte", created_by=test_admin.id)
    jam = Category(name="Fruchtaufstriche", created_by=test_admin.id)
    vegetables = Category(name="Gemüse", created_by=test_admin.id)
    session.add_all([fridge, freezer, pantry, dairy, jam, vegetables])
    session.commit()
    for obj in (fridge, freezer, pantry, dairy, jam, vegetables):
        session.refresh(obj)
    assert jam.id is not None and vegetables.id is not None
    session.add_all(
        [
            CategoryShelfLife(category_id=jam.id, storage_type=StorageType.AMBIENT, months_min=6, months_max=12),
            CategoryShelfLife(category_id=vegetables.id, storage_type=StorageType.FROZEN, months_min=6, months_max=12),
        ]
    )
    session.commit()
    return {
        "admin": test_admin.id,
        "fridge": fridge.id,  # type: ignore[dict-item]
        "freezer": freezer.id,  # type: ignore[dict-item]
        "pantry": pantry.id,  # type: ignore[dict-item]
        "dairy": dairy.id,  # type: ignore[dict-item]
        "jam": jam.id,
        "vegetables": vegetables.id,
    }


class TestDeadlineIsEndOfMonth:
    def test_month_only_mhd_lasts_until_the_end_of_the_month(self, session: Session, world: dict[str, int]) -> None:
        """Akzeptanzkriterium: „03/2026“ ist am 20.03. noch in Ordnung, tagesgenau wäre es abgelaufen."""
        month = item_service.create_item(
            session,
            product_name="Milch (03/2026)",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="l",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=world["admin"],
            category_id=world["dairy"],
        )
        day = item_service.create_item(
            session,
            product_name="Milch (01.03.2026)",
            best_before_date=date(2026, 3, 1),
            quantity=1,
            unit="l",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=world["admin"],
            category_id=world["dairy"],
        )

        month_view = expiry_service.get_item_expiry_view(session, month, today=date(2026, 3, 20))
        day_view = expiry_service.get_item_expiry_view(session, day, today=date(2026, 3, 20))

        assert (month_view.display_date, month_view.status) == (date(2026, 3, 31), "ok")
        assert (day_view.display_date, day_view.status) == (date(2026, 3, 1), "critical")

    def test_expiry_info_reports_the_end_of_the_month_as_mhd(self, session: Session, world: dict[str, int]) -> None:
        item = item_service.create_item(
            session,
            product_name="Erbsen",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="Packung",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
            category_id=world["vegetables"],
        )
        assert item.id is not None

        assert item_service.get_item_expiry_info(session, item.id) == (None, None, date(2026, 3, 31))

    def test_bulk_and_single_path_agree(self, session: Session, world: dict[str, int]) -> None:
        item = item_service.create_item(
            session,
            product_name="Joghurt",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=world["admin"],
            category_id=world["dairy"],
        )
        assert item.id is not None

        single = expiry_service.get_item_expiry_view(session, item, today=date(2026, 3, 20))
        bulk = expiry_service.get_expiry_views(session, [item], today=date(2026, 3, 20))[item.id]

        assert single == bulk


class TestBaseStaysOnTheFirst:
    def test_month_only_production_date_counts_from_the_first(self, session: Session, world: dict[str, int]) -> None:
        """Eingemacht „03/2026“ mit 6 bis 12 Monaten: ideal ab 01.09.2026, nicht erst ab 30.09."""
        item = item_service.create_item(
            session,
            product_name="Marmelade",
            best_before_date=date(2026, 3, 1),
            best_before_month_only=True,
            quantity=1,
            unit="Stück",
            item_type=ItemType.HOMEMADE_PRESERVED,
            location_id=world["pantry"],
            created_by=world["admin"],
            category_id=world["jam"],
        )
        assert item.id is not None

        assert item_service.get_item_expiry_info(session, item.id) == (date(2026, 9, 1), date(2027, 3, 1), None)

    def test_month_only_freeze_date_counts_from_the_first(self, session: Session, world: dict[str, int]) -> None:
        item = item_service.create_item(
            session,
            product_name="Bohnen",
            best_before_date=date(2026, 2, 1),
            quantity=1,
            unit="Beutel",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
            category_id=world["vegetables"],
            freeze_date=date(2026, 3, 1),
            freeze_date_month_only=True,
        )
        assert item.id is not None

        assert item_service.get_item_expiry_info(session, item.id) == (date(2026, 9, 1), date(2027, 3, 1), None)


class TestMirroringAndUpdates:
    def test_then_frozen_mirrors_date_and_precision(self, session: Session, world: dict[str, int]) -> None:
        """Bei „Frisch gekauft, dann eingefroren“ spiegelt best_before_date das Einfrierdatum (#387)."""
        item = item_service.create_item(
            session,
            product_name="Brot",
            best_before_date=date(2026, 1, 15),
            quantity=1,
            unit="Stück",
            item_type=ItemType.PURCHASED_THEN_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
            category_id=world["vegetables"],
            freeze_date=date(2026, 3, 1),
            freeze_date_month_only=True,
        )

        assert item.best_before_date == date(2026, 3, 1)
        assert item.best_before_month_only is True

    def test_update_changes_precision_in_both_directions(self, session: Session, world: dict[str, int]) -> None:
        item = item_service.create_item(
            session,
            product_name="Senf",
            best_before_date=date(2026, 3, 15),
            quantity=1,
            unit="Glas",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=world["fridge"],
            created_by=world["admin"],
            category_id=world["dairy"],
        )
        assert item.id is not None

        to_month = item_service.update_item(
            session, item.id, best_before_date=date(2026, 5, 1), best_before_month_only=True
        )
        assert (to_month.best_before_date, to_month.best_before_month_only) == (date(2026, 5, 1), True)

        unchanged = item_service.update_item(session, item.id, product_name="Senf scharf")
        assert unchanged.best_before_month_only is True, "ohne Angabe bleibt die Genauigkeit stehen"

        back_to_day = item_service.update_item(
            session, item.id, best_before_date=date(2026, 5, 17), best_before_month_only=False
        )
        assert (back_to_day.best_before_date, back_to_day.best_before_month_only) == (date(2026, 5, 17), False)
