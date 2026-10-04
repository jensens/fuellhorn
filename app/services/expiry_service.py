"""Expiry service - zentraler Haltbarkeitsstatus für Artikel (Issue #363).

Alle UI-Stellen (Dashboard, Vorratsliste, Item-Card, Bottom-Sheet) beziehen
Status, Anzeigedatum und Beschriftung ausschließlich von hier. Die Regeln:

- PURCHASED_FRESH / PURCHASED_FROZEN: das MHD der Packung ist das Anzeigedatum,
  Status nach den konfigurierbaren Schwellen (kritisch/warnung in Tagen).
- PURCHASED_THEN_FROZEN / HOMEMADE_FROZEN: Einfrierdatum + Kategorie-Haltbarkeit
  (FROZEN); HOMEMADE_PRESERVED: Produktionsdatum + Kategorie-Haltbarkeit (AMBIENT).
  Anzeigedatum ist das Idealdatum (months_min); warnung ab Idealdatum, kritisch
  nahe dem Maximaldatum (months_max).
- Fehlt Kategorie, Haltbarkeits-Konfiguration oder Einfrierdatum, ist der Status
  ``unknown`` – es gibt keinen Rückfall auf das Produktionsdatum.
"""

from ..models.category_shelf_life import CategoryShelfLife
from ..models.category_shelf_life import StorageType
from ..models.item import Item
from ..models.item import ItemType
from . import item_service
from . import shelf_life_service
from .expiry_calculator import calculate_expiry_dates
from .expiry_calculator import get_expiry_status_minmax
from .expiry_calculator import get_storage_type_for_item_type
from .preferences_service import get_expiry_thresholds
from dataclasses import dataclass
from datetime import date
from sqlmodel import Session
from sqlmodel import select
from typing import Literal


ExpiryViewStatus = Literal["ok", "warning", "critical", "unknown"]

LABEL_MHD = "MHD"
LABEL_OPTIMAL = "Ideal bis"
LABEL_UNKNOWN = "Keine Haltbarkeitsdaten"

# (critical_days, warning_days) – entspricht preferences_service.HARDCODED_DEFAULTS
DEFAULT_THRESHOLDS: tuple[int, int] = (3, 7)

FREEZE_DATE_TYPES = {ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN}


@dataclass(frozen=True)
class ExpiryView:
    """Anzeigefertiger Haltbarkeitsstatus eines Artikels."""

    status: ExpiryViewStatus
    display_date: date | None
    label: str


UNKNOWN_VIEW = ExpiryView(status="unknown", display_date=None, label=LABEL_UNKNOWN)

LABEL_PRODUCED = "Hergestellt am"
LABEL_FROZEN = "Eingefroren am"


def get_entered_dates(item: Item) -> list[tuple[str, date]]:
    """Die vom Nutzer erfassten Daten eines Artikels mit typabhängiger Beschriftung (Issue #342).

    - PURCHASED_FRESH / PURCHASED_FROZEN: das MHD der Packung
    - HOMEMADE_PRESERVED: Herstellungsdatum
    - HOMEMADE_FROZEN: Herstellungs- und Einfrierdatum
    - PURCHASED_THEN_FROZEN: nur das Einfrierdatum; best_before_date ist dort nur der
      Erfassungstag (siehe #387) und wird nicht gezeigt

    Returns:
        Liste von (Beschriftung, Datum), fehlende Einfrierdaten werden ausgelassen.
    """
    if item.item_type in (ItemType.PURCHASED_FRESH, ItemType.PURCHASED_FROZEN):
        return [(LABEL_MHD, item.best_before_date)]

    entries: list[tuple[str, date]] = []
    if item.item_type != ItemType.PURCHASED_THEN_FROZEN:
        entries.append((LABEL_PRODUCED, item.best_before_date))
    if item.item_type in FREEZE_DATE_TYPES and item.freeze_date is not None:
        entries.append((LABEL_FROZEN, item.freeze_date))
    return entries


