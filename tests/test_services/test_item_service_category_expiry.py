"""Tests for item_service category and expiry info functions (Issue #105, #151)."""

from app.models import ItemType
from app.models import LocationType
from app.models import User
from app.models.category_shelf_life import StorageType
from app.services import category_service
from app.services import item_service
from app.services import location_service
from app.services import shelf_life_service
from datetime import date
from dateutil.relativedelta import relativedelta
import pytest
from sqlmodel import Session


# =============================================================================
# Tests for create_item() with optional category_id
# =============================================================================


def test_create_item_without_category_id_succeeds(session: Session, test_admin: User) -> None:
    """Test that create_item works without category_id (optional since Issue #151)."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )

    # category_id is optional - should work without it
    item = item_service.create_item(
        session=session,
        product_name="Test",
        best_before_date=date(2025, 1, 1),
        quantity=1.0,
        unit="kg",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
    )

    assert item.id is not None
    assert item.category_id is None
    assert item.product_name == "Test"


def test_create_item_with_category_id_succeeds(session: Session, test_admin: User) -> None:
    """Test that create_item works with mandatory category_id."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milchprodukte",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Joghurt",
        best_before_date=date(2025, 1, 15),
        quantity=1,
        unit="Becher",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    assert item.id is not None
    assert item.category_id == category.id
    assert item.product_name == "Joghurt"


# =============================================================================
# Tests for get_item_category()
# =============================================================================


def test_get_item_category_returns_category(session: Session, test_admin: User) -> None:
    """Test that get_item_category returns the item's category."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Obst",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Äpfel",
        best_before_date=date(2025, 1, 20),
        quantity=5,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    result = item_service.get_item_category(session, item.id)

    assert result is not None
    assert result.id == category.id
    assert result.name == "Obst"


def test_get_item_category_item_not_found(session: Session) -> None:
    """Test that get_item_category raises ValueError for non-existent item."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.get_item_category(session, 999)


# =============================================================================
# Tests for get_item_expiry_info()
# =============================================================================


def test_get_item_expiry_info_purchased_fresh_uses_mhd(session: Session, test_admin: User) -> None:
    """Test that PURCHASED_FRESH items return best_before_date (MHD)."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Milch",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="Milch",
        best_before_date=date(2025, 1, 10),
        quantity=1,
        unit="L",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    assert optimal is None
    assert max_date is None
    assert mhd == date(2025, 1, 10)


def test_get_item_expiry_info_purchased_frozen_uses_mhd(session: Session, test_admin: User) -> None:
    """Test that PURCHASED_FROZEN items return best_before_date (MHD)."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="TK-Ware",
        created_by=test_admin.id,
    )

    assert category.id is not None

    item = item_service.create_item(
        session=session,
        product_name="TK-Pizza",
        best_before_date=date(2025, 6, 1),
        quantity=2,
        unit="Stück",
        item_type=ItemType.PURCHASED_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    assert optimal is None
    assert max_date is None
    assert mhd == date(2025, 6, 1)


def test_get_item_expiry_info_frozen_with_shelf_life(session: Session, test_admin: User) -> None:
    """Test that PURCHASED_THEN_FROZEN items use shelf life config."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Fleisch",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create shelf life config: 3-6 months frozen
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=category.id,
        storage_type=StorageType.FROZEN,
        months_min=3,
        months_max=6,
    )

    freeze_date = date(2025, 1, 1)
    item = item_service.create_item(
        session=session,
        product_name="Rindfleisch",
        best_before_date=date(2025, 1, 5),  # Original MHD
        freeze_date=freeze_date,
        quantity=500,
        unit="g",
        item_type=ItemType.PURCHASED_THEN_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    assert optimal == freeze_date + relativedelta(months=3)  # 2025-04-01
    assert max_date == freeze_date + relativedelta(months=6)  # 2025-07-01
    assert mhd is None


def test_get_item_expiry_info_homemade_frozen_with_shelf_life(session: Session, test_admin: User) -> None:
    """Test that HOMEMADE_FROZEN items use shelf life config."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create shelf life config: 6-12 months frozen
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    freeze_date = date(2025, 2, 1)
    item = item_service.create_item(
        session=session,
        product_name="Erbsen",
        best_before_date=freeze_date,  # Production date for homemade
        freeze_date=freeze_date,
        quantity=1,
        unit="kg",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    assert optimal == freeze_date + relativedelta(months=6)  # 2025-08-01
    assert max_date == freeze_date + relativedelta(months=12)  # 2026-02-01
    assert mhd is None


def test_get_item_expiry_info_homemade_preserved_with_shelf_life(session: Session, test_admin: User) -> None:
    """Test that HOMEMADE_PRESERVED items use shelf life config (ambient)."""
    location = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Eingemachtes",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # Create shelf life config: 12-24 months ambient
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=category.id,
        storage_type=StorageType.AMBIENT,
        months_min=12,
        months_max=24,
    )

    production_date = date(2025, 3, 1)
    item = item_service.create_item(
        session=session,
        product_name="Marmelade",
        best_before_date=production_date,  # Production date for homemade
        quantity=6,
        unit="Gläser",
        item_type=ItemType.HOMEMADE_PRESERVED,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    assert optimal == production_date + relativedelta(months=12)  # 2026-03-01
    assert max_date == production_date + relativedelta(months=24)  # 2027-03-01
    assert mhd is None


def test_get_item_expiry_info_frozen_no_shelf_life_config(session: Session, test_admin: User) -> None:
    """Test that frozen items without shelf life config return None dates."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    category = category_service.create_category(
        session=session,
        name="Sonstiges",
        created_by=test_admin.id,
    )

    assert category.id is not None

    # No shelf life config for this category

    item = item_service.create_item(
        session=session,
        product_name="Unbekanntes",
        best_before_date=date(2025, 1, 1),
        freeze_date=date(2025, 1, 1),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_THEN_FROZEN,
        location_id=location.id,
        created_by=test_admin.id,
        category_id=category.id,
    )

    optimal, max_date, mhd = item_service.get_item_expiry_info(session, item.id)

    # No shelf life config - return None for all
    assert optimal is None
    assert max_date is None
    assert mhd is None


def test_get_item_expiry_info_item_not_found(session: Session) -> None:
    """Test that get_item_expiry_info raises ValueError for non-existent item."""
    with pytest.raises(ValueError, match="Item with id 999 not found"):
        item_service.get_item_expiry_info(session, 999)
