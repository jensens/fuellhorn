"""Category model for item classification."""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class Category(SQLModel, table=True):
    """Category/Tag for item classification.

    Categories are used to classify items. Shelf life is configured
    separately per storage type in CategoryShelfLife.
    Supports one-level hierarchy via parent_id for UI grouping.
    """

    __tablename__ = "category"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    color: str | None = Field(default=None)  # Hex color code (e.g., "#FF5733")
    parent_id: int | None = Field(default=None, foreign_key="category.id")
    sort_order: int = Field(default=0)  # For drag & drop sorting
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
