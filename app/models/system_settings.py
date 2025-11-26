"""SystemSettings Model.

Stores system-wide settings that can be configured by admins.
Used as fallback when users don't have their own preferences.
"""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class SystemSettings(SQLModel, table=True):
    """System-wide settings (Admin-configurable).

    These settings are used as defaults when a user doesn't have
    their own preference set for a given key.

    Example keys:
    - "default_item_type_time_window" - Default time window for item type (minutes)
    - "default_category_time_window" - Default time window for categories (minutes)
    - "default_location_time_window" - Default time window for location (minutes)
    """

    __tablename__ = "system_settings"

    # Primary Key
    id: int | None = Field(default=None, primary_key=True)

    # Setting key (unique identifier)
    key: str = Field(unique=True, index=True)

    # Setting value (stored as JSON-compatible string)
    value: str

    # Audit fields
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: int = Field(foreign_key="users.id")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SystemSettings {self.key}={self.value}>"
