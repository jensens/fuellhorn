"""Tests for CategoryShelfLife model."""

from app.models import Category
from app.models import User
import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


class TestStorageType:
    """Tests for StorageType enum."""

    def test_storage_type_values(self) -> None:
        """Test that StorageType has correct values."""
        from app.models.category_shelf_life import StorageType

        assert StorageType.FROZEN.value == "frozen"
        assert StorageType.CHILLED.value == "chilled"
        assert StorageType.AMBIENT.value == "ambient"

    def test_storage_type_is_string_enum(self) -> None:
        """Test that StorageType is a string enum."""
        from app.models.category_shelf_life import StorageType

        assert isinstance(StorageType.FROZEN, str)
        assert StorageType.FROZEN == "frozen"


class TestCategoryShelfLife:
    """Tests for CategoryShelfLife model."""

    def test_create_category_shelf_life(self, session: Session, test_admin: User) -> None:
        """Test creating a CategoryShelfLife record."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType

        # Create a category first
        category = Category(
            name="Fleisch",
            created_by=test_admin.id,
        )
        session.add(category)
        session.commit()
        session.refresh(category)

        # Create CategoryShelfLife
        shelf_life = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
            source_url="https://example.com/frozen-meat",
        )
        session.add(shelf_life)
        session.commit()
        session.refresh(shelf_life)

        assert shelf_life.id is not None
        assert shelf_life.category_id == category.id
        assert shelf_life.storage_type == StorageType.FROZEN
        assert shelf_life.months_min == 6
        assert shelf_life.months_max == 12
        assert shelf_life.source_url == "https://example.com/frozen-meat"

    def test_create_category_shelf_life_without_source_url(self, session: Session, test_admin: User) -> None:
        """Test creating a CategoryShelfLife without source_url."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType

        category = Category(name="Gemüse", created_by=test_admin.id)
        session.add(category)
        session.commit()

        shelf_life = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.CHILLED,
            months_min=1,
            months_max=2,
        )
        session.add(shelf_life)
        session.commit()
        session.refresh(shelf_life)

        assert shelf_life.id is not None
        assert shelf_life.source_url is None

    def test_unique_constraint_category_storage(self, session: Session, test_admin: User) -> None:
        """Test unique constraint on (category_id, storage_type)."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType

        category = Category(name="Obst", created_by=test_admin.id)
        session.add(category)
        session.commit()

        # First entry should work
        shelf_life1 = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )
        session.add(shelf_life1)
        session.commit()

        # Duplicate should fail
        shelf_life2 = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=3,
            months_max=6,
        )
        session.add(shelf_life2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_same_category_different_storage_types(self, session: Session, test_admin: User) -> None:
        """Test that same category can have different storage types."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType

        category = Category(name="Milchprodukte", created_by=test_admin.id)
        session.add(category)
        session.commit()

        # Add entries for different storage types
        frozen = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )
        chilled = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.CHILLED,
            months_min=1,
            months_max=2,
        )
        ambient = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.AMBIENT,
            months_min=1,
            months_max=3,
        )

        session.add_all([frozen, chilled, ambient])
        session.commit()

        session.refresh(frozen)
        session.refresh(chilled)
        session.refresh(ambient)

        assert frozen.id is not None
        assert chilled.id is not None
        assert ambient.id is not None

    def test_months_min_validation(self, session: Session, test_admin: User) -> None:
        """Test that months_min field has ge=1 constraint in schema."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType
        from pydantic import ValidationError

        category = Category(name="Test", created_by=test_admin.id)
        session.add(category)
        session.commit()

        # Use model_validate to trigger Pydantic validation
        with pytest.raises(ValidationError):
            CategoryShelfLife.model_validate(
                {
                    "category_id": category.id,
                    "storage_type": StorageType.FROZEN,
                    "months_min": 0,  # Invalid: must be >= 1
                    "months_max": 12,
                }
            )

    def test_months_max_validation(self, session: Session, test_admin: User) -> None:
        """Test that months_max field has le=36 constraint in schema."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType
        from pydantic import ValidationError

        category = Category(name="Test2", created_by=test_admin.id)
        session.add(category)
        session.commit()

        # Use model_validate to trigger Pydantic validation
        with pytest.raises(ValidationError):
            CategoryShelfLife.model_validate(
                {
                    "category_id": category.id,
                    "storage_type": StorageType.FROZEN,
                    "months_min": 1,
                    "months_max": 37,  # Invalid: must be <= 36
                }
            )

    def test_all_storage_types(self, session: Session, test_admin: User) -> None:
        """Test creating entries for all storage types."""
        from app.models.category_shelf_life import CategoryShelfLife
        from app.models.category_shelf_life import StorageType

        for i, storage_type in enumerate(StorageType):
            category = Category(name=f"Category_{i}", created_by=test_admin.id)
            session.add(category)
            session.commit()

            shelf_life = CategoryShelfLife(
                category_id=category.id,
                storage_type=storage_type,
                months_min=1,
                months_max=12,
            )
            session.add(shelf_life)
            session.commit()
            session.refresh(shelf_life)

            assert shelf_life.storage_type == storage_type
