"""Eine Quelle der Wahrheit für alles, was vom Artikel-Typ abhängt (Issue #398).

Vorher lebten ItemType→Lagerart-Mapping, erlaubte Lagerort-Typen, Datumsfelder und
Anzeigenamen verstreut in Services, Komponenten und Seiten, teils mit abweichender
Semantik. Hier steht pro Typ eine Zeile; alle Stellen konsumieren sie.
"""

from ..models.category_shelf_life import StorageType
from ..models.item import ItemType
from ..models.location import LocationType
from dataclasses import dataclass


@dataclass(frozen=True)
class ItemTypeSpec:
    """Verhalten eines Artikel-Typs.

    Attributes:
        label: Anzeigename (Wizard-Chips, Fehlermeldungen, Filter).
        short_label: Kurzform für das Badge auf der Artikel-Karte.
        expiry_storage_type: Lagerart für die Haltbarkeits-Berechnung; ``None`` = das MHD
            der Packung gilt direkt (``purchased_fresh``, ``purchased_frozen``).
        filter_storage_type: Lagerart, nach der Kategorien im Wizard gefiltert werden;
            ``purchased_frozen`` zeigt absichtlich nur FROZEN-Kategorien, obwohl es
            per MHD abläuft. ``None`` = alle Kategorien.
        location_types: erlaubte Lagerort-Typen.
        uses_freeze_date: Einfrierdatum ist Pflicht und Basis der Haltbarkeit.
        best_before_label: Beschriftung von ``best_before_date`` ("MHD" bzw.
            "Hergestellt am"); ``None`` = Feld wird nicht erfasst, der Service spiegelt
            dort das Einfrierdatum (``purchased_then_frozen``, Issue #387).
    """

    label: str
    short_label: str
    expiry_storage_type: StorageType | None
    filter_storage_type: StorageType | None
    location_types: tuple[LocationType, ...]
    uses_freeze_date: bool
    best_before_label: str | None


LABEL_MHD = "MHD"
LABEL_PRODUCED = "Hergestellt am"
LABEL_FROZEN = "Eingefroren am"

_FROZEN_LOCATIONS = (LocationType.FROZEN,)
_UNFROZEN_LOCATIONS = (LocationType.AMBIENT, LocationType.CHILLED)

ITEM_TYPE_SPECS: dict[ItemType, ItemTypeSpec] = {
    ItemType.PURCHASED_FRESH: ItemTypeSpec(
        label="Frisch eingekauft",
        short_label="Frisch",
        expiry_storage_type=None,
        filter_storage_type=None,
        location_types=_UNFROZEN_LOCATIONS,
        uses_freeze_date=False,
        best_before_label=LABEL_MHD,
    ),
    ItemType.PURCHASED_FROZEN: ItemTypeSpec(
        label="TK-Ware gekauft",
        short_label="TK gekauft",
        expiry_storage_type=None,
        filter_storage_type=StorageType.FROZEN,
        location_types=_FROZEN_LOCATIONS,
        uses_freeze_date=False,
        best_before_label=LABEL_MHD,
    ),
    ItemType.PURCHASED_THEN_FROZEN: ItemTypeSpec(
        label="Frisch gekauft → eingefroren",
        short_label="Eingefr.",
        expiry_storage_type=StorageType.FROZEN,
        filter_storage_type=StorageType.FROZEN,
        location_types=_FROZEN_LOCATIONS,
        uses_freeze_date=True,
        best_before_label=None,
    ),
    ItemType.HOMEMADE_FROZEN: ItemTypeSpec(
        label="Selbst eingefroren",
        short_label="Selbst eingefr.",
        expiry_storage_type=StorageType.FROZEN,
        filter_storage_type=StorageType.FROZEN,
        location_types=_FROZEN_LOCATIONS,
        uses_freeze_date=True,
        best_before_label=LABEL_PRODUCED,
    ),
    ItemType.HOMEMADE_PRESERVED: ItemTypeSpec(
        label="Selbst eingemacht",
        short_label="Eingemacht",
        expiry_storage_type=StorageType.AMBIENT,
        filter_storage_type=StorageType.AMBIENT,
        location_types=_UNFROZEN_LOCATIONS,
        uses_freeze_date=False,
        best_before_label=LABEL_PRODUCED,
    ),
}

ITEM_TYPE_LABELS: dict[ItemType, str] = {item_type: spec.label for item_type, spec in ITEM_TYPE_SPECS.items()}
ITEM_TYPE_SHORT_LABELS: dict[ItemType, str] = {
    item_type: spec.short_label for item_type, spec in ITEM_TYPE_SPECS.items()
}
FREEZE_DATE_TYPES: frozenset[ItemType] = frozenset(
    item_type for item_type, spec in ITEM_TYPE_SPECS.items() if spec.uses_freeze_date
)

LOCATION_TYPE_LABELS: dict[LocationType, str] = {
    LocationType.FROZEN: "Gefroren",
    LocationType.CHILLED: "Gekühlt",
    LocationType.AMBIENT: "Raumtemperatur",
}
STORAGE_TYPE_LABELS: dict[StorageType, str] = {
    StorageType.FROZEN: "Tiefkühlung",
    StorageType.CHILLED: "Kühlung",
    StorageType.AMBIENT: "Raumtemperatur",
}


def spec_for(item_type: ItemType) -> ItemTypeSpec:
    """Spec eines Typs; jeder ``ItemType`` hat genau eine Zeile."""
    return ITEM_TYPE_SPECS[item_type]


def get_item_type_label(item_type: ItemType) -> str:
    """Anzeigename eines Artikel-Typs."""
    return ITEM_TYPE_SPECS[item_type].label


def get_storage_type_for_item_type(item_type: ItemType) -> StorageType | None:
    """Lagerart für die Haltbarkeits-Berechnung; ``None`` = MHD gilt direkt."""
    return ITEM_TYPE_SPECS[item_type].expiry_storage_type


def get_filter_storage_type(item_type: ItemType) -> StorageType | None:
    """Lagerart für den Kategoriefilter im Wizard; ``None`` = alle Kategorien."""
    return ITEM_TYPE_SPECS[item_type].filter_storage_type


def get_valid_location_types(item_type: ItemType) -> list[LocationType]:
    """Erlaubte Lagerort-Typen eines Artikel-Typs."""
    return list(ITEM_TYPE_SPECS[item_type].location_types)


def uses_freeze_date(item_type: ItemType) -> bool:
    """Einfrierdatum ist Pflicht und Basis der Haltbarkeit."""
    return ITEM_TYPE_SPECS[item_type].uses_freeze_date


def get_best_before_label(item_type: ItemType) -> str | None:
    """Beschriftung von ``best_before_date``; ``None`` = Feld wird nicht erfasst."""
    return ITEM_TYPE_SPECS[item_type].best_before_label


BEST_BEFORE_INPUT_LABELS: dict[str, str] = {
    LABEL_MHD: "Mindesthaltbarkeitsdatum (MHD)",
    LABEL_PRODUCED: LABEL_PRODUCED,
}


def get_best_before_input_label(item_type: ItemType) -> str | None:
    """Lange Form der ``best_before_date``-Beschriftung für Eingabefelder (Wizard, Edit-View)."""
    label = ITEM_TYPE_SPECS[item_type].best_before_label
    return None if label is None else BEST_BEFORE_INPUT_LABELS[label]
