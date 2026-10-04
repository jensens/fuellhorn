"""Item service - Business logic for item management."""

from ..models.category import Category
from ..models.item import Item
from ..models.item import ItemType
from ..models.location import LocationType
from ..models.withdrawal import Withdrawal
from . import expiry_calculator
from . import shelf_life_service
from .category_service import get_category
from .errors import ServiceValidationError
from .location_service import get_location
from .location_service import get_valid_location_types
from .validation import require_non_empty
from datetime import date
from sqlalchemy import func
from sqlmodel import Session
from sqlmodel import select


ITEM_TYPE_LABELS: dict[ItemType, str] = {
    ItemType.PURCHASED_FRESH: "Frisch eingekauft",
    ItemType.PURCHASED_FROZEN: "TK-Ware gekauft",
    ItemType.PURCHASED_THEN_FROZEN: "Frisch gekauft → eingefroren",
    ItemType.HOMEMADE_FROZEN: "Selbst eingefroren",
    ItemType.HOMEMADE_PRESERVED: "Selbst eingemacht",
}
LOCATION_TYPE_LABELS: dict[LocationType, str] = {
    LocationType.FROZEN: "Gefroren",
    LocationType.CHILLED: "Gekühlt",
    LocationType.AMBIENT: "Raumtemperatur",
}
STORAGE_TYPE_LABELS = {"frozen": "Tiefkühlung", "chilled": "Kühlung", "ambient": "Raumtemperatur"}
FREEZE_DATE_REQUIRED_TYPES = {ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN}


def effective_best_before_date(item_type: ItemType, best_before_date: date, freeze_date: date | None) -> date:
    """Datums-Semantik (Issue #387): ``best_before_date`` ist je Typ MHD oder Herstellungsdatum.

    Für PURCHASED_THEN_FROZEN gibt es kein eigenes Datum: das Einfrierdatum ist das
    einzige erfasste Datum und ``best_before_date`` spiegelt es, damit Sortierung und
    Anzeige nicht auf einem stillen Erfassungstag beruhen.
    """
    if item_type == ItemType.PURCHASED_THEN_FROZEN and freeze_date is not None:
        return freeze_date
    return best_before_date


class Unset:
    """Sentinel für ``update_item``: Feld nicht übergeben (Issue #386).

    Nullable-Felder (``notes``, ``freeze_date``, ``category_id``) brauchen den
    Unterschied zwischen "nicht angefasst" und "auf None setzen"; mit ``None``
    als Default ließen sie sich nie leeren.
    """

    def __repr__(self) -> str:
        return "UNSET"


UNSET = Unset()


