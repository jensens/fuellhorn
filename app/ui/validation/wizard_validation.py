"""Validation logic for Item Capture Wizard."""

from typing import Any


def validate_product_name(name: str | None) -> str | None:
    """Validate product name.

    Args:
        name: Product name to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not name or len(name.strip()) < 2:
        return "Mindestens 2 Zeichen erforderlich"
    return None


def validate_quantity(qty: float | None) -> str | None:
    """Validate quantity.

    Args:
        qty: Quantity to validate

    Returns:
        Error message if invalid, None if valid
    """
    if qty is None or qty <= 0:
        return "Menge muss größer als 0 sein"
    return None


def validate_item_type(item_type: Any) -> str | None:
    """Validate item type selection.

    Args:
        item_type: Selected item type

    Returns:
        Error message if invalid, None if valid
    """
    if item_type is None:
        return "Bitte Artikel-Typ auswählen"
    return None


def validate_step1(
    product_name: str | None,
    item_type: Any,
    quantity: float | None,
) -> dict[str, str]:
    """Validate all Step 1 fields.

    Args:
        product_name: Product name input
        item_type: Selected item type
        quantity: Quantity input

    Returns:
        Dictionary of field errors (empty if all valid)
    """
    errors: dict[str, str] = {}

    if error := validate_product_name(product_name):
        errors["product_name"] = error

    if error := validate_item_type(item_type):
        errors["item_type"] = error

    if error := validate_quantity(quantity):
        errors["quantity"] = error

    return errors


def is_step1_valid(
    product_name: str | None,
    item_type: Any,
    quantity: float | None,
) -> bool:
    """Check if Step 1 is valid.

    Args:
        product_name: Product name input
        item_type: Selected item type
        quantity: Quantity input

    Returns:
        True if all fields are valid
    """
    return len(validate_step1(product_name, item_type, quantity)) == 0
