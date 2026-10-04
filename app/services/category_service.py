"""Category service - Business logic for category management."""

from ..models.category import Category
from ..models.category_shelf_life import CategoryShelfLife
from ..models.category_shelf_life import StorageType
from ..models.item import Item
from ..models.item import ItemType
from ..services.errors import DuplicateNameError
from ..services.errors import ServiceValidationError
from ..services.expiry_calculator import get_storage_type_for_item_type
from ..services.sentinels import UNSET
from ..services.sentinels import Unset
from ..services.validation import require_non_empty
from ..services.validation import validate_hex_color
from collections import defaultdict
from sqlmodel import Session
from sqlmodel import col
from sqlmodel import func
from sqlmodel import select


def _validate_parent(session: Session, category_id: int | None, parent_id: int | None) -> None:
    """Guards für die einstufige Hierarchie (Issue #395).

    - nicht sich selbst zuordnen
    - der Parent muss existieren und darf selbst keinen Parent haben (eine Ebene)
    - eine Kategorie mit Unterkategorien kann kein Kind werden
    - eine Kategorie mit Artikeln kann keine Gruppe werden (Gruppen sind nicht wählbar)
    """
    if parent_id is None:
        return
    if category_id is not None and parent_id == category_id:
        raise ServiceValidationError("Eine Kategorie kann nicht sich selbst zugeordnet werden.")
    parent = get_category(session, parent_id)
    if parent.parent_id is not None:
        raise ServiceValidationError(
            f"'{parent.name}' ist selbst eine Unterkategorie; die Hierarchie hat nur eine Ebene."
        )
    if category_id is not None:
        child_count = session.exec(
            select(func.count()).select_from(Category).where(Category.parent_id == category_id)
        ).one()
        if child_count:
            raise ServiceValidationError(
                f"Die Kategorie hat {child_count} Unterkategorien und kann nicht selbst Unterkategorie werden."
            )
    item_count = session.exec(select(func.count()).select_from(Item).where(Item.category_id == parent_id)).one()
    if item_count:
        raise ServiceValidationError(
            f"'{parent.name}' hat {item_count} Artikel und kann keine Gruppe werden; "
            "Gruppen sind beim Erfassen nicht wählbar."
        )


def create_category(
    session: Session,
    name: str,
    created_by: int,
    color: str | None = None,
    parent_id: int | None = None,
) -> Category:
    """Create a new category.

    Args:
        session: Database session
        name: Category name (case-insensitive unique)
        created_by: User ID who created the category
        color: Hex color code (e.g., "#FF5733")
        parent_id: Eltern-Kategorie (eine Ebene, Issue #395)

    Returns:
        Created category

    Raises:
        ServiceValidationError: leerer Name, ungültige Farbe oder unzulässiger Parent (Issue #383, #395)
        DuplicateNameError: If category with same name already exists
    """
    name = require_non_empty(name, "Kategoriename")
    color = validate_hex_color(color)
    _validate_parent(session, None, parent_id)

    # Check for duplicate name (case-insensitive)
    existing = session.exec(
        select(Category).where(Category.name.ilike(name))  # type: ignore
    ).first()

    if existing:
        raise DuplicateNameError("name", existing.name, "Kategorie")

    # Get next sort_order (max + 1)
    max_order = session.exec(select(func.max(Category.sort_order))).one()
    next_order = (max_order or 0) + 1

    category = Category(
        name=name,
        created_by=created_by,
        color=color,
        parent_id=parent_id,
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
    parent_id: int | None | Unset = UNSET,
) -> Category:
    """Update category.

    Args:
        session: Database session
        id: Category ID
        name: New name (case-insensitive unique)
        color: New color code
        parent_id: Eltern-Kategorie; ``UNSET`` lässt sie unverändert, ``None`` löst sie (Issue #395)

    Returns:
        Updated category

    Raises:
        ValueError: If category not found or duplicate name
    """
    category = get_category(session, id)

    if name is not None:
        name = require_non_empty(name, "Kategoriename")
    if color is not None:
        color = validate_hex_color(color)

    # Check for duplicate name if changing name
    if name and name.lower() != category.name.lower():
        existing = session.exec(
            select(Category).where(Category.name.ilike(name))  # type: ignore
        ).first()

        if existing:
            raise DuplicateNameError("name", existing.name, "Kategorie")

        category.name = name

    if color is not None:
        category.color = color

    if not isinstance(parent_id, Unset):
        _validate_parent(session, id, parent_id)
        category.parent_id = parent_id

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


def expand_category_filter(session: Session, category_ids: set[int]) -> set[int]:
    """Eltern-Kategorien im Filter stehen für alle ihre Kinder (Issue #395)."""
    if not category_ids:
        return set()
    children = session.exec(select(Category.id).where(col(Category.parent_id).in_(category_ids))).all()
    return set(category_ids) | {child_id for child_id in children if child_id is not None}


