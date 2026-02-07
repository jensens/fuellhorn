"""Tests for category_service."""

from app.models import Category
from app.models import User
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from app.models.item import ItemType
from app.services import category_service
import pytest
from sqlmodel import Session
from sqlmodel import select


def test_create_category(session: Session, test_admin: User) -> None:
    """Test creating a category."""
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
        color="#4CAF50",
    )

    assert category.id is not None
    assert category.name == "Gemüse"
    assert category.color == "#4CAF50"
    assert category.created_by == test_admin.id


def test_create_category_duplicate_name_fails(session: Session, test_admin: User) -> None:
    """Test that duplicate category names fail."""
    category_service.create_category(
        session=session,
        name="Fleisch",
        created_by=test_admin.id,
    )

    with pytest.raises(ValueError, match="Category with name 'Fleisch' already exists"):
        category_service.create_category(
            session=session,
            name="fleisch",  # Case-insensitive check
            created_by=test_admin.id,
        )


def test_get_all_categories(session: Session, test_admin: User) -> None:
    """Test retrieving all categories."""
    category_service.create_category(session, "Gemüse", test_admin.id)
    category_service.create_category(session, "Fleisch", test_admin.id)
    category_service.create_category(session, "Fisch", test_admin.id)

    categories = category_service.get_all_categories(session)

    assert len(categories) == 3
    assert {c.name for c in categories} == {"Gemüse", "Fleisch", "Fisch"}


def test_get_category_by_id(session: Session, test_admin: User) -> None:
    """Test retrieving a category by ID."""
    created = category_service.create_category(session, "Obst", test_admin.id, color="#FF9800")

    category = category_service.get_category(session, created.id)

    assert category.id == created.id
    assert category.name == "Obst"
    assert category.color == "#FF9800"


def test_get_category_not_found(session: Session) -> None:
    """Test that getting non-existent category raises error."""
    with pytest.raises(ValueError, match="Category with id 999 not found"):
        category_service.get_category(session, 999)


def test_update_category(session: Session, test_admin: User) -> None:
    """Test updating a category."""
    category = category_service.create_category(session, "Brot", test_admin.id)

    updated = category_service.update_category(
        session=session,
        id=category.id,
        name="Brot & Backwaren",
        color="#FFEB3B",
    )

    assert updated.id == category.id
    assert updated.name == "Brot & Backwaren"
    assert updated.color == "#FFEB3B"


def test_update_category_duplicate_name_fails(session: Session, test_admin: User) -> None:
    """Test that updating to duplicate name fails."""
    category_service.create_category(session, "Milch", test_admin.id)
    category2 = category_service.create_category(session, "Käse", test_admin.id)

    with pytest.raises(ValueError, match="Category with name 'Milch' already exists"):
        category_service.update_category(session, category2.id, name="milch")


def test_delete_category(session: Session, test_admin: User) -> None:
    """Test deleting a category."""
    category = category_service.create_category(session, "Getränke", test_admin.id)

    category_service.delete_category(session, category.id)

    # Verify it's deleted
    result = session.exec(select(Category).where(Category.id == category.id)).first()
    assert result is None


def test_delete_category_not_found(session: Session) -> None:
    """Test that deleting non-existent category raises error."""
    with pytest.raises(ValueError, match="Category with id 999 not found"):
        category_service.delete_category(session, 999)


# =============================================================================
# Sort Order Tests (Issue #146)
# =============================================================================


def test_create_category_assigns_sort_order(session: Session, test_admin: User) -> None:
    """Test that new categories get auto-assigned sort_order."""
    cat1 = category_service.create_category(session, "First", test_admin.id)
    cat2 = category_service.create_category(session, "Second", test_admin.id)
    cat3 = category_service.create_category(session, "Third", test_admin.id)

    # Each new category should get the next sort_order
    assert cat1.sort_order == 1
    assert cat2.sort_order == 2
    assert cat3.sort_order == 3


def test_get_all_categories_returns_sorted(session: Session, test_admin: User) -> None:
    """Test that get_all_categories returns categories in sort_order."""
    # Create categories (they get sort_order 1, 2, 3)
    cat1 = category_service.create_category(session, "First", test_admin.id)
    cat2 = category_service.create_category(session, "Second", test_admin.id)
    cat3 = category_service.create_category(session, "Third", test_admin.id)

    # Manually change sort_order to reverse order
    cat1.sort_order = 3
    cat2.sort_order = 1
    cat3.sort_order = 2
    session.add_all([cat1, cat2, cat3])
    session.commit()

    # Should return in sort_order: Second, Third, First
    categories = category_service.get_all_categories(session)
    assert [c.name for c in categories] == ["Second", "Third", "First"]


def test_update_category_order(session: Session, test_admin: User) -> None:
    """Test updating category order."""
    cat1 = category_service.create_category(session, "First", test_admin.id)
    cat2 = category_service.create_category(session, "Second", test_admin.id)
    cat3 = category_service.create_category(session, "Third", test_admin.id)

    # Reorder: Third, First, Second
    category_service.update_category_order(session, [cat3.id, cat1.id, cat2.id])

    # Verify new order
    categories = category_service.get_all_categories(session)
    assert [c.name for c in categories] == ["Third", "First", "Second"]
    assert categories[0].sort_order == 0
    assert categories[1].sort_order == 1
    assert categories[2].sort_order == 2


