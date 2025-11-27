"""Tests for shelf_life_service."""

from app.models import Category
from app.models import User
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from app.services import shelf_life_service
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="test_category")
def test_category_fixture(session: Session, test_admin: User) -> Category:
    """Create a test category."""
    category = Category(
        name="Fleisch",
        created_by=test_admin.id,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def test_create_shelf_life(session: Session, test_category: Category) -> None:
    """Test creating a shelf life configuration."""
    shelf_life = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
        source_url="https://example.com/shelf-life",
    )

    assert shelf_life.id is not None
    assert shelf_life.category_id == test_category.id
    assert shelf_life.storage_type == StorageType.FROZEN
    assert shelf_life.months_min == 6
    assert shelf_life.months_max == 12
    assert shelf_life.source_url == "https://example.com/shelf-life"


def test_create_shelf_life_without_source_url(session: Session, test_category: Category) -> None:
    """Test creating a shelf life configuration without source URL."""
    shelf_life = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.CHILLED,
        months_min=1,
        months_max=2,
    )

    assert shelf_life.id is not None
    assert shelf_life.source_url is None


def test_create_shelf_life_min_greater_than_max_fails(session: Session, test_category: Category) -> None:
    """Test that creating with months_min > months_max raises error."""
    with pytest.raises(ValueError, match="months_min .* must be <= months_max"):
        shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=12,
            months_max=6,
        )


def test_create_shelf_life_equal_min_max(session: Session, test_category: Category) -> None:
    """Test creating with equal months_min and months_max."""
    shelf_life = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.AMBIENT,
        months_min=6,
        months_max=6,
    )

    assert shelf_life.months_min == 6
    assert shelf_life.months_max == 6


def test_get_shelf_life(session: Session, test_category: Category) -> None:
    """Test retrieving a shelf life by category_id and storage_type."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    shelf_life = shelf_life_service.get_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
    )

    assert shelf_life is not None
    assert shelf_life.id == created.id
    assert shelf_life.months_min == 6
    assert shelf_life.months_max == 12


def test_get_shelf_life_not_found(session: Session, test_category: Category) -> None:
    """Test that getting non-existent shelf life returns None."""
    shelf_life = shelf_life_service.get_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
    )

    assert shelf_life is None


def test_get_shelf_life_different_storage_type(session: Session, test_category: Category) -> None:
    """Test that get_shelf_life returns correct entry for storage type."""
    # Create entries for different storage types
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.CHILLED,
        months_min=1,
        months_max=2,
    )

    # Get CHILLED entry
    shelf_life = shelf_life_service.get_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.CHILLED,
    )

    assert shelf_life is not None
    assert shelf_life.storage_type == StorageType.CHILLED
    assert shelf_life.months_min == 1
    assert shelf_life.months_max == 2


def test_get_all_shelf_lives_for_category(session: Session, test_category: Category) -> None:
    """Test retrieving all shelf life configurations for a category."""
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.CHILLED,
        months_min=1,
        months_max=2,
    )
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.AMBIENT,
        months_min=3,
        months_max=6,
    )

    shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(
        session=session,
        category_id=test_category.id,
    )

    assert len(shelf_lives) == 3
    storage_types = {sl.storage_type for sl in shelf_lives}
    assert storage_types == {StorageType.FROZEN, StorageType.CHILLED, StorageType.AMBIENT}


def test_get_all_shelf_lives_for_category_empty(session: Session, test_category: Category) -> None:
    """Test that get_all_shelf_lives_for_category returns empty list if none exist."""
    shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(
        session=session,
        category_id=test_category.id,
    )

    assert shelf_lives == []


def test_get_all_shelf_lives_for_category_only_returns_matching(
    session: Session, test_admin: User, test_category: Category
) -> None:
    """Test that only shelf lives for the specified category are returned."""
    # Create another category
    other_category = Category(name="Gemüse", created_by=test_admin.id)
    session.add(other_category)
    session.commit()
    session.refresh(other_category)

    # Create shelf lives for both categories
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )
    shelf_life_service.create_shelf_life(
        session=session,
        category_id=other_category.id,
        storage_type=StorageType.FROZEN,
        months_min=9,
        months_max=18,
    )

    # Get only for test_category
    shelf_lives = shelf_life_service.get_all_shelf_lives_for_category(
        session=session,
        category_id=test_category.id,
    )

    assert len(shelf_lives) == 1
    assert shelf_lives[0].category_id == test_category.id


def test_update_shelf_life(session: Session, test_category: Category) -> None:
    """Test updating a shelf life configuration."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    updated = shelf_life_service.update_shelf_life(
        session=session,
        id=created.id,
        months_min=9,
        months_max=18,
        source_url="https://example.com/updated",
    )

    assert updated.id == created.id
    assert updated.months_min == 9
    assert updated.months_max == 18
    assert updated.source_url == "https://example.com/updated"


def test_update_shelf_life_partial(session: Session, test_category: Category) -> None:
    """Test partial update of shelf life configuration."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
        source_url="https://example.com/original",
    )

    # Update only months_max
    updated = shelf_life_service.update_shelf_life(
        session=session,
        id=created.id,
        months_max=24,
    )

    assert updated.months_min == 6  # Unchanged
    assert updated.months_max == 24  # Updated
    assert updated.source_url == "https://example.com/original"  # Unchanged


def test_update_shelf_life_not_found(session: Session) -> None:
    """Test that updating non-existent shelf life raises error."""
    with pytest.raises(ValueError, match="Shelf life with id 999 not found"):
        shelf_life_service.update_shelf_life(
            session=session,
            id=999,
            months_min=6,
        )


def test_update_shelf_life_min_greater_than_max_fails(session: Session, test_category: Category) -> None:
    """Test that updating with months_min > months_max raises error."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    with pytest.raises(ValueError, match="months_min .* must be <= months_max"):
        shelf_life_service.update_shelf_life(
            session=session,
            id=created.id,
            months_min=24,  # Greater than existing max (12)
        )


def test_update_shelf_life_new_max_less_than_existing_min_fails(session: Session, test_category: Category) -> None:
    """Test that updating months_max < existing months_min raises error."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    with pytest.raises(ValueError, match="months_min .* must be <= months_max"):
        shelf_life_service.update_shelf_life(
            session=session,
            id=created.id,
            months_max=3,  # Less than existing min (6)
        )


def test_delete_shelf_life(session: Session, test_category: Category) -> None:
    """Test deleting a shelf life configuration."""
    created = shelf_life_service.create_shelf_life(
        session=session,
        category_id=test_category.id,
        storage_type=StorageType.FROZEN,
        months_min=6,
        months_max=12,
    )

    shelf_life_service.delete_shelf_life(session=session, id=created.id)

    # Verify it's deleted
    result = session.exec(select(CategoryShelfLife).where(CategoryShelfLife.id == created.id)).first()
    assert result is None


def test_delete_shelf_life_not_found(session: Session) -> None:
    """Test that deleting non-existent shelf life raises error."""
    with pytest.raises(ValueError, match="Shelf life with id 999 not found"):
        shelf_life_service.delete_shelf_life(session=session, id=999)
