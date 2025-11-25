"""Unit tests for wizard validation logic."""

from app.models.freeze_time_config import ItemType
from app.ui.validation import is_step1_valid
from app.ui.validation import validate_item_type
from app.ui.validation import validate_product_name
from app.ui.validation import validate_quantity
from app.ui.validation import validate_step1


# Product Name Validation Tests


def test_validate_product_name_valid() -> None:
    """Test valid product names."""
    assert validate_product_name("Tomaten") is None
    assert validate_product_name("AB") is None  # Minimum 2 chars
    assert validate_product_name("  Erbsen  ") is None  # Trimmed


def test_validate_product_name_too_short() -> None:
    """Test product name < 2 characters."""
    assert validate_product_name("A") == "Mindestens 2 Zeichen erforderlich"
    assert validate_product_name("") == "Mindestens 2 Zeichen erforderlich"
    assert validate_product_name("   ") == "Mindestens 2 Zeichen erforderlich"


def test_validate_product_name_none() -> None:
    """Test product name is None."""
    assert validate_product_name(None) == "Mindestens 2 Zeichen erforderlich"


# Quantity Validation Tests


def test_validate_quantity_valid() -> None:
    """Test valid quantities."""
    assert validate_quantity(1.0) is None
    assert validate_quantity(0.1) is None
    assert validate_quantity(500) is None
    assert validate_quantity(999.99) is None


def test_validate_quantity_zero() -> None:
    """Test quantity = 0."""
    assert validate_quantity(0) == "Menge muss größer als 0 sein"
    assert validate_quantity(0.0) == "Menge muss größer als 0 sein"


def test_validate_quantity_negative() -> None:
    """Test negative quantity."""
    assert validate_quantity(-1) == "Menge muss größer als 0 sein"
    assert validate_quantity(-0.5) == "Menge muss größer als 0 sein"


def test_validate_quantity_none() -> None:
    """Test quantity is None."""
    assert validate_quantity(None) == "Menge muss größer als 0 sein"


# Item Type Validation Tests


def test_validate_item_type_valid() -> None:
    """Test valid item type."""
    assert validate_item_type(ItemType.PURCHASED_FRESH) is None
    assert validate_item_type(ItemType.PURCHASED_FROZEN) is None
    assert validate_item_type(ItemType.HOMEMADE_PRESERVED) is None


def test_validate_item_type_none() -> None:
    """Test item type is None."""
    assert validate_item_type(None) == "Bitte Artikel-Typ auswählen"


# Step 1 Complete Validation Tests


def test_validate_step1_all_valid() -> None:
    """Test Step 1 with all valid fields."""
    errors = validate_step1(
        product_name="Tomaten",
        item_type=ItemType.PURCHASED_FRESH,
        quantity=500.0,
        unit="g",
    )
    assert errors == {}
    assert len(errors) == 0


def test_validate_step1_all_invalid() -> None:
    """Test Step 1 with all invalid fields."""
    errors = validate_step1(
        product_name="",
        item_type=None,
        quantity=0,
        unit=None,
    )
    assert len(errors) == 4
    assert "product_name" in errors
    assert "item_type" in errors
    assert "quantity" in errors
    assert "unit" in errors


def test_validate_step1_product_name_invalid() -> None:
    """Test Step 1 with invalid product name only."""
    errors = validate_step1(
        product_name="A",
        item_type=ItemType.PURCHASED_FROZEN,
        quantity=100.0,
        unit="kg",
    )
    assert len(errors) == 1
    assert "product_name" in errors
    assert errors["product_name"] == "Mindestens 2 Zeichen erforderlich"


def test_validate_step1_quantity_invalid() -> None:
    """Test Step 1 with invalid quantity only."""
    errors = validate_step1(
        product_name="Erbsen",
        item_type=ItemType.HOMEMADE_FROZEN,
        quantity=-5.0,
        unit="L",
    )
    assert len(errors) == 1
    assert "quantity" in errors
    assert errors["quantity"] == "Menge muss größer als 0 sein"


