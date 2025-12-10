"""Item service - Business logic for item management."""

from ..models.category import Category
from ..models.item import Item
from ..models.item import ItemType
from ..models.withdrawal import Withdrawal
from . import expiry_calculator
from . import shelf_life_service
from datetime import date
from datetime import timedelta
from sqlalchemy import func
from sqlmodel import Session
from sqlmodel import select


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
    """

    item = Item(
        product_name=product_name,
        best_before_date=best_before_date,
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
        .group_by(Withdrawal.item_id)  # type: ignore[arg-type]
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
    notes: str | None = None,
) -> Item:
    """Update item.

    Args:
        session: Database session
        id: Item ID
        product_name: New product name
        quantity: New quantity
        notes: New notes

    Returns:
        Updated item

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)

    if product_name is not None:
        item.product_name = product_name

    if quantity is not None:
        item.quantity = quantity

    if notes is not None:
        item.notes = notes

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def mark_item_consumed(session: Session, id: int, user_id: int | None = None) -> Item:
    """Mark item as consumed.

    Creates a Withdrawal entry to track when and by whom the item was consumed.

    Args:
        session: Database session
        id: Item ID
        user_id: User ID who consumed the item (for tracking)

    Returns:
        Updated item

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)

    # Create withdrawal entry for the full remaining quantity
    if user_id is not None:
        withdrawal = Withdrawal(
            item_id=item.id,
            quantity=item.quantity,
            withdrawn_by=user_id,
        )
        session.add(withdrawal)

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

    # Delete associated withdrawal entries first
    # (SQLite doesn't enforce CASCADE by default)
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


def get_items_expiring_soon(session: Session, days: int = 7) -> list[Item]:
    """Get items with best_before_date within X days.

    Note: For items that use shelf life calculation (frozen/preserved),
    this is a rough approximation. Use get_item_expiry_info() for accurate dates.

    Args:
        session: Database session
        days: Number of days to look ahead (default 7)

    Returns:
        List of items with best_before_date coming up soon
    """
    cutoff_date = date.today() + timedelta(days=days)

    return list(
        session.exec(
            select(Item).where(
                Item.best_before_date <= cutoff_date,
                Item.is_consumed.is_(False),  # type: ignore
            )
        ).all()
    )


def withdraw_partial(
    session: Session,
    item_id: int,
    withdraw_quantity: float,
    user_id: int | None = None,
) -> Item:
    """Withdraw a partial quantity from an item.

    Creates a Withdrawal entry to track the withdrawal.

    Args:
        session: Database session
        item_id: Item ID
        withdraw_quantity: Quantity to withdraw
        user_id: User ID who withdrew the item (for tracking)

    Returns:
        Updated item

    Raises:
        ValueError: If item not found, already consumed, withdraw_quantity <= 0,
                   or withdraw_quantity > available quantity
    """
    # Validate withdraw quantity is positive
    if withdraw_quantity <= 0:
        raise ValueError("Withdraw quantity must be positive")

    # Get the item (raises ValueError if not found)
    item = get_item(session, item_id)

    # Check if item is already consumed
    if item.is_consumed:
        raise ValueError("Item is already consumed")

    # Validate withdraw quantity doesn't exceed available
    if withdraw_quantity > item.quantity:
        raise ValueError(
            f"Cannot withdraw more than available. Requested: {withdraw_quantity}, Available: {item.quantity}"
        )

    # Create withdrawal entry
    if user_id is not None:
        withdrawal = Withdrawal(
            item_id=item.id,
            quantity=withdraw_quantity,
            withdrawn_by=user_id,
        )
        session.add(withdrawal)

    # Update quantity
    item.quantity = item.quantity - withdraw_quantity

    # Mark as consumed if quantity reaches zero
    if item.quantity == 0:
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
