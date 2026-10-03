"""Tests für den zentralen Haltbarkeitsstatus (Issue #363).

``compute_expiry_view`` ist eine reine Funktion: Artikel + Haltbarkeits-Konfiguration
+ Schwellen + Stichtag → ``ExpiryView(status, display_date, label)``. Sie ersetzt die
verstreuten und widersprüchlichen Berechnungen in Item-Card, Bottom-Sheet, Dashboard
und Vorratsliste.
"""

from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import StorageType
from app.services.expiry_service import ExpiryView
from app.services.expiry_service import compute_expiry_view
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta


# Fixer Stichtag, bewusst nicht das reale Datum: deckt auf, wenn ``today`` nicht durchgereicht wird.
TODAY = date(2030, 6, 15)


def _item(item_type: ItemType, best_before: date, freeze_date: date | None = None, category_id: int | None = 1) -> Item:
    return Item(
        product_name="Testartikel",
        best_before_date=best_before,
        freeze_date=freeze_date,
        quantity=1.0,
        unit="g",
        item_type=item_type,
        location_id=1,
        category_id=category_id,
        created_by=1,
    )


FROZEN_2_3 = CategoryShelfLife(category_id=1, storage_type=StorageType.FROZEN, months_min=2, months_max=3)
AMBIENT_6_12 = CategoryShelfLife(category_id=1, storage_type=StorageType.AMBIENT, months_min=6, months_max=12)


# --- MHD-Typen: PURCHASED_FRESH / PURCHASED_FROZEN -------------------------------


def test_purchased_fresh_far_mhd_is_ok_with_mhd_label() -> None:
    """MHD in 10 Tagen → ok, Anzeigedatum = MHD, Beschriftung 'MHD'."""
    mhd = TODAY + timedelta(days=10)
    view = compute_expiry_view(_item(ItemType.PURCHASED_FRESH, mhd), None, today=TODAY)
    assert view == ExpiryView(status="ok", display_date=mhd, label="MHD")


def test_purchased_fresh_mhd_within_warning_days_is_warning() -> None:
    """MHD in 5 Tagen (Default-Warnschwelle 7) → warning."""
    view = compute_expiry_view(_item(ItemType.PURCHASED_FRESH, TODAY + timedelta(days=5)), None, today=TODAY)
    assert view.status == "warning"


def test_purchased_fresh_mhd_within_critical_days_is_critical() -> None:
    """MHD in 2 Tagen (Default-Kritischschwelle 3) → critical."""
    view = compute_expiry_view(_item(ItemType.PURCHASED_FRESH, TODAY + timedelta(days=2)), None, today=TODAY)
    assert view.status == "critical"


def test_purchased_fresh_past_mhd_is_critical() -> None:
    """Abgelaufenes MHD → critical."""
    view = compute_expiry_view(_item(ItemType.PURCHASED_FRESH, TODAY - timedelta(days=1)), None, today=TODAY)
    assert view.status == "critical"


def test_purchased_frozen_uses_mhd_even_with_shelf_life() -> None:
    """TK-Ware gekauft nutzt das MHD der Packung, nicht die Kategorie-Haltbarkeit."""
    mhd = TODAY + timedelta(days=30)
    view = compute_expiry_view(_item(ItemType.PURCHASED_FROZEN, mhd), FROZEN_2_3, today=TODAY)
    assert view == ExpiryView(status="ok", display_date=mhd, label="MHD")


# --- Haltbarkeits-Typen: HOMEMADE_FROZEN / PURCHASED_THEN_FROZEN / HOMEMADE_PRESERVED


def test_homemade_frozen_today_is_ok_with_optimal_date() -> None:
    """Review-Szenario: heute eingefroren, 2–3 Monate → ok, Anzeigedatum = Idealdatum."""
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=TODAY - timedelta(days=1), freeze_date=TODAY)
    view = compute_expiry_view(item, FROZEN_2_3, today=TODAY)
    assert view == ExpiryView(status="ok", display_date=TODAY + relativedelta(months=2), label="Ideal bis")


