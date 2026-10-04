"""Tests: Welche erfassten Daten gehören zu einem Artikel angezeigt (Issue #342).

Nach der Erfassung war nur das errechnete Haltbarkeitsdatum sichtbar, nicht das
eingegebene Herstellungs-/Einfrierdatum. ``get_entered_dates`` liefert die
anzuzeigenden Eingabedaten mit typabhängiger Beschriftung.
"""

from app.models import Item
from app.models import ItemType
from app.services.expiry_service import EnteredDate
from app.services.expiry_service import get_entered_dates
from datetime import date


PRODUCED = date(2026, 9, 1)
FROZEN = date(2026, 9, 2)


def _item(
    item_type: ItemType,
    freeze_date: date | None = None,
    *,
    best_before_month_only: bool = False,
    freeze_date_month_only: bool = False,
) -> Item:
    return Item(
        product_name="x",
        best_before_date=PRODUCED,
        best_before_month_only=best_before_month_only,
        freeze_date=freeze_date,
        freeze_date_month_only=freeze_date_month_only,
        quantity=1,
        unit="g",
        item_type=item_type,
        location_id=1,
        created_by=1,
    )


def test_purchased_fresh_shows_mhd() -> None:
    assert get_entered_dates(_item(ItemType.PURCHASED_FRESH)) == [EnteredDate("MHD", PRODUCED, False)]


def test_purchased_frozen_shows_mhd() -> None:
    assert get_entered_dates(_item(ItemType.PURCHASED_FROZEN)) == [EnteredDate("MHD", PRODUCED, False)]


def test_homemade_preserved_shows_production_date() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_PRESERVED)) == [EnteredDate("Hergestellt am", PRODUCED, False)]


def test_homemade_frozen_shows_production_and_freeze_date() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_FROZEN, FROZEN)) == [
        EnteredDate("Hergestellt am", PRODUCED, False),
        EnteredDate("Eingefroren am", FROZEN, False),
    ]


def test_purchased_then_frozen_shows_only_freeze_date() -> None:
    """best_before_date ist bei diesem Typ nur der Erfassungstag (siehe #387) und wird nicht gezeigt."""
    assert get_entered_dates(_item(ItemType.PURCHASED_THEN_FROZEN, FROZEN)) == [
        EnteredDate("Eingefroren am", FROZEN, False)
    ]


def test_missing_freeze_date_is_skipped() -> None:
    assert get_entered_dates(_item(ItemType.HOMEMADE_FROZEN, None)) == [EnteredDate("Hergestellt am", PRODUCED, False)]


def test_month_only_precision_is_reported_per_date() -> None:
    """Die Anzeige braucht die Genauigkeit, um „09/2026“ statt „01.09.2026“ zu zeigen (Issue #347)."""
    entries = get_entered_dates(
        _item(
            ItemType.HOMEMADE_FROZEN,
            FROZEN,
            best_before_month_only=True,
            freeze_date_month_only=False,
        )
    )

    assert [(entry.label, entry.month_only) for entry in entries] == [
        ("Hergestellt am", True),
        ("Eingefroren am", False),
    ]