def delete_category(session: Session, id: int) -> None:
    """Löscht eine Kategorie samt ihrer Haltbarkeiten in einer Transaktion.

    Verweigert das Löschen, solange Artikel (auch entnommene) oder
    Unterkategorien die Kategorie referenzieren; vorher endete das in
    PostgreSQL in einem rohen IntegrityError nach Teillöschung (Issue #379).

    Raises:
        ValueError: Kategorie nicht gefunden oder noch referenziert.
    """
    category = get_category(session, id)

    item_count = session.exec(select(func.count()).select_from(Item).where(Item.category_id == id)).one()
    if item_count:
        raise ValueError(
            f"Kategorie '{category.name}' kann nicht gelöscht werden: {item_count} Artikel verwenden sie "
            "(auch entnommene). Bitte diese Artikel zuerst einer anderen Kategorie zuordnen."
        )

    child_count = session.exec(select(func.count()).select_from(Category).where(Category.parent_id == id)).one()
    if child_count:
        raise ValueError(
            f"Kategorie '{category.name}' kann nicht gelöscht werden: {child_count} Unterkategorie(n) hängen daran. "
            "Bitte diese zuerst löschen oder umhängen."
        )

    for shelf_life in session.exec(select(CategoryShelfLife).where(CategoryShelfLife.category_id == id)).all():
        session.delete(shelf_life)
    # Ohne Relationship kennt SQLAlchemy die Löschreihenfolge nicht: erst Haltbarkeiten
    # schreiben, dann die Kategorie, alles in derselben Transaktion
    session.flush()
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


def _get_storage_type_for_filtering(item_type: ItemType) -> StorageType | None:
    """Get storage type for category filtering.

    PURCHASED_FROZEN filters to FROZEN categories (unlike expiry calculation
    where it uses MHD directly). PURCHASED_FRESH shows all categories.
    """
    if item_type == ItemType.PURCHASED_FROZEN:
        return StorageType.FROZEN
    return get_storage_type_for_item_type(item_type)


def get_categories_for_item_type(session: Session, item_type: ItemType) -> list[Category]:
    """Get leaf categories filtered by item type.

    Returns only categories appropriate for the given item type:
    - PURCHASED_FRESH: All leaf categories
    - PURCHASED_FROZEN: Only categories with FROZEN shelf-life
    - PURCHASED_THEN_FROZEN / HOMEMADE_FROZEN: Only FROZEN shelf-life
    - HOMEMADE_PRESERVED: Only AMBIENT shelf-life

    Only returns leaf categories (those without children).
    """
    storage_type = _get_storage_type_for_filtering(item_type)

    # Get IDs of categories that have children (= parent categories)
    parent_ids_query = (
        select(Category.parent_id).where(Category.parent_id.is_not(None)).distinct()  # type: ignore[union-attr]
    )
    parent_ids = set(session.exec(parent_ids_query).all())

    if storage_type is None:
        # PURCHASED_FRESH: all leaf categories
        all_cats = session.exec(select(Category).order_by(Category.sort_order)).all()  # type: ignore[arg-type]
        return [c for c in all_cats if c.id not in parent_ids]

    # Kategorien mit eigener Haltbarkeit für den Storage-Type; Kinder erben die ihrer Eltern (#395)
    with_shelf_life = set(
        session.exec(select(CategoryShelfLife.category_id).where(CategoryShelfLife.storage_type == storage_type)).all()
    )
    all_cats = session.exec(select(Category).order_by(Category.sort_order)).all()  # type: ignore[arg-type]
    return [
        c for c in all_cats if c.id not in parent_ids and (c.id in with_shelf_life or c.parent_id in with_shelf_life)
    ]


def get_grouped_categories_for_item_type(
    session: Session, item_type: ItemType
) -> list[tuple[str | None, list[Category]]]:
    """Get categories grouped by parent for UI rendering.

    Returns a list of (group_name, categories) tuples:
    - group_name is the parent category name, or None for standalone categories
    - categories is the list of leaf categories in that group

    Groups are ordered: grouped categories first, then standalone.
    """
    leaves = get_categories_for_item_type(session, item_type)

    # Group by parent_id
    grouped: dict[int | None, list[Category]] = defaultdict(list)
    for cat in leaves:
        grouped[cat.parent_id].append(cat)

    # Build result: resolve parent names
    result: list[tuple[str | None, list[Category]]] = []
    seen_parents: set[int] = set()

    # First: categories with parents (grouped)
    for cat in leaves:
        if cat.parent_id is not None and cat.parent_id not in seen_parents:
            seen_parents.add(cat.parent_id)
            parent = session.get(Category, cat.parent_id)
            group_name = parent.name if parent else None
            result.append((group_name, grouped[cat.parent_id]))

    # Then: standalone categories (no parent)
    standalone = grouped.get(None, [])
    if standalone:
        result.append((None, standalone))

    return result
