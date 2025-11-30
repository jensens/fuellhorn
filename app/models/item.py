"""Item model for inventory management."""

from datetime import date
from datetime import datetime
from enum import Enum
from sqlmodel import Field
from sqlmodel import SQLModel


class ItemType(str, Enum):
    """Item type for expiry calculation.

    Based on UI_KONZEPT.md - reflects actual user workflow for food storage.
    """

    PURCHASED_FRESH = "purchased_fresh"  # Frisch eingekauft
    PURCHASED_FROZEN = "purchased_frozen"  # TK-Ware gekauft
    PURCHASED_THEN_FROZEN = "purchased_then_frozen"  # Frisch gekauft → eingefroren
    HOMEMADE_FROZEN = "homemade_frozen"  # Selbst eingefroren (Ernte/Reste)
    HOMEMADE_PRESERVED = "homemade_preserved"  # Selbst eingemacht


class Item(SQLModel, table=True):
    """Item in the inventory.

    Represents a physical item with expiry tracking and categorization.
    Expiry is calculated dynamically based on category shelf life.
    """

    __tablename__ = "item"

    id: int | None = Field(default=None, primary_key=True)
    product_name: str = Field(index=True)
    best_before_date: date  # MHD for purchased items, production date for homemade
    freeze_date: date | None = Field(default=None)  # Date when item was frozen
    quantity: float = Field(gt=0)
    unit: str  # e.g., "kg", "L", "pieces"
    item_type: ItemType
    location_id: int = Field(foreign_key="location.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")
    notes: str | None = Field(default=None)
    is_consumed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
