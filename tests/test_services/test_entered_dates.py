"""Tests: Welche erfassten Daten gehören zu einem Artikel angezeigt (Issue #342).

Nach der Erfassung war nur das errechnete Haltbarkeitsdatum sichtbar, nicht das
eingegebene Herstellungs-/Einfrierdatum. ``get_entered_dates`` liefert die
anzuzeigenden Eingabedaten mit typabhängiger Beschriftung.
"""

from app.models import Item
from app.models import ItemType
from app.services.expiry_service import get_entered_dates
from datetime import date


PRODUCED = date(2026, 9, 1)
FROZEN = date(2026, 9, 2)


def _item(item_type: ItemType, freeze_date: date | None = None) -> Item:
    return Item(
        product_name="x",
        best_before_date=PRODUCED,
        freeze_date=freeze_date,
        quantity=1,
        unit="g",
        item_type=item_type,
        location_id=1,
        created_by=1,
    )


def test_purchased_fresh_shows_mhd() -> None:
    assert get_entered_dates(_item(ItemType.PURCHASED_FRESH)) == [("MHD", PRODUCED)]


def test_purchased_frozen_shows_mhd() -> None:
    assert get_entered_dates(_item(ItemType.PURCHASED_FROZEN)) == [("MHD", PRODUCED)]


def test_homemade_preserved_shows_production_date() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_PRESERVED)) == [("Hergestellt am", PRODUCED)]


def test_homemade_frozen_shows_production_and_freeze_date() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_FROZEN, FROZEN)) == [
        ("Hergestellt am", PRODUCED),
        ("Eingefroren am", FROZEN),
    ]


def test_purchased_then_frozen_shows_only_freeze_date() -> None:
    """best_before_date ist bei diesem Typ nur der Erfassungstag (siehe #387) und wird nicht gezeigt."""
    assert get_entered_dates(_item(ItemType.PURCHASED_THEN_FROZEN, FROZEN)) == [("Eingefroren am", FROZEN)]


def test_missing_freeze_date_is_skipped() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_FROZEN, None)) == [("Hergestellt am", PRODUCED)]
