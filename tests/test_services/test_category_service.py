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
        freeze_time_months=12,
    )

    assert category.id is not None
    assert category.name == "Gemüse"
    assert category.color == "#4CAF50"
    assert category.freeze_time_months == 12
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
        freeze_time_months=6,
    )

    assert updated.id == category.id
    assert updated.name == "Brot & Backwaren"
    assert updated.color == "#FFEB3B"
    assert updated.freeze_time_months == 6


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
