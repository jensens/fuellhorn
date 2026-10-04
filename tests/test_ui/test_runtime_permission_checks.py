"""UI-Tests: Mutations-Handler prüfen die Berechtigung zur Laufzeit, nicht nur beim Seitenaufbau (Issue #381).

Szenario: Admin hat /admin/users offen, wird in der Datenbank degradiert oder
deaktiviert und klickt dann eine Aktion. Vorher lief die Aktion trotzdem durch.
"""

from app.models import User
from app.models.user import Role
from app.services.auth_service import get_user_by_username
from nicegui.testing import User as TestUser
from sqlmodel import Session
from sqlmodel import select


def _set_admin(engine, *, role: Role | None = None, is_active: bool | None = None) -> None:
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.username == "admin")).one()
        if role is not None:
            admin.role = role.value
        if is_active is not None:
            admin.is_active = is_active
        session.add(admin)
        session.commit()


def _restore_admin(engine) -> None:
    _set_admin(engine, role=Role.ADMIN, is_active=True)


async def _fill_new_user_dialog(user: TestUser) -> None:
    user.find(marker="new-user-button").click()
    await user.should_see("Neuen Benutzer erstellen")
    user.find("Benutzername").type("spaeter")
    user.find("E-Mail").type("spaeter@example.com")
    user.find(marker="password-input").type("geheim-123")
    user.find(marker="password-confirm-input").type("geheim-123")


async def test_demoted_admin_cannot_create_users_anymore(logged_in_user: TestUser, isolated_test_database) -> None:
    await logged_in_user.open("/admin/users")
    await _fill_new_user_dialog(logged_in_user)

    _set_admin(isolated_test_database, role=Role.USER)
    try:
        logged_in_user.find("Speichern").click()
        await logged_in_user.should_see("Keine Berechtigung")
    finally:
        _restore_admin(isolated_test_database)

    with Session(isolated_test_database) as session:
        assert get_user_by_username(session, "spaeter") is None


async def test_deactivated_admin_cannot_create_users_anymore(logged_in_user: TestUser, isolated_test_database) -> None:
    await logged_in_user.open("/admin/users")
    await _fill_new_user_dialog(logged_in_user)

    _set_admin(isolated_test_database, is_active=False)
    try:
        logged_in_user.find("Speichern").click()
        await logged_in_user.should_see("deaktiviert")
    finally:
        _restore_admin(isolated_test_database)

    with Session(isolated_test_database) as session:
        assert get_user_by_username(session, "spaeter") is None


async def test_demoted_admin_cannot_delete_categories(
    logged_in_user: TestUser, standard_categories, isolated_test_database
) -> None:
    await logged_in_user.open("/admin/categories")
    logged_in_user.find(marker="delete-Fleisch").click()
    await logged_in_user.should_see("Kategorie löschen")

    _set_admin(isolated_test_database, role=Role.USER)
    try:
        logged_in_user.find("Löschen").click()
        await logged_in_user.should_see("Keine Berechtigung")
    finally:
        _restore_admin(isolated_test_database)

    with Session(isolated_test_database) as session:
        from app.services import category_service

        assert category_service.get_category(session, 101) is not None
