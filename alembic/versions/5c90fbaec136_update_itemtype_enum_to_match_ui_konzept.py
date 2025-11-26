"""update ItemType enum to match UI_KONZEPT

Revision ID: 5c90fbaec136
Revises: 4a9f912e1477
Create Date: 2025-11-24 17:17:24.232002

"""

from typing import Sequence
from typing import Union


# revision identifiers, used by Alembic.
revision: str = "5c90fbaec136"
down_revision: Union[str, Sequence[str], None] = "4a9f912e1477"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Note: This migration updates ItemType enum values from:
      - TINNED, JARRED, FROZEN, CHILLED, AMBIENT
    To:
      - PURCHASED_FRESH, PURCHASED_FROZEN, PURCHASED_THEN_FROZEN,
        HOMEMADE_FROZEN, HOMEMADE_PRESERVED

    For SQLite: No migration needed as enums are stored as strings.
    For PostgreSQL: Would require creating new enum type and migrating data.

    Since this is early development with no production data, we skip the actual
    column alteration. The code changes are sufficient for new databases.
    """
    # Skip for SQLite (stores enums as strings anyway)
    # For PostgreSQL with existing data, this would need manual migration
    pass


def downgrade() -> None:
    """Downgrade schema.

    Cannot automatically downgrade enum value changes.
    This would require manual data migration.
    """
    pass
