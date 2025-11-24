"""UI Tests for Item Capture Wizard - Step 1.

Phase 2: Basic structure tests (auth required).
Phase 3 will add full interaction tests with login flow.
"""

from nicegui.testing import User


async def test_wizard_route_requires_auth(user: User) -> None:
    """Test that /items/add requires authentication."""
    await user.open("/items/add")
    # Should redirect to login
    await user.should_see("Benutzername")


# Phase 3: Add full interaction tests with login flow
# - test_wizard_step1_renders
# - test_step1_has_item_type_radios
# - test_step1_has_next_button
