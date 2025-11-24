"""Category model for item classification."""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class Category(SQLModel, table=True):
    """Category/Tag for item classification.

    Categories are used to classify items and configure freeze times.
    Flat structure (no hierarchy).
    """

    __tablename__ = "category"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    color: str | None = Field(default=None)  # Hex color code (e.g., "#FF5733")
    freeze_time_months: int | None = Field(default=None, ge=1, le=24)  # 1-24 months
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
