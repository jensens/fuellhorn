"""Shelf life service - Business logic for CategoryShelfLife management."""

from ..models.category_shelf_life import CategoryShelfLife
from ..models.category_shelf_life import StorageType
from sqlmodel import Session
from sqlmodel import select


def create_shelf_life(
    session: Session,
    category_id: int,
    storage_type: StorageType,
    months_min: int,
    months_max: int,
    source_url: str | None = None,
) -> CategoryShelfLife:
    """Create shelf life config. Validates min <= max.

    Args:
        session: Database session
        category_id: Category ID
        storage_type: Storage type (frozen, chilled, ambient)
        months_min: Minimum shelf life in months (1-36)
        months_max: Maximum shelf life in months (1-36)
        source_url: Optional source URL for the information

    Returns:
        Created CategoryShelfLife

    Raises:
        ValueError: If months_min > months_max or duplicate exists
    """
    # Validate min <= max
    if months_min > months_max:
        raise ValueError("months_min must be <= months_max")

    # Check for duplicate
    existing = session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category_id,
            CategoryShelfLife.storage_type == storage_type,
        )
    ).first()

    if existing:
        raise ValueError(
            f"Shelf life for category_id={category_id} and storage_type={storage_type.value} already exists"
        )

    shelf_life = CategoryShelfLife(
        category_id=category_id,
        storage_type=storage_type,
        months_min=months_min,
        months_max=months_max,
        source_url=source_url,
    )

    session.add(shelf_life)
    session.commit()
    session.refresh(shelf_life)

    return shelf_life


def get_shelf_life(
    session: Session,
    category_id: int,
    storage_type: StorageType,
) -> CategoryShelfLife | None:
    """Get shelf life for category and storage type.

    Args:
        session: Database session
        category_id: Category ID
        storage_type: Storage type

    Returns:
        CategoryShelfLife or None if not found
    """
    return session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category_id,
            CategoryShelfLife.storage_type == storage_type,
        )
    ).first()


def get_all_shelf_lives_for_category(
    session: Session,
    category_id: int,
) -> list[CategoryShelfLife]:
    """Get all shelf life configs for a category.

    Args:
        session: Database session
        category_id: Category ID

    Returns:
        List of CategoryShelfLife for the category
    """
    return list(
        session.exec(
            select(CategoryShelfLife).where(
                CategoryShelfLife.category_id == category_id,
            )
        ).all()
    )


def update_shelf_life(
    session: Session,
    id: int,
    months_min: int | None = None,
    months_max: int | None = None,
    source_url: str | None = None,
) -> CategoryShelfLife:
    """Update shelf life config.

    Args:
        session: Database session
        id: Shelf life config ID
        months_min: New minimum months (optional)
        months_max: New maximum months (optional)
        source_url: New source URL (optional)

    Returns:
        Updated CategoryShelfLife

    Raises:
        ValueError: If not found or validation fails
    """
    shelf_life = session.get(CategoryShelfLife, id)

    if not shelf_life:
        raise ValueError(f"Shelf life with id {id} not found")

    # Apply updates
    new_min = months_min if months_min is not None else shelf_life.months_min
    new_max = months_max if months_max is not None else shelf_life.months_max

    # Validate min <= max
    if new_min > new_max:
        raise ValueError("months_min must be <= months_max")

    if months_min is not None:
        shelf_life.months_min = months_min
    if months_max is not None:
        shelf_life.months_max = months_max
    if source_url is not None:
        shelf_life.source_url = source_url

    session.add(shelf_life)
    session.commit()
    session.refresh(shelf_life)

    return shelf_life


def delete_shelf_life(session: Session, id: int) -> None:
    """Delete shelf life config.

    Args:
        session: Database session
        id: Shelf life config ID

    Raises:
        ValueError: If not found
    """
    shelf_life = session.get(CategoryShelfLife, id)

    if not shelf_life:
        raise ValueError(f"Shelf life with id {id} not found")

    session.delete(shelf_life)
    session.commit()


def create_or_update_shelf_life(
    session: Session,
    category_id: int,
    storage_type: StorageType,
    months_min: int,
    months_max: int,
    source_url: str | None = None,
) -> CategoryShelfLife:
    """Create or update shelf life config (upsert).

    If a config for the category and storage type exists, update it.
    Otherwise, create a new one.

    Args:
        session: Database session
        category_id: Category ID
        storage_type: Storage type
        months_min: Minimum months
        months_max: Maximum months
        source_url: Optional source URL

    Returns:
        Created or updated CategoryShelfLife

    Raises:
        ValueError: If validation fails
    """
    # Validate min <= max
    if months_min > months_max:
        raise ValueError("months_min must be <= months_max")

    # Check for existing
    existing = get_shelf_life(session, category_id, storage_type)

    if existing:
        # Update existing
        existing.months_min = months_min
        existing.months_max = months_max
        if source_url is not None:
            existing.source_url = source_url

        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new
        return create_shelf_life(
            session=session,
            category_id=category_id,
            storage_type=storage_type,
            months_min=months_min,
            months_max=months_max,
            source_url=source_url,
        )