def validate_item_data(
    session: Session,
    *,
    product_name: str | None,
    quantity: float | None,
    unit: str | None,
    item_type: ItemType,
    location_id: int | None,
    category_id: int | None,
    best_before_date: date | None,
    freeze_date: date | None,
) -> str:
    """Invarianten eines Artikels prüfen (Issue #385); liefert den getrimmten Produktnamen.

    Pydantic-Constraints wie ``Field(gt=0)`` wirken bei ``table=True`` nicht, und
    die UI-Validierung schützt weder CLI, Seed noch künftige API. Deshalb prüft
    der Service selbst:

    - Produktname und Einheit nicht leer, Menge > 0, Datum vorhanden
    - Einfrierdatum für selbst eingefrorene Artikel; bei Selbstgemachtem nicht
      vor dem Produktionsdatum
    - Lagerort existiert und seine Lagerart passt zum Artikel-Typ
    - Artikel-Typen mit Haltbarkeitsberechnung brauchen eine Kategorie mit
      passender Haltbarkeit (sonst ist kein Ablaufdatum berechenbar)

    Raises:
        ServiceValidationError: Regel verletzt (deutsche Meldung)
        ValueError: Lagerort oder Kategorie nicht gefunden
    """
    cleaned_name = require_non_empty(product_name, "Produktname")
    require_non_empty(unit, "Einheit")
    if quantity is None or not quantity > 0:
        raise ServiceValidationError("Menge muss größer als 0 sein.")
    if best_before_date is None:
        raise ServiceValidationError("Datum ist erforderlich.")

    if item_type in FREEZE_DATE_REQUIRED_TYPES and freeze_date is None:
        raise ServiceValidationError(f"Einfrierdatum ist für '{ITEM_TYPE_LABELS[item_type]}' erforderlich.")
    if item_type == ItemType.HOMEMADE_FROZEN and freeze_date is not None and freeze_date < best_before_date:
        raise ServiceValidationError("Einfrierdatum darf nicht vor dem Produktionsdatum liegen.")

    if location_id is None:
        raise ServiceValidationError("Lagerort ist erforderlich.")
    location = get_location(session, location_id)
    valid_types = get_valid_location_types(item_type)
    if location.location_type not in valid_types:
        allowed = ", ".join(LOCATION_TYPE_LABELS[t] for t in valid_types)
        raise ServiceValidationError(
            f"Lagerort '{location.name}' ({LOCATION_TYPE_LABELS[location.location_type]}) passt nicht zu "
            f"'{ITEM_TYPE_LABELS[item_type]}'. Erlaubt: {allowed}."
        )

    storage_type = expiry_calculator.get_storage_type_for_item_type(item_type)
    if category_id is None:
        if storage_type is not None:
            raise ServiceValidationError(
                f"'{ITEM_TYPE_LABELS[item_type]}' braucht eine Kategorie mit Haltbarkeit für "
                f"{STORAGE_TYPE_LABELS[storage_type.value]}."
            )
        return cleaned_name
    category = get_category(session, category_id)
    if storage_type is not None and shelf_life_service.get_shelf_life(session, category_id, storage_type) is None:
        raise ServiceValidationError(
            f"Kategorie '{category.name}' hat keine Haltbarkeit für {STORAGE_TYPE_LABELS[storage_type.value]}. "
            "Bitte eine passende Kategorie wählen."
        )
    return cleaned_name


