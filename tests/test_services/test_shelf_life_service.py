"""Tests for shelf_life_service."""

from app.models import Category
from app.models import User
from app.models.category_shelf_life import StorageType
import pytest
from sqlmodel import Session


@pytest.fixture
def test_category(session: Session, test_admin: User) -> Category:
    """Create a test category."""
    category = Category(name="Fleisch", created_by=test_admin.id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


class TestCreateShelfLife:
    """Tests for create_shelf_life function."""

    def test_create_shelf_life_success(self, session: Session, test_category: Category) -> None:
        """Test creating a shelf life config."""
        from app.services import shelf_life_service

        result = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
            source_url="https://example.com/frozen",
        )

        assert result.id is not None
        assert result.category_id == test_category.id
        assert result.storage_type == StorageType.FROZEN
        assert result.months_min == 6
        assert result.months_max == 12
        assert result.source_url == "https://example.com/frozen"

    def test_create_shelf_life_without_source_url(self, session: Session, test_category: Category) -> None:
        """Test creating a shelf life config without source_url."""
        from app.services import shelf_life_service

        result = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.CHILLED,
            months_min=1,
            months_max=2,
        )

        assert result.id is not None
        assert result.source_url is None

    def test_create_shelf_life_validates_min_max(self, session: Session, test_category: Category) -> None:
        """Test that min must be <= max."""
        from app.services import shelf_life_service

        with pytest.raises(ValueError, match="months_min must be <= months_max"):
            shelf_life_service.create_shelf_life(
                session=session,
                category_id=test_category.id,
                storage_type=StorageType.FROZEN,
                months_min=12,
                months_max=6,  # Invalid: max < min
            )

    def test_create_shelf_life_duplicate_raises_error(self, session: Session, test_category: Category) -> None:
        """Test that duplicate (category_id, storage_type) raises error."""
        from app.services import shelf_life_service

        # Create first entry
        shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            shelf_life_service.create_shelf_life(
                session=session,
                category_id=test_category.id,
                storage_type=StorageType.FROZEN,
                months_min=3,
                months_max=6,
            )


class TestGetShelfLife:
    """Tests for get_shelf_life function."""

    def test_get_shelf_life_existing(self, session: Session, test_category: Category) -> None:
        """Test getting an existing shelf life config."""
        from app.services import shelf_life_service

        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        result = shelf_life_service.get_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
        )

        assert result is not None
        assert result.id == created.id

    def test_get_shelf_life_not_found(self, session: Session, test_category: Category) -> None:
        """Test getting a non-existing shelf life config."""
        from app.services import shelf_life_service

        result = shelf_life_service.get_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
        )

        assert result is None


class TestGetAllShelfLivesForCategory:
    """Tests for get_all_shelf_lives_for_category function."""

    def test_get_all_shelf_lives_empty(self, session: Session, test_category: Category) -> None:
        """Test getting shelf lives for category with none."""
        from app.services import shelf_life_service

        result = shelf_life_service.get_all_shelf_lives_for_category(
            session=session,
            category_id=test_category.id,
        )

        assert result == []

    def test_get_all_shelf_lives_multiple(self, session: Session, test_category: Category) -> None:
        """Test getting multiple shelf lives for a category."""
        from app.services import shelf_life_service

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

        result = shelf_life_service.get_all_shelf_lives_for_category(
            session=session,
            category_id=test_category.id,
        )

        assert len(result) == 2
        storage_types = {r.storage_type for r in result}
        assert storage_types == {StorageType.FROZEN, StorageType.CHILLED}


class TestUpdateShelfLife:
    """Tests for update_shelf_life function."""

    def test_update_shelf_life_months(self, session: Session, test_category: Category) -> None:
        """Test updating months_min and months_max."""
        from app.services import shelf_life_service

        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        result = shelf_life_service.update_shelf_life(
            session=session,
            id=created.id,
            months_min=3,
            months_max=9,
        )

        assert result.months_min == 3
        assert result.months_max == 9

    def test_update_shelf_life_source_url(self, session: Session, test_category: Category) -> None:
        """Test updating source_url."""
        from app.services import shelf_life_service

        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        result = shelf_life_service.update_shelf_life(
            session=session,
            id=created.id,
            source_url="https://updated.com",
        )

        assert result.source_url == "https://updated.com"

    def test_update_shelf_life_validates_min_max(self, session: Session, test_category: Category) -> None:
        """Test that update validates min <= max."""
        from app.services import shelf_life_service

        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        with pytest.raises(ValueError, match="months_min must be <= months_max"):
            shelf_life_service.update_shelf_life(
                session=session,
                id=created.id,
                months_min=15,
                months_max=10,
            )

    def test_update_shelf_life_not_found(self, session: Session) -> None:
        """Test updating non-existing shelf life raises error."""
        from app.services import shelf_life_service

        with pytest.raises(ValueError, match="not found"):
            shelf_life_service.update_shelf_life(
                session=session,
                id=9999,
                months_min=3,
            )


class TestDeleteShelfLife:
    """Tests for delete_shelf_life function."""

    def test_delete_shelf_life_success(self, session: Session, test_category: Category) -> None:
        """Test deleting a shelf life config."""
        from app.services import shelf_life_service

        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        shelf_life_service.delete_shelf_life(session=session, id=created.id)

        # Verify it's deleted
        result = shelf_life_service.get_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
        )
        assert result is None

    def test_delete_shelf_life_not_found(self, session: Session) -> None:
        """Test deleting non-existing shelf life raises error."""
        from app.services import shelf_life_service

        with pytest.raises(ValueError, match="not found"):
            shelf_life_service.delete_shelf_life(session=session, id=9999)


class TestCreateOrUpdateShelfLife:
    """Tests for create_or_update_shelf_life function (upsert)."""

    def test_create_or_update_creates_new(self, session: Session, test_category: Category) -> None:
        """Test that it creates a new entry when none exists."""
        from app.services import shelf_life_service

        result = shelf_life_service.create_or_update_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        assert result.id is not None
        assert result.months_min == 6
        assert result.months_max == 12

    def test_create_or_update_updates_existing(self, session: Session, test_category: Category) -> None:
        """Test that it updates an existing entry."""
        from app.services import shelf_life_service

        # Create initial
        created = shelf_life_service.create_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )

        # Update via create_or_update
        result = shelf_life_service.create_or_update_shelf_life(
            session=session,
            category_id=test_category.id,
            storage_type=StorageType.FROZEN,
            months_min=3,
            months_max=9,
        )

        assert result.id == created.id
        assert result.months_min == 3
        assert result.months_max == 9

    def test_create_or_update_validates_min_max(self, session: Session, test_category: Category) -> None:
        """Test validation on create_or_update."""
        from app.services import shelf_life_service

        with pytest.raises(ValueError, match="months_min must be <= months_max"):
            shelf_life_service.create_or_update_shelf_life(
                session=session,
                category_id=test_category.id,
                storage_type=StorageType.FROZEN,
                months_min=12,
                months_max=6,
            )
