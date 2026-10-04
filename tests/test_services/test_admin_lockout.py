"""Tests: Kein Aussperren des letzten Admins, keine Selbst-Degradierung (Issue #380)."""

from app.models import User
from app.models.user import Role
from app.services import auth_service
import pytest
from sqlmodel import Session


def _admin(session: Session, name: str) -> User:
    return auth_service.create_user(
        session, username=name, email=f"{name}@example.com", password="geheim-123", role=Role.ADMIN
    )


def _user(session: Session, name: str) -> User:
    return auth_service.create_user(
        session, username=name, email=f"{name}@example.com", password="geheim-123", role=Role.USER
    )


class TestSelfProtection:
    def test_admin_cannot_demote_self(self, session: Session) -> None:
        admin = _admin(session, "chef")
        _admin(session, "stellvertretung")

        with pytest.raises(ValueError, match="eigene"):
            auth_service.update_user(session, admin.id, role=Role.USER, acting_user_id=admin.id)

    def test_admin_cannot_deactivate_self(self, session: Session) -> None:
        admin = _admin(session, "chef")
        _admin(session, "stellvertretung")

        with pytest.raises(ValueError, match="eigene"):
            auth_service.update_user(session, admin.id, is_active=False, acting_user_id=admin.id)

    def test_admin_cannot_delete_self(self, session: Session) -> None:
        admin = _admin(session, "chef")
        _admin(session, "stellvertretung")

        with pytest.raises(ValueError, match="eigene"):
            auth_service.delete_user(session, admin.id, acting_user_id=admin.id)

    def test_self_edit_of_email_or_password_is_allowed(self, session: Session) -> None:
        admin = _admin(session, "chef")

        updated = auth_service.update_user(session, admin.id, email="neu@example.com", acting_user_id=admin.id)

        assert updated.email == "neu@example.com"


class TestLastAdmin:
    def test_last_active_admin_cannot_be_demoted(self, session: Session) -> None:
        admin = _admin(session, "einzig")
        actor = _user(session, "helfer")

        with pytest.raises(ValueError, match="letzte aktive Admin"):
            auth_service.update_user(session, admin.id, role=Role.USER, acting_user_id=actor.id)

    def test_last_active_admin_cannot_be_deactivated_or_deleted(self, session: Session) -> None:
        admin = _admin(session, "einzig")
        actor = _user(session, "helfer")

        with pytest.raises(ValueError, match="letzte aktive Admin"):
            auth_service.update_user(session, admin.id, is_active=False, acting_user_id=actor.id)
        with pytest.raises(ValueError, match="letzte aktive Admin"):
            auth_service.delete_user(session, admin.id, acting_user_id=actor.id)

    def test_inactive_admins_do_not_count(self, session: Session) -> None:
        admin = _admin(session, "einzig")
        dormant = _admin(session, "schlaefer")
        auth_service.update_user(session, dormant.id, is_active=False, acting_user_id=admin.id)
        actor = _user(session, "helfer")

        with pytest.raises(ValueError, match="letzte aktive Admin"):
            auth_service.update_user(session, admin.id, role=Role.USER, acting_user_id=actor.id)

    def test_demoting_an_admin_is_allowed_when_another_active_admin_remains(self, session: Session) -> None:
        admin = _admin(session, "chef")
        second = _admin(session, "stellvertretung")

        updated = auth_service.update_user(session, second.id, role=Role.USER, acting_user_id=admin.id)

        assert updated.role == Role.USER.value

    def test_guards_apply_without_acting_user_too(self, session: Session) -> None:
        """CLI/Skripte ohne handelnden Nutzer dürfen den letzten Admin ebenfalls nicht entfernen."""
        admin = _admin(session, "einzig")

        with pytest.raises(ValueError, match="letzte aktive Admin"):
            auth_service.update_user(session, admin.id, role=Role.USER)
