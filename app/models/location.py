"""Location model for storage location management."""

from datetime import datetime
from enum import Enum
from sqlmodel import Field
from sqlmodel import SQLModel


class LocationType(str, Enum):
    """Storage location type."""

    FROZEN = "frozen"
    CHILLED = "chilled"
    AMBIENT = "ambient"


class Location(SQLModel, table=True):
    """Storage location for items.

    Locations represent physical storage areas with different temperature zones.
    """

    __tablename__ = "location"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    location_type: LocationType
    color: str | None = Field(default=None)  # Hex color code (e.g., "#FF5733")
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
