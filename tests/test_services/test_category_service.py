"""Tests for category_service."""

from app.models import Category
from app.models import User
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