def create_item(
    session: Session,
    product_name: str,
    best_before_date: date,
    quantity: float,
    unit: str,
    item_type: ItemType,
    location_id: int,
    created_by: int,
    category_id: int | None = None,
    freeze_date: date | None = None,
    notes: str | None = None,
) -> Item:
    """Create a new item.

    Note: expiry_date is stored as best_before_date. The actual expiry info
    should be retrieved via get_item_expiry_info() which calculates dynamically.

    Args:
        session: Database session
        product_name: Product name
        best_before_date: Best before/manufacture date
        quantity: Quantity
        unit: Unit (e.g., "kg", "L", "pieces")
        item_type: Type of item
        location_id: Location ID
        created_by: User ID who created the item
        category_id: Category ID (optional for MHD items, required for frozen/preserved)
        freeze_date: Date when item was frozen (required for FROZEN items)
        notes: Optional notes

    Returns:
        Created item

    Raises:
        ServiceValidationError: Invariante verletzt (Issue #385)
        ValueError: Lagerort oder Kategorie nicht gefunden
    """
    product_name = validate_item_data(
        session,
        product_name=product_name,
        quantity=quantity,
        unit=unit,
        item_type=item_type,
        location_id=location_id,
        category_id=category_id,
        best_before_date=best_before_date,
        freeze_date=freeze_date,
    )

    item = Item(
        product_name=product_name,
        best_before_date=effective_best_before_date(item_type, best_before_date, freeze_date),
        freeze_date=freeze_date,
        quantity=quantity,
        unit=unit,
        item_type=item_type,
        location_id=location_id,
        category_id=category_id,
        notes=notes,
        created_by=created_by,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def get_all_items(session: Session) -> list[Item]:
    """Get all items.

    Args:
        session: Database session

    Returns:
        List of all items
    """
    return list(session.exec(select(Item)).all())


def get_active_items(session: Session) -> list[Item]:
    """Get all non-consumed (active) items.

    Args:
        session: Database session

    Returns:
        List of active items sorted by best_before_date
    """
    return list(
        session.exec(
            select(Item)
            .where(Item.is_consumed.is_(False))  # type: ignore
            .order_by(Item.best_before_date)  # type: ignore[arg-type]
        ).all()
    )


def get_consumed_items(session: Session) -> list[Item]:
    """Get all items that have been (partially) withdrawn.

    Returns items that have at least one withdrawal entry,
    sorted by last withdrawal date (newest first).

    Args:
        session: Database session

    Returns:
        List of items with withdrawals, sorted by last withdrawal date descending
    """
    # Subquery to get the max withdrawal date per item
    max_withdrawal_subquery = (
        select(
            Withdrawal.item_id,
            func.max(Withdrawal.withdrawn_at).label("last_withdrawn"),
        )
        .group_by(Withdrawal.item_id)
        .subquery()
    )

    # Join items with their last withdrawal date and sort
    items_with_withdrawals = session.exec(
        select(Item)
        .join(max_withdrawal_subquery, Item.id == max_withdrawal_subquery.c.item_id)  # type: ignore[arg-type]
        .order_by(max_withdrawal_subquery.c.last_withdrawn.desc())
    ).all()

    return list(items_with_withdrawals)


def get_item(session: Session, id: int) -> Item:
    """Get item by ID.

    Args:
        session: Database session
        id: Item ID

    Returns:
        Item

    Raises:
        ValueError: If item not found
    """
    item = session.get(Item, id)

    if not item:
        raise ValueError(f"Item with id {id} not found")

    return item


def update_item(
    session: Session,
    id: int,
    product_name: str | None = None,
    quantity: float | None = None,
    unit: str | None = None,
    best_before_date: date | None = None,
    freeze_date: date | None | Unset = UNSET,
    location_id: int | None = None,
    category_id: int | None | Unset = UNSET,
    item_type: ItemType | None = None,
    notes: str | None | Unset = UNSET,
) -> Item:
    """Update item.

    Pflichtfelder: ``None`` heißt "nicht ändern". Nullable-Felder (``freeze_date``,
    ``category_id``, ``notes``): ``UNSET`` heißt "nicht ändern", ``None`` leert das
    Feld (Issue #386).

    Args:
        session: Database session
        id: Item ID
        product_name: New product name
        quantity: New quantity
        unit: New unit
        best_before_date: New best before date
        freeze_date: New freeze date
        location_id: New location ID
        category_id: New category ID
        item_type: New item type
        notes: New notes

    Returns:
        Updated item

    Raises:
        ValueError: If item not found
        ServiceValidationError: Invariante des zusammengeführten Zustands verletzt (Issue #385)
    """
    item = get_item(session, id)

    new_freeze_date = item.freeze_date if isinstance(freeze_date, Unset) else freeze_date
    new_category_id = item.category_id if isinstance(category_id, Unset) else category_id
    new_notes = item.notes if isinstance(notes, Unset) else notes

    # Zusammengeführten Zustand prüfen, bevor etwas am Objekt geändert wird
    new_item_type = item_type if item_type is not None else item.item_type
    product_name = validate_item_data(
        session,
        product_name=product_name if product_name is not None else item.product_name,
        quantity=quantity if quantity is not None else item.quantity,
        unit=unit if unit is not None else item.unit,
        item_type=new_item_type,
        location_id=location_id if location_id is not None else item.location_id,
        category_id=new_category_id,
        best_before_date=best_before_date if best_before_date is not None else item.best_before_date,
        freeze_date=new_freeze_date,
    )

    if product_name is not None:
        item.product_name = product_name

    if quantity is not None:
        item.quantity = quantity

    if unit is not None:
        item.unit = unit

    item.best_before_date = effective_best_before_date(
        new_item_type,
        best_before_date if best_before_date is not None else item.best_before_date,
        new_freeze_date,
    )

    item.freeze_date = new_freeze_date

    if location_id is not None:
        item.location_id = location_id

    item.category_id = new_category_id

    if item_type is not None:
        item.item_type = item_type

    item.notes = new_notes

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def mark_item_consumed(session: Session, id: int, user_id: int) -> Item:
    """Mark item as consumed.

    Always creates a Withdrawal entry (who, when, how much): without it the item
    would vanish from both the active list and the consumed list, which is an
    inner join on withdrawals (Issue #367). Sets quantity to 0 to ensure correct
    initial quantity calculation.

    Args:
        session: Database session
        id: Item ID
        user_id: User ID who consumed the item (required)

    Returns:
        Updated item

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)

    # Create withdrawal entry for the full remaining quantity
    withdrawal = Withdrawal(
        item_id=item.id,
        quantity=item.quantity,
        withdrawn_by=user_id,
    )
    session.add(withdrawal)

    # Set quantity to 0 (Bug #222: was missing, causing wrong initial quantity calc)
    item.quantity = 0
    item.is_consumed = True

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def delete_item(session: Session, id: int) -> None:
    """Delete item and all associated withdrawal entries.

    Args:
        session: Database session
        id: Item ID

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)

    # Entnahmen explizit löschen. Seit #378 greift ON DELETE CASCADE auch in SQLite
    # (PRAGMA foreign_keys=ON); der explizite Schritt bleibt als klare Absicht
    # und unabhängig vom Dialekt bestehen.
    withdrawals = session.exec(select(Withdrawal).where(Withdrawal.item_id == id)).all()
    for withdrawal in withdrawals:
        session.delete(withdrawal)

    session.delete(item)
    session.commit()