def test_is_step1_valid_returns_true_when_valid() -> None:
    """Test is_step1_valid returns True for valid inputs."""
    assert (
        is_step1_valid(
            product_name="Kartoffeln",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=2000.0,
            unit="kg",
        )
        is True
    )


def test_is_step1_valid_returns_false_when_invalid() -> None:
    """Test is_step1_valid returns False for invalid inputs."""
    assert (
        is_step1_valid(
            product_name="",
            item_type=None,
            quantity=0,
        )
        is False
    )


def test_is_step1_valid_returns_false_with_one_error() -> None:
    """Test is_step1_valid returns False with just one error."""
    assert (
        is_step1_valid(
            product_name="OK",
            item_type=ItemType.PURCHASED_FRESH,
            quantity=0,  # Invalid
        )
        is False
    )


# Step 2 Validation Tests


def test_validate_best_before_date_valid() -> None:
    """Test valid best before dates."""
    from app.ui.validation import validate_best_before_date
    from datetime import date
    from datetime import timedelta

    assert validate_best_before_date(date.today()) is None
    assert validate_best_before_date(date.today() + timedelta(days=30)) is None
    assert validate_best_before_date(date.today() - timedelta(days=7)) is None


def test_validate_best_before_date_none() -> None:
    """Test best before date is None."""
    from app.ui.validation import validate_best_before_date

    assert validate_best_before_date(None) == "Datum erforderlich"


def test_validate_freeze_date_required_for_frozen() -> None:
    """Test freeze date required for frozen types."""
    from app.ui.validation import validate_freeze_date
    from datetime import date

    error = validate_freeze_date(None, ItemType.PURCHASED_FROZEN, date.today())
    assert error == "Einfrierdatum erforderlich für TK-Artikel"

    error = validate_freeze_date(None, ItemType.PURCHASED_THEN_FROZEN, date.today())
    assert error == "Einfrierdatum erforderlich für TK-Artikel"

    error = validate_freeze_date(None, ItemType.HOMEMADE_FROZEN, date.today())
    assert error == "Einfrierdatum erforderlich für TK-Artikel"


def test_validate_freeze_date_not_required_for_fresh() -> None:
    """Test freeze date not required for fresh types."""
    from app.ui.validation import validate_freeze_date
    from datetime import date

    error = validate_freeze_date(None, ItemType.PURCHASED_FRESH, date.today())
    assert error is None

    error = validate_freeze_date(None, ItemType.HOMEMADE_PRESERVED, date.today())
    assert error is None


def test_validate_freeze_date_cannot_be_before_best_before() -> None:
    """Test freeze date validation against best_before."""
    from app.ui.validation import validate_freeze_date
    from datetime import date

    best_before = date(2024, 1, 1)
    freeze_date_val = date(2023, 12, 1)  # Before best_before

    error = validate_freeze_date(freeze_date_val, ItemType.PURCHASED_THEN_FROZEN, best_before)
    assert error is not None
    assert "vor Produktionsdatum" in error


def test_validate_freeze_date_valid_after_best_before() -> None:
    """Test valid freeze date after best_before."""
    from app.ui.validation import validate_freeze_date
    from datetime import date

    best_before = date(2024, 1, 1)
    freeze_date_val = date(2024, 1, 15)  # After best_before

    error = validate_freeze_date(freeze_date_val, ItemType.PURCHASED_FROZEN, best_before)
    assert error is None


def test_validate_step2_all_valid_non_frozen() -> None:
    """Test Step 2 validation with all valid fields for non-frozen item."""
    from app.ui.validation import validate_step2
    from datetime import date

    errors = validate_step2(
        item_type=ItemType.PURCHASED_FRESH,
        best_before=date.today(),
        freeze_date=None,
    )
    assert errors == {}