def test_update_category_order_invalid_id(session: Session, test_admin: User) -> None:
    """Test that invalid category ID raises error."""
    category_service.create_category(session, "First", test_admin.id)

    with pytest.raises(ValueError, match="Category with id 999 not found"):
        category_service.update_category_order(session, [999])


# =============================================================================
# Category Filtering and Grouping Tests (Issue #351)
# =============================================================================


def _create_category_with_shelf_life(
    session: Session,
    name: str,
    admin_id: int,
    storage_type: StorageType,
    parent_id: int | None = None,
) -> Category:
    """Helper: create a category with shelf life entry."""
    cat = Category(name=name, created_by=admin_id, parent_id=parent_id)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    sl = CategoryShelfLife(
        category_id=cat.id,  # type: ignore[arg-type]
        storage_type=storage_type,
        months_min=3,
        months_max=6,
    )
    session.add(sl)
    session.commit()
    return cat


def test_get_categories_for_frozen_returns_only_frozen(session: Session, test_admin: User) -> None:
    """Test that HOMEMADE_FROZEN only returns categories with FROZEN shelf-life."""
    admin_id = test_admin.id  # type: ignore[assignment]

    # Create FROZEN and AMBIENT categories
    _create_category_with_shelf_life(session, "Gemüse", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Fleisch", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Marmelade", admin_id, StorageType.AMBIENT)

    result = category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN)

    names = {c.name for c in result}
    assert "Gemüse" in names
    assert "Fleisch" in names
    assert "Marmelade" not in names


def test_get_categories_for_preserved_returns_only_ambient(session: Session, test_admin: User) -> None:
    """Test that HOMEMADE_PRESERVED only returns categories with AMBIENT shelf-life."""
    admin_id = test_admin.id  # type: ignore[assignment]

    _create_category_with_shelf_life(session, "Gemüse", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Marmelade", admin_id, StorageType.AMBIENT)
    _create_category_with_shelf_life(session, "Chutney", admin_id, StorageType.AMBIENT)

    result = category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_PRESERVED)

    names = {c.name for c in result}
    assert "Marmelade" in names
    assert "Chutney" in names
    assert "Gemüse" not in names


def test_get_categories_for_fresh_returns_all(session: Session, test_admin: User) -> None:
    """Test that PURCHASED_FRESH returns all leaf categories."""
    admin_id = test_admin.id  # type: ignore[assignment]

    _create_category_with_shelf_life(session, "Gemüse", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Marmelade", admin_id, StorageType.AMBIENT)
    # Category without shelf-life (fresh-only)
    fresh_cat = Category(name="Nudeln", created_by=admin_id)
    session.add(fresh_cat)
    session.commit()

    result = category_service.get_categories_for_item_type(session, ItemType.PURCHASED_FRESH)

    names = {c.name for c in result}
    assert "Gemüse" in names
    assert "Marmelade" in names
    assert "Nudeln" in names


def test_get_categories_for_purchased_frozen_returns_frozen(session: Session, test_admin: User) -> None:
    """Test that PURCHASED_FROZEN filters to FROZEN categories."""
    admin_id = test_admin.id  # type: ignore[assignment]

    _create_category_with_shelf_life(session, "Gemüse", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Marmelade", admin_id, StorageType.AMBIENT)

    result = category_service.get_categories_for_item_type(session, ItemType.PURCHASED_FROZEN)

    names = {c.name for c in result}
    assert "Gemüse" in names
    assert "Marmelade" not in names


def test_get_categories_excludes_parents(session: Session, test_admin: User) -> None:
    """Test that parent categories with children are excluded from results."""
    admin_id = test_admin.id  # type: ignore[assignment]

    # Create parent + children
    parent = _create_category_with_shelf_life(session, "Fleisch", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Rindfleisch", admin_id, StorageType.FROZEN, parent_id=parent.id)
    _create_category_with_shelf_life(session, "Schwein", admin_id, StorageType.FROZEN, parent_id=parent.id)

    result = category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN)

    names = {c.name for c in result}
    assert "Rindfleisch" in names
    assert "Schwein" in names
    assert "Fleisch" not in names  # Parent excluded


def test_get_grouped_categories_returns_correct_groups(session: Session, test_admin: User) -> None:
    """Test that grouped categories are correctly organized."""
    admin_id = test_admin.id  # type: ignore[assignment]

    # Create parent + children
    parent = _create_category_with_shelf_life(session, "Fleisch", admin_id, StorageType.FROZEN)
    _create_category_with_shelf_life(session, "Rind", admin_id, StorageType.FROZEN, parent_id=parent.id)
    _create_category_with_shelf_life(session, "Schwein", admin_id, StorageType.FROZEN, parent_id=parent.id)
    # Standalone category
    _create_category_with_shelf_life(session, "Gemüse", admin_id, StorageType.FROZEN)

    result = category_service.get_grouped_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN)

    # Should have 2 groups: "Fleisch" group and None (standalone)
    assert len(result) == 2

    # Find the Fleisch group
    fleisch_group = next((g for g in result if g[0] == "Fleisch"), None)
    assert fleisch_group is not None
    assert len(fleisch_group[1]) == 2
    assert {c.name for c in fleisch_group[1]} == {"Rind", "Schwein"}

    # Find the standalone group
    standalone_group = next((g for g in result if g[0] is None), None)
    assert standalone_group is not None
    assert len(standalone_group[1]) == 1
    assert standalone_group[1][0].name == "Gemüse"
