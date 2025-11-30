"""Category model for item classification."""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class Category(SQLModel, table=True):
    """Category/Tag for item classification.

    Categories are used to classify items. Shelf life is configured
    separately per storage type in CategoryShelfLife.
    Flat structure (no hierarchy).
    """

    __tablename__ = "category"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    color: str | None = Field(default=None)  # Hex color code (e.g., "#FF5733")
    sort_order: int = Field(default=0)  # For drag & drop sorting
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
