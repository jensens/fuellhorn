"""Item service - Business logic for item management."""

from ..models.category import Category
from ..models.freeze_time_config import ItemType
from ..models.item import Item
from ..models.item import ItemCategory
from . import expiry_calculator
from . import freeze_time_service
from datetime import date
from datetime import timedelta
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
    freeze_date: date | None = None,
    notes: str | None = None,
    category_ids: list[int] | None = None,
) -> Item:
    """Create a new item with automatic expiry calculation.

    Args:
        session: Database session
        product_name: Product name
        best_before_date: Best before/manufacture date
        quantity: Quantity
        unit: Unit (e.g., "kg", "L", "pieces")
        item_type: Type of item
        location_id: Location ID
        created_by: User ID who created the item
        freeze_date: Date when item was frozen (required for FROZEN items)
        notes: Optional notes
        category_ids: Optional list of category IDs to assign

    Returns:
        Created item

    Raises:
        ValueError: If frozen item without freeze_date
    """
    # Get freeze time configuration for this item type
    freeze_time_months = freeze_time_service.get_freeze_time_for_item(
        session=session,
        item_type=item_type,
        category_id=None,  # TODO: Support category-specific freeze times
    )

    # Calculate expiry date
    expiry_date = expiry_calculator.calculate_expiry_date(
        item_type=item_type,
        best_before_date=best_before_date,
        freeze_date=freeze_date,
        freeze_time_months=freeze_time_months,
    )

    item = Item(
        product_name=product_name,
        best_before_date=best_before_date,
        freeze_date=freeze_date,
        expiry_date=expiry_date,
        quantity=quantity,
        unit=unit,
        item_type=item_type,
        location_id=location_id,
        notes=notes,
        created_by=created_by,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    # Add category associations
    if category_ids:
        for category_id in category_ids:
            item_category = ItemCategory(
                item_id=item.id,
                category_id=category_id,
            )
            session.add(item_category)

        session.commit()

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
        List of active items sorted by expiry date
    """
    return list(
        session.exec(
            select(Item)
            .where(Item.is_consumed.is_(False))  # type: ignore
            .order_by(Item.expiry_date)  # type: ignore[arg-type]
        ).all()
    )


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


def mark_item_consumed(session: Session, id: int) -> Item:
    """Mark item as consumed.

    Args:
        session: Database session
        id: Item ID

    Returns:
        Updated item

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)
    item.is_consumed = True

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


def delete_item(session: Session, id: int) -> None:
    """Delete item.

    Args:
        session: Database session
        id: Item ID

    Raises:
        ValueError: If item not found
    """
    item = get_item(session, id)

    # Delete category associations first
    session.exec(select(ItemCategory).where(ItemCategory.item_id == id)).all()
    for item_category in session.exec(select(ItemCategory).where(ItemCategory.item_id == id)).all():
        session.delete(item_category)

    session.delete(item)
    session.commit()


def get_item_categories(session: Session, item_id: int) -> list[Category]:
    """Get categories for an item.

    Args:
        session: Database session
        item_id: Item ID

    Returns:
        List of categories
    """
    item_categories = session.exec(select(ItemCategory).where(ItemCategory.item_id == item_id)).all()

    category_ids = [ic.category_id for ic in item_categories]

    return list(
        session.exec(select(Category).where(Category.id.in_(category_ids))).all()  # type: ignore
    )


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
    """Get items expiring within X days.

    Args:
        session: Database session
        days: Number of days to look ahead (default 7)

    Returns:
        List of items expiring soon
    """
    cutoff_date = date.today() + timedelta(days=days)

    return list(
        session.exec(
            select(Item).where(
                Item.expiry_date <= cutoff_date,
                Item.is_consumed.is_(False),  # type: ignore
            )
        ).all()
    )


def withdraw_partial(
    session: Session,
    item_id: int,
    withdraw_quantity: float,
) -> Item:
    """Withdraw a partial quantity from an item.

    Args:
        session: Database session
        item_id: Item ID
        withdraw_quantity: Quantity to withdraw

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

    # Update quantity
    item.quantity = item.quantity - withdraw_quantity

    # Mark as consumed if quantity reaches zero
    if item.quantity == 0:
        item.is_consumed = True

    session.add(item)
    session.commit()
    session.refresh(item)

    return item