def get_item_category(session: Session, item_id: int) -> Category | None:
    """Get the category for an item.

    Args:
        session: Database session
        item_id: Item ID

    Returns:
        Category or None if item has no category

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, item_id)

    if item.category_id is None:
        return None

    return session.get(Category, item.category_id)


def get_items_by_location(session: Session, location_id: int) -> list[Item]:
    """Get items filtered by location.

    Args:
        session: Database session
        location_id: Location ID

    Returns:
        List of items in the location
    """
    return list(session.exec(select(Item).where(Item.location_id == location_id)).all())


QUANTITY_DECIMALS = 3
"""Auflösung von Mengen (Nachkommastellen). Mengen sind Floats; ohne Rundung erreicht
ein Restbestand nie exakt 0 und 1,0 − 0,3 − 0,3 verweigert die letzte Entnahme von 0,4
(Issue #365)."""


def normalize_quantity(value: float) -> float:
    """Rundet eine Menge auf die Auflösung und entfernt negative Nullen."""
    rounded = round(value, QUANTITY_DECIMALS)
    return 0.0 if rounded == 0 else rounded


def withdraw_partial(
    session: Session,
    item_id: int,
    withdraw_quantity: float,
    user_id: int,
) -> Item:
    """Withdraw a partial quantity from an item.

    Always creates a Withdrawal entry (Issue #367). Quantities are compared
    and stored at QUANTITY_DECIMALS resolution so float noise can neither block
    the last withdrawal nor leave a residue that keeps the item "active".

    Args:
        session: Database session
        item_id: Item ID
        withdraw_quantity: Quantity to withdraw
        user_id: User ID who withdrew the item (required)

    Returns:
        Updated item

    Raises:
        ValueError: If item not found, already consumed, withdraw_quantity <= 0
                   (after rounding), or withdraw_quantity > available quantity
    """
    withdraw_quantity = normalize_quantity(withdraw_quantity)

    # Validate withdraw quantity is positive
    if withdraw_quantity <= 0:
        raise ValueError("Withdraw quantity must be positive")

    # Get the item (raises ValueError if not found)
    item = get_item(session, item_id)

    # Check if item is already consumed
    if item.is_consumed:
        raise ValueError("Item is already consumed")

    # Validate withdraw quantity doesn't exceed available (at quantity resolution)
    remaining = normalize_quantity(item.quantity - withdraw_quantity)
    if remaining < 0:
        raise ValueError(
            f"Cannot withdraw more than available. Requested: {withdraw_quantity}, Available: {item.quantity}"
        )

    # Create withdrawal entry
    withdrawal = Withdrawal(
        item_id=item.id,
        quantity=withdraw_quantity,
        withdrawn_by=user_id,
    )
    session.add(withdrawal)

    # Update quantity
    item.quantity = remaining

    # Mark as consumed if quantity reaches zero
    if remaining == 0:
        item.is_consumed = True

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def get_item_expiry_info(
    session: Session,
    item_id: int,
) -> tuple[date | None, date | None, date | None]:
    """Get expiry information for an item.

    Returns (optimal_date, max_date, best_before_date) where:
    - For PURCHASED_FRESH, PURCHASED_FROZEN: (None, None, best_before_date)
    - For PURCHASED_THEN_FROZEN, HOMEMADE_FROZEN: (optimal, max, None) using shelf life
    - For HOMEMADE_PRESERVED: (optimal, max, None) using shelf life

    Args:
        session: Database session
        item_id: Item ID

    Returns:
        Tuple of (optimal_date, max_date, best_before_date)
        Only one of the two patterns will have values, the other will be None

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, item_id)

    # Determine storage type for this item type
    storage_type = expiry_calculator.get_storage_type_for_item_type(item.item_type)

    # If storage_type is None, this item uses MHD directly
    if storage_type is None:
        return (None, None, item.best_before_date)

    # Get shelf life config for this category and storage type
    if item.category_id is None:
        # No category - can't look up shelf life
        return (None, None, None)

    shelf_life = shelf_life_service.get_shelf_life(
        session=session,
        category_id=item.category_id,
        storage_type=storage_type,
    )

    if shelf_life is None:
        # No shelf life config for this category
        return (None, None, None)

    # Determine base date for calculation
    if item.item_type in [ItemType.PURCHASED_THEN_FROZEN, ItemType.HOMEMADE_FROZEN]:
        # Use freeze_date for frozen items
        if item.freeze_date is None:
            return (None, None, None)
        base_date = item.freeze_date
    else:
        # Use best_before_date (production date) for preserved items
        base_date = item.best_before_date

    # Calculate optimal and max dates
    optimal_date, max_date = expiry_calculator.calculate_expiry_dates(
        item_type=item.item_type,
        base_date=base_date,
        months_min=shelf_life.months_min,
        months_max=shelf_life.months_max,
    )

    return (optimal_date, max_date, None)


def get_withdrawal_history(session: Session, item_id: int) -> list[Withdrawal]:
    """Get withdrawal history for an item.

    Args:
        session: Database session
        item_id: Item ID

    Returns:
        List of Withdrawal entries sorted chronologically (oldest first)
    """
    return list(
        session.exec(
            select(Withdrawal).where(Withdrawal.item_id == item_id).order_by(Withdrawal.withdrawn_at)  # type: ignore[arg-type]
        ).all()
    )


def get_item_initial_quantity(session: Session, item_id: int) -> float:
    """Get the initial quantity of an item before any withdrawals.

    Calculates: current_quantity + sum(all withdrawals)

    Args:
        session: Database session
        item_id: Item ID

    Returns:
        Initial quantity

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, item_id)
    withdrawals = get_withdrawal_history(session, item_id)
    total_withdrawn = sum(w.quantity for w in withdrawals)
    return item.quantity + total_withdrawn