def test_homemade_frozen_past_optimal_is_warning() -> None:
    """Idealdatum überschritten, Maximum noch mehr als 3 Tage entfernt → warning."""
    freeze = TODAY - relativedelta(months=2, days=10)
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=freeze, freeze_date=freeze)
    assert compute_expiry_view(item, FROZEN_2_3, today=TODAY).status == "warning"


def test_homemade_frozen_at_max_is_critical() -> None:
    """Maximaldatum erreicht → critical."""
    freeze = TODAY - relativedelta(months=3)
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=freeze, freeze_date=freeze)
    assert compute_expiry_view(item, FROZEN_2_3, today=TODAY).status == "critical"


def test_purchased_then_frozen_uses_freeze_date() -> None:
    """Gekauft → eingefroren rechnet vom Einfrierdatum, nicht vom best_before_date."""
    freeze = TODAY - timedelta(days=7)
    item = _item(ItemType.PURCHASED_THEN_FROZEN, best_before=TODAY, freeze_date=freeze)
    view = compute_expiry_view(item, FROZEN_2_3, today=TODAY)
    assert view.display_date == freeze + relativedelta(months=2)


def test_homemade_preserved_uses_production_date_and_ambient_shelf_life() -> None:
    """Eingemachtes rechnet vom Produktionsdatum (best_before_date) mit AMBIENT-Haltbarkeit."""
    production = TODAY - timedelta(days=30)
    view = compute_expiry_view(_item(ItemType.HOMEMADE_PRESERVED, production), AMBIENT_6_12, today=TODAY)
    assert view == ExpiryView(status="ok", display_date=production + relativedelta(months=6), label="Ideal bis")


# --- unknown -----------------------------------------------------------------------


def test_shelf_life_type_without_shelf_life_is_unknown() -> None:
    """Kategorie ohne passende Haltbarkeit → unknown, kein Datum, erklärende Beschriftung."""
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=TODAY, freeze_date=TODAY)
    view = compute_expiry_view(item, None, today=TODAY)
    assert view == ExpiryView(status="unknown", display_date=None, label="Keine Haltbarkeitsdaten")


def test_frozen_type_without_freeze_date_is_unknown() -> None:
    """Eingefrorener Typ ohne Einfrierdatum → unknown (kein Rückfall auf das Produktionsdatum)."""
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=TODAY - timedelta(days=60), freeze_date=None)
    assert compute_expiry_view(item, FROZEN_2_3, today=TODAY).status == "unknown"


def test_shelf_life_type_without_category_is_unknown() -> None:
    """Ohne Kategorie kann keine Haltbarkeit nachgeschlagen werden → unknown."""
    item = _item(ItemType.HOMEMADE_PRESERVED, best_before=TODAY, category_id=None)
    assert compute_expiry_view(item, None, today=TODAY).status == "unknown"


# --- konfigurierbare Schwellen ----------------------------------------------------


def test_thresholds_are_applied_to_mhd_items() -> None:
    """Mit Warnschwelle 14 Tagen ist ein MHD in 10 Tagen bereits warning."""
    item = _item(ItemType.PURCHASED_FRESH, TODAY + timedelta(days=10))
    assert compute_expiry_view(item, None, thresholds=(1, 14), today=TODAY).status == "warning"


def test_thresholds_are_applied_to_shelf_life_items() -> None:
    """Mit Kritischschwelle 30 Tagen ist ein Maximaldatum in 20 Tagen critical."""
    freeze = TODAY - relativedelta(months=3) + timedelta(days=20)
    item = _item(ItemType.HOMEMADE_FROZEN, best_before=freeze, freeze_date=freeze)
    assert compute_expiry_view(item, FROZEN_2_3, thresholds=(30, 60), today=TODAY).status == "critical"
