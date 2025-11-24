"""FreezeTimeConfig model for freeze time calculation rules."""

from datetime import datetime
from enum import Enum
from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from sqlmodel import SQLModel


class ItemType(str, Enum):
    """Item type for expiry calculation.

    Based on UI_KONZEPT.md - reflects actual user workflow for food storage.
    """

    PURCHASED_FRESH = "purchased_fresh"              # Frisch eingekauft
    PURCHASED_FROZEN = "purchased_frozen"            # TK-Ware gekauft
    PURCHASED_THEN_FROZEN = "purchased_then_frozen"  # Frisch gekauft → eingefroren
    HOMEMADE_FROZEN = "homemade_frozen"              # Selbst eingefroren (Ernte/Reste)
    HOMEMADE_PRESERVED = "homemade_preserved"        # Selbst eingemacht


class FreezeTimeConfig(SQLModel, table=True):
    """Freeze time configuration for different item types.

    Defines freeze time rules either globally (category_id is null)
    or per category (category_id is set).
    """

    __tablename__ = "freeze_time_config"
    __table_args__ = (
        UniqueConstraint("category_id", "item_type", name="uq_category_item_type"),
    )

    id: int | None = Field(default=None, primary_key=True)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    item_type: ItemType
    freeze_time_months: int = Field(ge=1, le=24)  # 1-24 months
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
