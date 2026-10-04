"""UI-Tests: Der angemeldete Admin kann sich nicht selbst degradieren oder deaktivieren (Issue #380)."""

from nicegui import ui
from nicegui.testing import User as TestUser


async def test_own_row_has_role_and_active_controls_disabled(logged_in_user: TestUser) -> None:
    await logged_in_user.open("/admin/users")
    logged_in_user.find(marker="edit-admin").click()
    await logged_in_user.should_see("Benutzer bearbeiten")

    role_select = logged_in_user.find(kind=ui.select, marker="edit-role").elements.pop()
    active_switch = logged_in_user.find(kind=ui.switch, marker="edit-is-active").elements.pop()

    assert role_select.enabled is False
    assert active_switch.enabled is False
    await logged_in_user.should_see("eigene Rolle")


async def test_other_users_row_keeps_controls_enabled(logged_in_user: TestUser, standard_users) -> None:
    await logged_in_user.open("/admin/users")
    logged_in_user.find(marker="edit-testuser1").click()
    await logged_in_user.should_see("Benutzer bearbeiten")

    role_select = logged_in_user.find(kind=ui.select, marker="edit-role").elements.pop()
    active_switch = logged_in_user.find(kind=ui.switch, marker="edit-is-active").elements.pop()

    assert role_select.enabled is True
    assert active_switch.enabled is True
