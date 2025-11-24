"""FreezeTime service - Business logic for freeze time configuration."""

from ..models.freeze_time_config import FreezeTimeConfig
from ..models.freeze_time_config import ItemType
from sqlmodel import Session
from sqlmodel import select


def create_freeze_time_config(
    session: Session,
    item_type: ItemType,
    freeze_time_months: int,
    created_by: int,
    category_id: int | None = None,
) -> FreezeTimeConfig:
    """Create a new freeze time configuration.

    Args:
        session: Database session
        item_type: Type of item (tinned/jarred/frozen/chilled/ambient)
        freeze_time_months: Freeze time in months (1-24)
        created_by: User ID who created the config
        category_id: Optional category ID for category-specific config

    Returns:
        Created freeze time config

    Raises:
        ValueError: If config with same (category_id, item_type) already exists
    """
    # Check for duplicate (category_id, item_type)
    existing = session.exec(
        select(FreezeTimeConfig).where(
            FreezeTimeConfig.category_id == category_id,
            FreezeTimeConfig.item_type == item_type,
        )
    ).first()

    if existing:
        raise ValueError(
            f"Freeze time config for category_id={category_id} and "
            f"item_type={item_type.value.upper()} already exists"
        )

    config = FreezeTimeConfig(
        category_id=category_id,
        item_type=item_type,
        freeze_time_months=freeze_time_months,
        created_by=created_by,
    )

    session.add(config)
    session.commit()
    session.refresh(config)

    return config


def get_all_freeze_time_configs(session: Session) -> list[FreezeTimeConfig]:
    """Get all freeze time configs.

    Args:
        session: Database session

    Returns:
        List of all freeze time configs
    """
    return list(session.exec(select(FreezeTimeConfig)).all())


def get_freeze_time_config(session: Session, id: int) -> FreezeTimeConfig:
    """Get freeze time config by ID.

    Args:
        session: Database session
        id: Config ID

    Returns:
        Freeze time config

    Raises:
        ValueError: If config not found
    """
    config = session.get(FreezeTimeConfig, id)

    if not config:
        raise ValueError(f"Freeze time config with id {id} not found")

    return config


def update_freeze_time_config(
    session: Session,
    id: int,
    item_type: ItemType | None = None,
    freeze_time_months: int | None = None,
) -> FreezeTimeConfig:
    """Update freeze time config.

    Args:
        session: Database session
        id: Config ID
        item_type: New item type
        freeze_time_months: New freeze time in months

    Returns:
        Updated freeze time config

    Raises:
        ValueError: If config not found or duplicate (category_id, item_type)
    """
    config = get_freeze_time_config(session, id)

    # Check for duplicate (category_id, item_type) if changing item_type
    if item_type and item_type != config.item_type:
        existing = session.exec(
            select(FreezeTimeConfig).where(
                FreezeTimeConfig.category_id == config.category_id,
                FreezeTimeConfig.item_type == item_type,
            )
        ).first()

        if existing:
            raise ValueError(
                f"Freeze time config for category_id={config.category_id} and "
                f"item_type={item_type.value.upper()} already exists"
            )

        config.item_type = item_type

    if freeze_time_months is not None:
        config.freeze_time_months = freeze_time_months

    session.add(config)
    session.commit()
    session.refresh(config)

    return config


def delete_freeze_time_config(session: Session, id: int) -> None:
    """Delete freeze time config.

    Args:
        session: Database session
        id: Config ID

    Raises:
        ValueError: If config not found
    """
    config = get_freeze_time_config(session, id)

    session.delete(config)
    session.commit()


def get_freeze_time_for_item(
    session: Session,
    item_type: ItemType,
    category_id: int | None = None,
) -> int | None:
    """Get freeze time in months for an item.

    Looks up freeze time configuration with the following priority:
    1. Category-specific config (if category_id provided)
    2. Global default config (category_id=None)
    3. None if no config found

    Args:
        session: Database session
        item_type: Type of item
        category_id: Optional category ID

    Returns:
        Freeze time in months, or None if no config found
    """
    # Try category-specific config first
    if category_id:
        config = session.exec(
            select(FreezeTimeConfig).where(
                FreezeTimeConfig.category_id == category_id,
                FreezeTimeConfig.item_type == item_type,
            )
        ).first()

        if config:
            return config.freeze_time_months

    # Fall back to global default
    config = session.exec(
        select(FreezeTimeConfig).where(
            FreezeTimeConfig.category_id.is_(None),  # type: ignore
            FreezeTimeConfig.item_type == item_type,
        )
    ).first()

    if config:
        return config.freeze_time_months

    return None
