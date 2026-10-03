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
from ..models.item import Item
from ..models.item import ItemType
from .expiry_calculator import calculate_expiry_dates
from .expiry_calculator import get_expiry_status_minmax
from .expiry_calculator import get_storage_type_for_item_type
from dataclasses import dataclass
from datetime import date
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
