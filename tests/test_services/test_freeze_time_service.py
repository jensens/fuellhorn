"""Tests for freeze_time_service."""

from app.models import ItemType
from app.models import User
from app.services import category_service
from app.services import freeze_time_service
import pytest
from sqlmodel import Session


def test_create_global_freeze_time_config(session: Session, test_admin: User) -> None:
    """Test creating a global freeze time config (no category)."""
    config = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=12,
        created_by=test_admin.id,
    )

    assert config.id is not None
    assert config.category_id is None
    assert config.item_type == ItemType.FROZEN
    assert config.freeze_time_months == 12
    assert config.created_by == test_admin.id


def test_create_category_specific_freeze_time_config(
    session: Session, test_admin: User
) -> None:
    """Test creating a category-specific freeze time config."""
    category = category_service.create_category(
        session=session,
        name="Fleisch",
        created_by=test_admin.id,
    )

    config = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=6,
        created_by=test_admin.id,
        category_id=category.id,
    )

    assert config.id is not None
    assert config.category_id == category.id
    assert config.item_type == ItemType.FROZEN
    assert config.freeze_time_months == 6


def test_create_freeze_time_config_duplicate_fails(
    session: Session, test_admin: User
) -> None:
    """Test that duplicate (category_id, item_type) fails."""
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.TINNED,
        freeze_time_months=24,
        created_by=test_admin.id,
    )

    with pytest.raises(
        ValueError,
        match="Freeze time config for category_id=None and item_type=TINNED already exists",
    ):
        freeze_time_service.create_freeze_time_config(
            session=session,
            item_type=ItemType.TINNED,
            freeze_time_months=18,
            created_by=test_admin.id,
        )


def test_create_freeze_time_config_category_duplicate_fails(
    session: Session, test_admin: User
) -> None:
    """Test that duplicate category-specific config fails."""
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.CHILLED,
        freeze_time_months=3,
        created_by=test_admin.id,
        category_id=category.id,
    )

    with pytest.raises(
        ValueError,
        match=f"Freeze time config for category_id={category.id} and item_type=CHILLED already exists",
    ):
        freeze_time_service.create_freeze_time_config(
            session=session,
            item_type=ItemType.CHILLED,
            freeze_time_months=5,
            created_by=test_admin.id,
            category_id=category.id,
        )


def test_get_all_freeze_time_configs(session: Session, test_admin: User) -> None:
    """Test getting all freeze time configs."""
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=12,
        created_by=test_admin.id,
    )
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.TINNED,
        freeze_time_months=24,
        created_by=test_admin.id,
    )

    configs = freeze_time_service.get_all_freeze_time_configs(session)

    assert len(configs) == 2


def test_get_freeze_time_config(session: Session, test_admin: User) -> None:
    """Test getting a freeze time config by ID."""
    created = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.AMBIENT,
        freeze_time_months=6,
        created_by=test_admin.id,
    )

    config = freeze_time_service.get_freeze_time_config(session, created.id)

    assert config.id == created.id
    assert config.item_type == ItemType.AMBIENT


def test_get_freeze_time_config_not_found_fails(session: Session) -> None:
    """Test that getting non-existent freeze time config fails."""
    with pytest.raises(
        ValueError, match="Freeze time config with id 999 not found"
    ):
        freeze_time_service.get_freeze_time_config(session, 999)


def test_update_freeze_time_config(session: Session, test_admin: User) -> None:
    """Test updating a freeze time config."""
    created = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.JARRED,
        freeze_time_months=12,
        created_by=test_admin.id,
    )

    updated = freeze_time_service.update_freeze_time_config(
        session=session,
        id=created.id,
        freeze_time_months=18,
    )

    assert updated.freeze_time_months == 18
    assert updated.item_type == ItemType.JARRED  # Unchanged


def test_update_freeze_time_config_to_duplicate_fails(
    session: Session, test_admin: User
) -> None:
    """Test that updating to duplicate (category_id, item_type) fails."""
    category = category_service.create_category(
        session=session,
        name="Obst",
        created_by=test_admin.id,
    )

    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=12,
        created_by=test_admin.id,
        category_id=category.id,
    )
    second = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.CHILLED,
        freeze_time_months=3,
        created_by=test_admin.id,
        category_id=category.id,
    )

    with pytest.raises(
        ValueError,
        match=f"Freeze time config for category_id={category.id} and item_type=FROZEN already exists",
    ):
        freeze_time_service.update_freeze_time_config(
            session=session,
            id=second.id,
            item_type=ItemType.FROZEN,
        )


def test_delete_freeze_time_config(session: Session, test_admin: User) -> None:
    """Test deleting a freeze time config."""
    created = freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.AMBIENT,
        freeze_time_months=6,
        created_by=test_admin.id,
    )

    freeze_time_service.delete_freeze_time_config(session, created.id)

    with pytest.raises(
        ValueError, match="Freeze time config with id .* not found"
    ):
        freeze_time_service.get_freeze_time_config(session, created.id)


def test_get_freeze_time_for_item(session: Session, test_admin: User) -> None:
    """Test getting freeze time for an item (category-specific takes precedence)."""
    category = category_service.create_category(
        session=session,
        name="Fleisch",
        created_by=test_admin.id,
    )

    # Global default
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=12,
        created_by=test_admin.id,
    )

    # Category-specific override
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.FROZEN,
        freeze_time_months=6,
        created_by=test_admin.id,
        category_id=category.id,
    )

    # Should return category-specific config (6 months)
    months = freeze_time_service.get_freeze_time_for_item(
        session=session,
        item_type=ItemType.FROZEN,
        category_id=category.id,
    )

    assert months == 6


def test_get_freeze_time_for_item_falls_back_to_global(
    session: Session, test_admin: User
) -> None:
    """Test that freeze time falls back to global if no category-specific config."""
    category = category_service.create_category(
        session=session,
        name="Gemüse",
        created_by=test_admin.id,
    )

    # Only global default
    freeze_time_service.create_freeze_time_config(
        session=session,
        item_type=ItemType.CHILLED,
        freeze_time_months=3,
        created_by=test_admin.id,
    )

    # Should return global config (3 months)
    months = freeze_time_service.get_freeze_time_for_item(
        session=session,
        item_type=ItemType.CHILLED,
        category_id=category.id,
    )

    assert months == 3


def test_get_freeze_time_for_item_no_config_returns_none(
    session: Session, test_admin: User
) -> None:
    """Test that freeze time returns None if no config found."""
    category = category_service.create_category(
        session=session,
        name="Sonstiges",
        created_by=test_admin.id,
    )

    months = freeze_time_service.get_freeze_time_for_item(
        session=session,
        item_type=ItemType.AMBIENT,
        category_id=category.id,
    )

    assert months is None
