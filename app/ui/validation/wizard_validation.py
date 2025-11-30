"""Validation logic for Item Capture Wizard."""

from datetime import date
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


def validate_unit(unit: str | None) -> str | None:
    """Validate unit selection.

    Args:
        unit: Selected unit

    Returns:
        Error message if invalid, None if valid
    """
    if unit is None:
        return "Bitte Einheit auswählen"
    return None


def validate_step1(
    product_name: str | None,
    item_type: Any,
    quantity: float | None,
    unit: str | None = None,
) -> dict[str, str]:
    """Validate all Step 1 fields.

    Args:
        product_name: Product name input
        item_type: Selected item type
        quantity: Quantity input
        unit: Selected unit

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

    if error := validate_unit(unit):
        errors["unit"] = error

    return errors


def is_step1_valid(
    product_name: str | None,
    item_type: Any,
    quantity: float | None,
    unit: str | None = None,
) -> bool:
    """Check if Step 1 is valid.

    Args:
        product_name: Product name input
        item_type: Selected item type
        quantity: Quantity input
        unit: Selected unit

    Returns:
        True if all fields are valid
    """
    return len(validate_step1(product_name, item_type, quantity, unit)) == 0


# Step 2 Validation Functions


def validate_best_before_date(best_before: date | None) -> str | None:
    """Validate best before date.

    Args:
        best_before: Best before/production date to validate

    Returns:
        Error message if invalid, None if valid
    """
    if best_before is None:
        return "Datum erforderlich"
    return None


def validate_freeze_date(
    freeze_date: date | None,
    item_type: Any,
    best_before: date | None,
) -> str | None:
    """Validate freeze date for frozen items.

    Args:
        freeze_date: Freeze date to validate
        item_type: Selected item type
        best_before: Best before date for comparison

    Returns:
        Error message if invalid, None if valid
    """
    # Import here to avoid circular dependency
    from ...models.item import ItemType

    # Only self-frozen items require freeze_date
    # PURCHASED_FROZEN has MHD on package, no freeze_date needed
    frozen_types = {
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    }

    if item_type in frozen_types:
        if freeze_date is None:
            return "Einfrierdatum erforderlich für TK-Artikel"
        # Freeze date should not be before best_before
        if best_before and freeze_date < best_before:
            return "Einfrierdatum kann nicht vor Produktionsdatum liegen"

    return None


def _requires_category(item_type: Any) -> bool:
    """Check if item type requires a category.

    Since Issue #126, category_id is always required in the database schema
    for all item types. This ensures proper categorization and enables
    future shelf-life features.

    Args:
        item_type: Selected item type (unused, kept for API compatibility)

    Returns:
        Always True - category is required for all item types
    """
    # Note: item_type parameter kept for API compatibility but unused
    _ = item_type
    return True


def validate_step2(
    item_type: Any,
    best_before: date | None,
    freeze_date: date | None,
    category_id: int | None = None,
) -> dict[str, str]:
    """Validate all Step 2 fields.

    Args:
        item_type: Selected item type
        best_before: Best before/production date
        freeze_date: Freeze date (optional, required for frozen types)
        category_id: Category ID (required for types that need shelf life calculation)

    Returns:
        Dictionary of field errors (empty if all valid)
    """
    errors: dict[str, str] = {}

    if error := validate_best_before_date(best_before):
        errors["best_before"] = error

    if error := validate_freeze_date(freeze_date, item_type, best_before):
        errors["freeze_date"] = error

    # Category is required for types that calculate shelf life from DB
    if _requires_category(item_type) and category_id is None:
        errors["category"] = "Kategorie erforderlich für Haltbarkeitsberechnung"

    return errors


def is_step2_valid(
    item_type: Any,
    best_before: date | None,
    freeze_date: date | None,
    category_id: int | None = None,
) -> bool:
    """Check if Step 2 is valid.

    Args:
        item_type: Selected item type
        best_before: Best before/production date
        freeze_date: Freeze date
        category_id: Category ID (required for types that need shelf life calculation)

    Returns:
        True if all fields are valid
    """
    return len(validate_step2(item_type, best_before, freeze_date, category_id)) == 0


def requires_category(item_type: Any) -> bool:
    """Public helper to check if item type requires category selection.

    Args:
        item_type: Selected item type

    Returns:
        True if category is required
    """
    return _requires_category(item_type)


# Step 3 Validation Functions


def validate_location(location_id: int | None) -> str | None:
    """Validate location selection.

    Args:
        location_id: Selected location ID

    Returns:
        Error message if invalid, None if valid
    """
    if location_id is None:
        return "Bitte Lagerort auswählen"
    return None


def validate_category(category_id: int | None) -> str | None:
    """Validate category selection.

    Args:
        category_id: Selected category ID

    Returns:
        Error message if invalid, None if valid
    """
    if category_id is None:
        return "Kategorie ist erforderlich"
    return None


def validate_step3(
    location_id: int | None,
) -> dict[str, str]:
    """Validate all Step 3 fields.

    Args:
        location_id: Selected location ID

    Returns:
        Dictionary of field errors (empty if all valid)
    """
    errors: dict[str, str] = {}

    if error := validate_location(location_id):
        errors["location"] = error

    return errors


def is_step3_valid(
    location_id: int | None,
) -> bool:
    """Check if Step 3 is valid.

    Args:
        location_id: Selected location ID

    Returns:
        True if all fields are valid
    """
    return len(validate_step3(location_id)) == 0
