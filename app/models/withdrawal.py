"""Withdrawal model for tracking item withdrawals."""

from datetime import datetime
from sqlmodel import Field
from sqlmodel import SQLModel


class Withdrawal(SQLModel, table=True):
    """Tracks withdrawals (partial or complete) from inventory items.

    Each withdrawal records when, how much, and by whom an item was taken.
    Used for audit trail and history tracking.
    """

    __tablename__ = "withdrawal"

    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id", index=True, ondelete="CASCADE")
    quantity: float  # Amount withdrawn
    withdrawn_at: datetime = Field(default_factory=datetime.now)
    withdrawn_by: int = Field(foreign_key="users.id")
