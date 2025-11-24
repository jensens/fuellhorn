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
    )
    assert errors == {}
    assert len(errors) == 0


def test_validate_step1_all_invalid() -> None:
    """Test Step 1 with all invalid fields."""
    errors = validate_step1(
        product_name="",
        item_type=None,
        quantity=0,
    )
    assert len(errors) == 3
    assert "product_name" in errors
    assert "item_type" in errors
    assert "quantity" in errors


def test_validate_step1_product_name_invalid() -> None:
    """Test Step 1 with invalid product name only."""
    errors = validate_step1(
        product_name="A",
        item_type=ItemType.PURCHASED_FROZEN,
        quantity=100.0,
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
