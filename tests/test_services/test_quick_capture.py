"""Schnellerfassung und Liste der unvollständigen Artikel (Issue #463).

Unten im Keller zählt nur Ort, Name, Menge, Einheit und Typ. Unvollständig ist ein Artikel,
solange etwas fehlt, das der Wizard verlangt hätte: Datum, Kategorie, Einfrierdatum beim
eingefrorenen Typ und - wo die Haltbarkeit berechnet wird - eine Kategorie mit Haltbarkeit
für diese Lagerart (dieselbe Regel wie im Dienst, Issue #385).
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import expiry_service
from app.services import item_service
from app.services import item_types
from app.services.errors import ServiceValidationError
from datetime import date
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(session: Session, test_admin: User) -> dict[str, int]:
    """Kühlschrank und Truhe; eine Kategorie mit FROZEN-Haltbarkeit und eine ohne."""
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    frozen_cat = Category(name="Gemüse", created_by=test_admin.id)
    bare_cat = Category(name="Sonstiges", created_by=test_admin.id)
    session.add_all([fridge, freezer, frozen_cat, bare_cat])
    session.commit()
    for obj in (fridge, freezer, frozen_cat, bare_cat):
        session.refresh(obj)
    assert frozen_cat.id is not None and fridge.id is not None and freezer.id is not None and bare_cat.id is not None
    session.add(
        CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=6, months_max=12)
    )
    session.commit()
    return {
        "admin": test_admin.id,
        "fridge": fridge.id,
        "freezer": freezer.id,
        "frozen_cat": frozen_cat.id,
        "bare_cat": bare_cat.id,
    }


class TestQuickCreateItem:
    def test_stores_only_the_basics(self, session: Session, world: dict[str, int]) -> None:
        item = item_service.quick_create_item(
            session,
            product_name="  Erbsen aus Garten ",
            quantity=3,
            unit="Beutel",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
        )

        assert item.product_name == "Erbsen aus Garten", "der Name wird getrimmt"
        assert (item.quantity, item.unit) == (3, "Beutel")
        assert item.location_id == world["freezer"]
        assert item.best_before_date is None and item.freeze_date is None and item.category_id is None
        assert item.is_consumed is False

    def test_rejects_a_location_that_does_not_fit_the_type(self, session: Session, world: dict[str, int]) -> None:
        with pytest.raises(ServiceValidationError, match="passt nicht"):
            item_service.quick_create_item(
                session,
                product_name="Erbsen",
                quantity=1,
                unit="Beutel",
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=world["fridge"],
                created_by=world["admin"],
            )

    @pytest.mark.parametrize(("name", "quantity"), [("", 1), ("Erbsen", 0)])
    def test_rejects_empty_name_and_zero_quantity(
        self, session: Session, world: dict[str, int], name: str, quantity: float
    ) -> None:
        with pytest.raises(ServiceValidationError):
            item_service.quick_create_item(
                session,
                product_name=name,
                quantity=quantity,
                unit="Beutel",
                item_type=ItemType.PURCHASED_FRESH,
                location_id=world["fridge"],
                created_by=world["admin"],
            )


class TestItemsNeedingCompletion:
    def _quick(self, session: Session, world: dict[str, int], name: str, **overrides: object) -> int:
        arguments: dict[str, object] = {
            "product_name": name,
            "quantity": 1,
            "unit": "Stück",
            "item_type": ItemType.PURCHASED_FRESH,
            "location_id": world["fridge"],
            "created_by": world["admin"],
        }
        arguments.update(overrides)
        item = item_service.quick_create_item(session, **arguments)  # type: ignore[arg-type]
        assert item.id is not None
        return item.id

    def test_quick_captured_item_misses_date_and_category(self, session: Session, world: dict[str, int]) -> None:
        self._quick(session, world, "Butter")

        (entry,) = expiry_service.get_items_needing_completion(session)

        assert entry.item.product_name == "Butter"
        assert entry.missing == ["Datum", "Kategorie"]

    def test_frozen_item_also_misses_the_freeze_date(self, session: Session, world: dict[str, int]) -> None:
        self._quick(
            session,
            world,
            "Bohnen",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
        )

        (entry,) = expiry_service.get_items_needing_completion(session)

        assert entry.missing == ["Datum", "Einfrierdatum", "Kategorie"]

    def test_category_without_shelf_life_counts_where_expiry_is_computed(
        self, session: Session, world: dict[str, int]
    ) -> None:
        """Selbst Eingefrorenes braucht eine Kategorie mit Haltbarkeit, sonst kein Ablaufdatum.

        Der Dienst lässt so einen Artikel nicht entstehen (Issue #385); er bleibt übrig, wenn
        die Haltbarkeit später an der Kategorie fehlt. Daher direkt in die Datenbank.
        """
        session.add(
            Item(
                product_name="Gulasch",
                best_before_date=date(2026, 3, 1),
                freeze_date=date(2026, 3, 2),
                quantity=1,
                unit="Stück",
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=world["freezer"],
                created_by=world["admin"],
                category_id=world["bare_cat"],
            )
        )
        session.commit()

        (entry,) = expiry_service.get_items_needing_completion(session)

        assert entry.missing == ["passende Kategorie"]

    def test_mhd_types_need_no_shelf_life(self, session: Session, world: dict[str, int]) -> None:
        """Bei TK-Ware mit MHD ist das MHD die Frist; die Kategorie braucht keine Haltbarkeit."""
        item_service.create_item(
            session,
            product_name="Lachs",
            best_before_date=date(2026, 12, 3),
            quantity=1,
            unit="Packung",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
            category_id=world["bare_cat"],
        )

        assert expiry_service.get_items_needing_completion(session) == []

    def test_complete_items_are_not_listed(self, session: Session, world: dict[str, int]) -> None:
        item_service.create_item(
            session,
            product_name="Erbsen",
            best_before_date=date(2026, 2, 1),
            quantity=1,
            unit="Beutel",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
            created_by=world["admin"],
            category_id=world["frozen_cat"],
            freeze_date=date(2026, 3, 1),
        )

        assert expiry_service.get_items_needing_completion(session) == []

    def test_consumed_items_are_not_listed(self, session: Session, world: dict[str, int]) -> None:
        item_id = self._quick(session, world, "Rest")
        item_service.mark_item_consumed(session, item_id, world["admin"])

        assert expiry_service.get_items_needing_completion(session) == []

    def test_newest_capture_comes_first(self, session: Session, world: dict[str, int]) -> None:
        self._quick(session, world, "zuerst")
        self._quick(session, world, "danach")

        names = [entry.item.product_name for entry in expiry_service.get_items_needing_completion(session)]

        assert names == ["danach", "zuerst"]


def test_item_types_for_a_frozen_location() -> None:
    """Im Keller zählt Tempo: Die Truhe zeigt nur Typen, die dort hineinpassen (Issue #463)."""
    assert item_types.get_item_types_for_location(LocationType.FROZEN) == [
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    ]


def test_item_types_for_unfrozen_locations() -> None:
    """Regal und Kühlschrank zeigen die ungefrorenen Typen, in Enum-Reihenfolge."""
    for location_type in (LocationType.AMBIENT, LocationType.CHILLED):
        assert item_types.get_item_types_for_location(location_type) == [
            ItemType.PURCHASED_FRESH,
            ItemType.HOMEMADE_PRESERVED,
        ]


def test_every_location_type_offers_at_least_one_item_type() -> None:
    """Kein Lagerort darf ohne wählbaren Typ bleiben, sonst steht die Schnellerfassung still."""
    for location_type in LocationType:
        assert item_types.get_item_types_for_location(location_type)
