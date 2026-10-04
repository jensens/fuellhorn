"""Spec-Tabelle der Artikel-Typen: je Typ eine Zeile, alle Konsumenten lesen sie (Issue #398)."""

from app.models import ItemType
from app.models import LocationType
from app.models import StorageType
from app.services import category_service
from app.services import expiry_calculator
from app.services import expiry_service
from app.services import item_service
from app.services import item_types
from app.services import location_service
from app.ui.components import item_card
from app.ui.components import item_type_chips
from app.ui.pages import edit_item
from app.ui.validation import wizard_validation
from datetime import date
import pytest


FROZEN = (LocationType.FROZEN,)
UNFROZEN = (LocationType.AMBIENT, LocationType.CHILLED)

# (Typ, Label, Haltbarkeits-Lagerart, Filter-Lagerart, Lagerort-Typen, Einfrierdatum, best_before-Label)
SPEC_TABLE = [
    (ItemType.PURCHASED_FRESH, "Frisch eingekauft", None, None, UNFROZEN, False, "MHD"),
    (ItemType.PURCHASED_FROZEN, "TK-Ware gekauft", None, StorageType.FROZEN, FROZEN, False, "MHD"),
    (
        ItemType.PURCHASED_THEN_FROZEN,
        "Frisch gekauft → eingefroren",
        StorageType.FROZEN,
        StorageType.FROZEN,
        FROZEN,
        True,
        None,
    ),
    (
        ItemType.HOMEMADE_FROZEN,
        "Selbst eingefroren",
        StorageType.FROZEN,
        StorageType.FROZEN,
        FROZEN,
        True,
        "Hergestellt am",
    ),
    (
        ItemType.HOMEMADE_PRESERVED,
        "Selbst eingemacht",
        StorageType.AMBIENT,
        StorageType.AMBIENT,
        UNFROZEN,
        False,
        "Hergestellt am",
    ),
]


def test_every_item_type_has_exactly_one_spec_row() -> None:
    assert set(item_types.ITEM_TYPE_SPECS) == set(ItemType)
    assert [row[0] for row in SPEC_TABLE] == list(ItemType)


@pytest.mark.parametrize(
    ("item_type", "label", "expiry_storage", "filter_storage", "locations", "freeze", "bb_label"), SPEC_TABLE
)
def test_spec_row(
    item_type: ItemType,
    label: str,
    expiry_storage: StorageType | None,
    filter_storage: StorageType | None,
    locations: tuple[LocationType, ...],
    freeze: bool,
    bb_label: str | None,
) -> None:
    spec = item_types.spec_for(item_type)

    assert (spec.label, spec.expiry_storage_type, spec.filter_storage_type) == (label, expiry_storage, filter_storage)
    assert (spec.location_types, spec.uses_freeze_date, spec.best_before_label) == (locations, freeze, bb_label)


@pytest.mark.parametrize("item_type", list(ItemType))
def test_services_consume_the_spec(item_type: ItemType) -> None:
    """Die drei früher getrennten Mappings liefern exakt die Spec-Werte."""
    spec = item_types.spec_for(item_type)

    assert expiry_calculator.get_storage_type_for_item_type(item_type) == spec.expiry_storage_type
    assert location_service.get_valid_location_types(item_type) == list(spec.location_types)
    assert category_service._get_storage_type_for_filtering(item_type) == spec.filter_storage_type
    assert item_service.ITEM_TYPE_LABELS[item_type] == spec.label
    assert item_type_chips.get_item_type_label(item_type) == spec.label
    assert item_card.ITEM_TYPE_SHORT_LABELS[item_type] == spec.short_label


def test_freeze_date_types_come_from_the_spec() -> None:
    expected = {ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN}

    assert set(item_types.FREEZE_DATE_TYPES) == expected
    assert set(item_service.FREEZE_DATE_REQUIRED_TYPES) == expected
    assert set(expiry_service.FREEZE_DATE_TYPES) == expected
    assert set(edit_item.FREEZE_DATE_TYPES) == expected
    assert wizard_validation.validate_freeze_date(None, ItemType.PURCHASED_FROZEN, date(2026, 1, 1)) is None
    assert wizard_validation.validate_freeze_date(None, ItemType.HOMEMADE_FROZEN, date(2026, 1, 1)) is not None


@pytest.mark.parametrize("item_type", list(ItemType))
def test_edit_view_date_label_follows_the_spec(item_type: ItemType) -> None:
    label = edit_item._date_label(item_type)
    bb_label = item_types.get_best_before_label(item_type)

    if bb_label == "MHD":
        assert label.startswith("Mindesthaltbarkeitsdatum")
    else:
        assert label.startswith("Hergestellt am")


def test_items_filter_labels_come_from_the_spec() -> None:
    from app.ui.pages.items import ITEM_TYPE_LABELS as FILTER_LABELS

    assert FILTER_LABELS[""] == "Alle Typen"
    for item_type in ItemType:
        assert FILTER_LABELS[item_type.value] == item_types.get_item_type_label(item_type)
