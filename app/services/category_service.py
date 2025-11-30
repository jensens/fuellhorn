"""Category service - Business logic for category management."""

from ..models.category import Category
from sqlmodel import Session
from sqlmodel import func
from sqlmodel import select


def create_category(
    session: Session,
    name: str,
    created_by: int,
    color: str | None = None,
) -> Category:
    """Create a new category.

    Args:
        session: Database session
        name: Category name (case-insensitive unique)
        created_by: User ID who created the category
        color: Hex color code (e.g., "#FF5733")

    Returns:
        Created category

    Raises:
        ValueError: If category with same name already exists
    """
    # Check for duplicate name (case-insensitive)
    existing = session.exec(
        select(Category).where(Category.name.ilike(name))  # type: ignore
    ).first()

    if existing:
        raise ValueError(f"Category with name '{existing.name}' already exists")

    # Get next sort_order (max + 1)
    max_order = session.exec(select(func.max(Category.sort_order))).one()
    next_order = (max_order or 0) + 1

    category = Category(
        name=name,
        created_by=created_by,
        color=color,
        sort_order=next_order,
    )

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


def get_all_categories(session: Session) -> list[Category]:
    """Get all categories sorted by sort_order.

    Args:
        session: Database session

    Returns:
        List of all categories sorted by sort_order
    """
    return list(
        session.exec(select(Category).order_by(Category.sort_order)).all()  # type: ignore[arg-type]
    )


def get_category(session: Session, id: int) -> Category:
    """Get category by ID.

    Args:
        session: Database session
        id: Category ID

    Returns:
        Category

    Raises:
        ValueError: If category not found
    """
    category = session.get(Category, id)

    if not category:
        raise ValueError(f"Category with id {id} not found")

    return category


def update_category(
    session: Session,
    id: int,
    name: str | None = None,
    color: str | None = None,
) -> Category:
    """Update category.

    Args:
        session: Database session
        id: Category ID
        name: New name (case-insensitive unique)
        color: New color code

    Returns:
        Updated category

    Raises:
        ValueError: If category not found or duplicate name
    """
    category = get_category(session, id)

    # Check for duplicate name if changing name
    if name and name.lower() != category.name.lower():
        existing = session.exec(
            select(Category).where(Category.name.ilike(name))  # type: ignore
        ).first()

        if existing:
            raise ValueError(f"Category with name '{existing.name}' already exists")

        category.name = name

    if color is not None:
        category.color = color

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


def delete_category(session: Session, id: int) -> None:
    """Delete category.

    Args:
        session: Database session
        id: Category ID

    Raises:
        ValueError: If category not found
    """
    category = get_category(session, id)

    session.delete(category)
    session.commit()


def update_category_order(session: Session, category_ids: list[int]) -> None:
    """Update sort order of categories based on list order.

    Args:
        session: Database session
        category_ids: List of category IDs in desired order

    Raises:
        ValueError: If any category ID is invalid
    """
    for index, category_id in enumerate(category_ids):
        category = get_category(session, category_id)
        category.sort_order = index
        session.add(category)

    session.commit()
