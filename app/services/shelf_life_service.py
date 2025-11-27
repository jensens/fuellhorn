"""Shelf life service - Business logic for shelf life management."""

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
    """Create shelf life config.

    Args:
        session: Database session
        category_id: Category ID
        storage_type: Storage type (frozen, chilled, ambient)
        months_min: Minimum shelf life in months (1-36)
        months_max: Maximum shelf life in months (1-36)
        source_url: Optional source URL for the data

    Returns:
        Created shelf life configuration

    Raises:
        ValueError: If months_min > months_max
    """
    if months_min > months_max:
        raise ValueError(f"months_min ({months_min}) must be <= months_max ({months_max})")

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
        storage_type: Storage type (frozen, chilled, ambient)

    Returns:
        Shelf life configuration or None if not found
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
        List of shelf life configurations for the category
    """
    return list(session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == category_id)).all())


def _get_shelf_life_by_id(session: Session, id: int) -> CategoryShelfLife:
    """Get shelf life by ID (internal helper).

    Args:
        session: Database session
        id: Shelf life ID

    Returns:
        Shelf life configuration

    Raises:
        ValueError: If shelf life not found
    """
    shelf_life = session.get(CategoryShelfLife, id)

    if not shelf_life:
        raise ValueError(f"Shelf life with id {id} not found")

    return shelf_life


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
        id: Shelf life ID
        months_min: New minimum shelf life in months (optional)
        months_max: New maximum shelf life in months (optional)
        source_url: New source URL (optional)

    Returns:
        Updated shelf life configuration

    Raises:
        ValueError: If shelf life not found or months_min > months_max
    """
    shelf_life = _get_shelf_life_by_id(session, id)

    # Determine effective values for validation
    effective_min = months_min if months_min is not None else shelf_life.months_min
    effective_max = months_max if months_max is not None else shelf_life.months_max

    if effective_min > effective_max:
        raise ValueError(f"months_min ({effective_min}) must be <= months_max ({effective_max})")

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
        id: Shelf life ID

    Raises:
        ValueError: If shelf life not found
    """
    shelf_life = _get_shelf_life_by_id(session, id)

    session.delete(shelf_life)
    session.commit()