def test_validate_step2_all_valid_frozen() -> None:
    """Test Step 2 validation with all valid fields for frozen item."""
    from app.ui.validation import validate_step2
    from datetime import date

    errors = validate_step2(
        item_type=ItemType.PURCHASED_FROZEN,
        best_before=date(2024, 1, 1),
        freeze_date=date(2024, 1, 15),
    )
    assert errors == {}


def test_validate_step2_missing_best_before() -> None:
    """Test Step 2 validation with missing best_before."""
    from app.ui.validation import validate_step2

    errors = validate_step2(
        item_type=ItemType.PURCHASED_FRESH,
        best_before=None,
        freeze_date=None,
    )
    assert "best_before" in errors
    assert errors["best_before"] == "Datum erforderlich"


def test_validate_step2_frozen_missing_freeze_date() -> None:
    """Test Step 2 validation with frozen type but missing freeze_date."""
    from app.ui.validation import validate_step2
    from datetime import date

    errors = validate_step2(
        item_type=ItemType.HOMEMADE_FROZEN,
        best_before=date.today(),
        freeze_date=None,
    )
    assert "freeze_date" in errors
    assert "erforderlich" in errors["freeze_date"]


def test_is_step2_valid_returns_true_when_valid() -> None:
    """Test is_step2_valid returns True for valid inputs."""
    from app.ui.validation import is_step2_valid
    from datetime import date

    assert (
        is_step2_valid(
            item_type=ItemType.PURCHASED_FRESH,
            best_before=date.today(),
            freeze_date=None,
        )
        is True
    )

    assert (
        is_step2_valid(
            item_type=ItemType.PURCHASED_FROZEN,
            best_before=date(2024, 1, 1),
            freeze_date=date(2024, 1, 15),
        )
        is True
    )


def test_is_step2_valid_returns_false_when_invalid() -> None:
    """Test is_step2_valid returns False for invalid inputs."""
    from app.ui.validation import is_step2_valid

    assert (
        is_step2_valid(
            item_type=ItemType.PURCHASED_FROZEN,
            best_before=None,
            freeze_date=None,
        )
        is False
    )


# Step 3 Validation Tests


def test_validate_location_valid() -> None:
    """Test valid location ID."""
    from app.ui.validation import validate_location

    assert validate_location(1) is None
    assert validate_location(42) is None


def test_validate_location_none() -> None:
    """Test location is None."""
    from app.ui.validation import validate_location

    assert validate_location(None) == "Bitte Lagerort auswählen"


def test_validate_categories_always_valid() -> None:
    """Test categories are always valid (optional field)."""
    from app.ui.validation import validate_categories

    assert validate_categories(None) is None
    assert validate_categories([]) is None
    assert validate_categories([1, 2, 3]) is None


def test_validate_step3_all_valid_no_categories() -> None:
    """Test Step 3 validation with location only."""
    from app.ui.validation import validate_step3

    errors = validate_step3(location_id=1, category_ids=None)
    assert errors == {}


def test_validate_step3_all_valid_with_categories() -> None:
    """Test Step 3 validation with location and categories."""
    from app.ui.validation import validate_step3

    errors = validate_step3(location_id=1, category_ids=[1, 2, 3])
    assert errors == {}


def test_validate_step3_missing_location() -> None:
    """Test Step 3 validation with missing location."""
    from app.ui.validation import validate_step3

    errors = validate_step3(location_id=None, category_ids=[1, 2])
    assert "location" in errors
    assert errors["location"] == "Bitte Lagerort auswählen"


def test_is_step3_valid_returns_true_when_valid() -> None:
    """Test is_step3_valid returns True for valid inputs."""
    from app.ui.validation import is_step3_valid

    assert is_step3_valid(location_id=1, category_ids=None) is True
    assert is_step3_valid(location_id=5, category_ids=[1, 2, 3]) is True


def test_is_step3_valid_returns_false_when_invalid() -> None:
    """Test is_step3_valid returns False for invalid inputs."""
    from app.ui.validation import is_step3_valid

    assert is_step3_valid(location_id=None, category_ids=None) is False
    assert is_step3_valid(location_id=None, category_ids=[1, 2]) is False