def compute_expiry_view(
    item: Item,
    shelf_life: CategoryShelfLife | None,
    thresholds: tuple[int, int] = DEFAULT_THRESHOLDS,
    today: date | None = None,
) -> ExpiryView:
    """Berechnet den Haltbarkeitsstatus eines Artikels (reine Funktion).

    Args:
        item: Der Artikel.
        shelf_life: Haltbarkeits-Konfiguration seiner Kategorie für die passende
            Lagerart, oder None wenn keine existiert.
        thresholds: (critical_days, warning_days).
        today: Stichtag; Default ist das heutige Datum.

    Returns:
        ExpiryView mit Status, Anzeigedatum und Beschriftung.
    """
    today = today or date.today()
    critical_days, warning_days = thresholds

    storage_type = get_storage_type_for_item_type(item.item_type)
    if storage_type is None:
        status = get_expiry_status_minmax(
            None, None, item.best_before_date, critical_days=critical_days, warning_days=warning_days, today=today
        )
        return ExpiryView(status=status, display_date=item.best_before_date, label=LABEL_MHD)

    if item.category_id is None or shelf_life is None:
        return UNKNOWN_VIEW

    base_date = item.freeze_date if item.item_type in FREEZE_DATE_TYPES else item.best_before_date
    if base_date is None:
        return UNKNOWN_VIEW

    optimal_date, max_date = calculate_expiry_dates(
        item_type=item.item_type,
        base_date=base_date,
        months_min=shelf_life.months_min,
        months_max=shelf_life.months_max,
    )
    status = get_expiry_status_minmax(
        optimal_date, max_date, None, critical_days=critical_days, warning_days=warning_days, today=today
    )
    return ExpiryView(status=status, display_date=optimal_date, label=LABEL_OPTIMAL)


ShelfLifeIndex = dict[tuple[int, StorageType], CategoryShelfLife]


def _load_shelf_life_index(session: Session) -> ShelfLifeIndex:
    """Lädt alle Haltbarkeits-Konfigurationen mit einer Abfrage."""
    rows = session.exec(select(CategoryShelfLife)).all()
    return {(row.category_id, row.storage_type): row for row in rows}


def _shelf_life_from_index(item: Item, index: ShelfLifeIndex) -> CategoryShelfLife | None:
    storage_type = get_storage_type_for_item_type(item.item_type)
    if storage_type is None or item.category_id is None:
        return None
    return index.get((item.category_id, storage_type))


def get_item_expiry_view(session: Session, item: Item, today: date | None = None) -> ExpiryView:
    """Haltbarkeitsstatus eines einzelnen Artikels (Haltbarkeit und Schwellen aus der DB)."""
    shelf_life = None
    storage_type = get_storage_type_for_item_type(item.item_type)
    if storage_type is not None and item.category_id is not None:
        shelf_life = shelf_life_service.get_shelf_life(session, item.category_id, storage_type)
    return compute_expiry_view(item, shelf_life, get_expiry_thresholds(session), today)


def get_expiry_views(session: Session, items: list[Item], today: date | None = None) -> dict[int, ExpiryView]:
    """Haltbarkeitsstatus für viele Artikel; lädt Haltbarkeiten und Schwellen nur einmal.

    Returns:
        Mapping Artikel-ID → ExpiryView (Artikel ohne ID werden übersprungen).
    """
    thresholds = get_expiry_thresholds(session)
    index = _load_shelf_life_index(session)
    return {
        item.id: compute_expiry_view(item, _shelf_life_from_index(item, index), thresholds, today)
        for item in items
        if item.id is not None
    }


def get_items_expiring_soon(session: Session, today: date | None = None) -> list[Item]:
    """Aktive Artikel mit Status warning oder critical, nach Anzeigedatum sortiert.

    Ersetzt den alten Datumsvergleich auf best_before_date, der für eingefrorene
    und eingemachte Artikel das Produktionsdatum verglich. ``unknown`` zählt nicht.
    """
    items = item_service.get_active_items(session)
    views = get_expiry_views(session, items, today)
    expiring = [
        (item, views[item.id])
        for item in items
        if item.id is not None and views[item.id].status in ("warning", "critical")
    ]
    expiring.sort(key=lambda pair: pair[1].display_date or date.max)
    return [item for item, _ in expiring]
