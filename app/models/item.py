"""Item model for inventory management."""

from .freeze_time_config import ItemType
from datetime import date
from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class Item(SQLModel, table=True):
    """Item in the inventory.

    Represents a physical item with expiry tracking and categorization.
    """

    __tablename__ = "item"

    id: int | None = Field(default=None, primary_key=True)
    product_name: str = Field(index=True)
    best_before_date: date  # Date of manufacture/packaging
    freeze_date: date | None = Field(default=None)  # Date when item was frozen
    expiry_date: date  # Calculated expiry date
    quantity: float = Field(gt=0)
    unit: str  # e.g., "kg", "L", "pieces"
    item_type: ItemType
    location_id: int = Field(foreign_key="location.id")
    notes: str | None = Field(default=None)
    is_consumed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")


class ItemCategory(SQLModel, table=True):
    """Junction table for Item-Category Many-to-Many relationship."""

    __tablename__ = "item_category"

    item_id: int = Field(foreign_key="item.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
