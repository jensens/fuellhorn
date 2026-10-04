"""Artikel ohne Datum: speicherbar, Status „Keine Haltbarkeitsdaten“ (Issue #463).

Für die Schnellerfassung im Keller zählen nur Ort, Name, Menge, Einheit und Typ. Datum,
Kategorie und Einfrierdatum werden später oben im Warmen nachgepflegt, also muss ein
Artikel ohne diese Angaben existieren können, ohne dass irgendwo ein Datum erfunden wird.
Der normale Weg über den Wizard bleibt streng.
"""

from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import User
from app.services import expiry_service
from app.services import item_service
from app.services.errors import ServiceValidationError
from app.ui.pages.items import _sort_items
from datetime import date
import pytest
from sqlmodel import Session


def _item(item_type: ItemType, best_before: date | None, freeze_date: date | None = None, name: str = "x") -> Item:
    return Item(
        product_name=name,
        best_before_date=best_before,
        freeze_date=freeze_date,
        quantity=1,
        unit="Stück",
        item_type=item_type,
        location_id=1,
        created_by=1,
    )


@pytest.fixture(name="places")
def places_fixture(session: Session, test_admin: User) -> dict[str, int]:
    """Ein gekühlter und ein gefrorener Lagerort in derselben Session."""
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    session.add_all([fridge, freezer])
    session.commit()
    session.refresh(fridge)
    session.refresh(freezer)
    assert fridge.id is not None and freezer.id is not None
    return {"admin": test_admin.id, "chilled": fridge.id, "frozen": freezer.id}


def test_item_without_a_date_can_be_built() -> None:
    assert _item(ItemType.PURCHASED_FRESH, None).best_before_date is None


class TestStatusWithoutDate:
    @pytest.mark.parametrize(
        "item_type",
        [ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN, ItemType.HOMEMADE_PRESERVED],
    )
    def test_no_date_means_no_expiry_data(self, session: Session, item_type: ItemType) -> None:
        view = expiry_service.get_item_expiry_view(session, _item(item_type, None), today=date(2026, 10, 4))

        assert view == expiry_service.UNKNOWN_VIEW
        assert view.display_date is None and view.label == "Keine Haltbarkeitsdaten"

    def test_entered_dates_skip_the_missing_date(self) -> None:
        assert expiry_service.get_entered_dates(_item(ItemType.PURCHASED_FRESH, None)) == []

    def test_entered_dates_still_show_a_known_freeze_date(self) -> None:
        entries = expiry_service.get_entered_dates(_item(ItemType.HOMEMADE_FROZEN, None, freeze_date=date(2026, 3, 1)))

        assert [(entry.label, entry.value) for entry in entries] == [("Eingefroren am", date(2026, 3, 1))]


class TestQuickCaptureValidation:
    """``require_complete=False`` lässt Lücken zu, prüft aber weiter die Zusammenhänge."""

    def _validate(self, session: Session, places: dict[str, int], **overrides: object) -> None:
        arguments: dict[str, object] = {
            "product_name": "Erbsen",
            "quantity": 3,
            "unit": "Beutel",
            "item_type": ItemType.PURCHASED_FRESH,
            "location_id": places["chilled"],
            "category_id": None,
            "best_before_date": None,
            "freeze_date": None,
        }
        arguments.update(overrides)
        item_service.validate_item_data(session, **arguments)  # type: ignore[arg-type]

    def test_gaps_are_allowed(self, session: Session, places: dict[str, int]) -> None:
        self._validate(session, places, require_complete=False)

    def test_frozen_item_without_freeze_date_is_allowed(self, session: Session, places: dict[str, int]) -> None:
        self._validate(
            session,
            places,
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=places["frozen"],
            require_complete=False,
        )

    def test_date_order_is_only_checked_when_both_are_known(self, session: Session, places: dict[str, int]) -> None:
        self._validate(
            session,
            places,
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=places["frozen"],
            freeze_date=date(2026, 3, 1),
            require_complete=False,
        )

    def test_location_type_is_still_checked(self, session: Session, places: dict[str, int]) -> None:
        """Auch in Eile darf TK-Ware nicht in den Kühlschrank."""
        with pytest.raises(ServiceValidationError, match="passt nicht"):
            self._validate(
                session,
                places,
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=places["chilled"],
                require_complete=False,
            )

    def test_quantity_is_still_checked(self, session: Session, places: dict[str, int]) -> None:
        with pytest.raises(ServiceValidationError, match="Menge"):
            self._validate(session, places, quantity=0, require_complete=False)

    def test_the_normal_path_still_requires_a_date(self, session: Session, places: dict[str, int]) -> None:
        with pytest.raises(ServiceValidationError, match="Datum ist erforderlich"):
            self._validate(session, places)

    def test_the_normal_path_still_requires_the_freeze_date(self, session: Session, places: dict[str, int]) -> None:
        with pytest.raises(ServiceValidationError, match="Einfrierdatum"):
            self._validate(
                session,
                places,
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=places["frozen"],
                best_before_date=date(2026, 3, 1),
            )


def test_expiry_info_without_a_date_is_empty(session: Session, places: dict[str, int]) -> None:
    item = _item(ItemType.PURCHASED_FRESH, None, name="Milch")
    item.location_id = places["chilled"]
    item.created_by = places["admin"]
    session.add(item)
    session.commit()
    session.refresh(item)
    assert item.id is not None

    assert item_service.get_item_expiry_info(session, item.id) == (None, None, None)


def test_preserved_item_without_production_date_has_no_dates(session: Session, places: dict[str, int]) -> None:
    """Eingemachtes ohne Herstellungsdatum lässt sich nicht rechnen, auch mit Kategorie."""
    item = _item(ItemType.HOMEMADE_PRESERVED, None, name="Marmelade")
    item.location_id = places["chilled"]
    item.created_by = places["admin"]
    session.add(item)
    session.commit()
    session.refresh(item)
    assert item.id is not None

    assert item_service.get_item_expiry_info(session, item.id) == (None, None, None)


def test_items_without_a_date_sort_last() -> None:
    """Ohne wirksame Datumsliste darf die Sortierung nicht über ein fehlendes Datum stolpern."""
    with_date = _item(ItemType.PURCHASED_FRESH, date(2026, 3, 1), name="mit Datum")
    without_date = _item(ItemType.PURCHASED_FRESH, None, name="ohne Datum")

    ordered = _sort_items([without_date, with_date], "best_before_date", ascending=True)

    assert [item.product_name for item in ordered] == ["mit Datum", "ohne Datum"]