def get_recently_added_items(session: Session, limit: int = 5) -> list[Item]:
    """Get the most recently added active items.

    Args:
        session: Database session
        limit: Maximum number of items to return (default 5)

    Returns:
        List of items sorted by created_at descending (newest first)
    """
    return list(
        session.exec(
            select(Item)
            .where(Item.is_consumed.is_(False))  # type: ignore
            .order_by(Item.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        ).all()
    )


def get_item_count_by_location(session: Session) -> dict[int, int]:
    """Get count of active items per location.

    Args:
        session: Database session

    Returns:
        Dictionary mapping location_id to item count
    """
    results = session.exec(
        select(Item.location_id, func.count())
        .where(Item.is_consumed.is_(False))  # type: ignore
        .group_by(Item.location_id)
    ).all()

    return {location_id: count for location_id, count in results}


def get_item_count_by_category(session: Session) -> dict[int, int]:
    """Get count of active items per category.

    Items without a category are excluded.

    Args:
        session: Database session

    Returns:
        Dictionary mapping category_id to item count
    """
    results = session.exec(
        select(Item.category_id, func.count())
        .where(
            Item.is_consumed.is_(False),  # type: ignore
            Item.category_id.is_not(None),  # type: ignore
        )
        .group_by(Item.category_id)
    ).all()

    # category_id is guaranteed non-None due to the WHERE clause
    return {category_id: count for category_id, count in results if category_id is not None}
