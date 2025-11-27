"""CategoryShelfLife model for shelf life per category and storage type."""

from enum import Enum
from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from sqlmodel import SQLModel


class StorageType(str, Enum):
    """Storage type for shelf life calculation."""

    FROZEN = "frozen"  # Tiefgekühlt (-18°C)
    CHILLED = "chilled"  # Kühlschrank (2-8°C)
    AMBIENT = "ambient"  # Zimmertemperatur/Keller


class CategoryShelfLife(SQLModel, table=True):
    """Shelf life configuration per category and storage type."""

    __tablename__ = "category_shelf_life"
    __table_args__ = (UniqueConstraint("category_id", "storage_type", name="uq_category_storage"),)

    id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="category.id")
    storage_type: StorageType
    months_min: int = Field(ge=1, le=36)  # 1-36 Monate
    months_max: int = Field(ge=1, le=36)  # 1-36 Monate
    source_url: str | None = Field(default=None)  # Quellenangabe
