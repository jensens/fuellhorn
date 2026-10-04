"""Tests: typisierte Service-Fehler mit deutschen Meldungen (Issue #382).

Vorher warfen die Services generische ``ValueError`` mit englischen Texten, und
die Dialoge parsten SQLite-spezifische ``UNIQUE constraint``-Meldungen.
"""

from app.models import SystemSettings
from app.models import User
from app.models.location import LocationType
from app.models.user import Role
from app.services import auth_service
from app.services import category_service
from app.services import location_service
from app.services import preferences_service
from app.services.errors import DuplicateNameError
from app.services.errors import ServiceValidationError
import pytest
from sqlmodel import Session
from sqlmodel import select


class TestDuplicateNameError:
    def test_is_a_value_error_with_field_and_german_message(self) -> None:
        error = DuplicateNameError("email", "a@example.com", "E-Mail-Adresse")

        assert isinstance(error, ValueError)
        assert error.field == "email"
        assert "E-Mail-Adresse 'a@example.com' ist bereits vorhanden" in str(error)


class TestUserUniqueness:
    def test_create_user_duplicate_username(self, session: Session) -> None:
        auth_service.create_user(session, username="doppelt", email="a@example.com", password="geheim-123")

        with pytest.raises(DuplicateNameError) as excinfo:
            auth_service.create_user(session, username="Doppelt", email="b@example.com", password="geheim-123")

        assert excinfo.value.field == "username"
        assert "Benutzername" in str(excinfo.value)

    def test_create_user_duplicate_email(self, session: Session) -> None:
        auth_service.create_user(session, username="eins", email="gleich@example.com", password="geheim-123")

        with pytest.raises(DuplicateNameError) as excinfo:
            auth_service.create_user(session, username="zwei", email="Gleich@example.com", password="geheim-123")

        assert excinfo.value.field == "email"
        assert "E-Mail" in str(excinfo.value)

    def test_update_user_duplicate_email(self, session: Session) -> None:
        auth_service.create_user(session, username="eins", email="eins@example.com", password="geheim-123")
        other = auth_service.create_user(session, username="zwei", email="zwei@example.com", password="geheim-123")

        with pytest.raises(DuplicateNameError) as excinfo:
            auth_service.update_user(session, other.id, email="eins@example.com")

        assert excinfo.value.field == "email"

    def test_update_user_keeping_own_email_is_fine(self, session: Session) -> None:
        user = auth_service.create_user(session, username="eins", email="eins@example.com", password="geheim-123")

        updated = auth_service.update_user(session, user.id, email="eins@example.com", role=Role.USER)

        assert updated.email == "eins@example.com"


class TestNameUniqueness:
    def test_duplicate_category_name(self, session: Session, test_admin: User) -> None:
        category_service.create_category(session, name="Gemüse", created_by=test_admin.id)

        with pytest.raises(DuplicateNameError) as excinfo:
            category_service.create_category(session, name="gemüse", created_by=test_admin.id)

        assert excinfo.value.field == "name"
        assert "Kategorie 'Gemüse' ist bereits vorhanden" in str(excinfo.value)

    def test_duplicate_location_name(self, session: Session, test_admin: User) -> None:
        location_service.create_location(
            session, name="Keller", location_type=LocationType.AMBIENT, created_by=test_admin.id
        )

        with pytest.raises(DuplicateNameError) as excinfo:
            location_service.create_location(
                session, name="keller", location_type=LocationType.AMBIENT, created_by=test_admin.id
            )

        assert excinfo.value.field == "name"
        assert "Lagerort 'Keller' ist bereits vorhanden" in str(excinfo.value)


class TestSystemSettings:
    def test_set_system_settings_writes_all_keys_at_once(self, session: Session, test_admin: User) -> None:
        preferences_service.set_system_settings(
            session, {"item_type_time_window": "15", "category_time_window": "20"}, test_admin.id
        )

        stored = {s.key: s.value for s in session.exec(select(SystemSettings)).all()}
        assert stored == {"item_type_time_window": "15", "category_time_window": "20"}

    def test_set_system_settings_rejects_inverted_expiry_thresholds(self, session: Session, test_admin: User) -> None:
        with pytest.raises(ServiceValidationError, match="Kritisch"):
            preferences_service.set_system_settings(
                session, {"expiry_critical_days": "7", "expiry_warning_days": "3"}, test_admin.id
            )

        assert session.exec(select(SystemSettings)).all() == []

    def test_set_system_settings_rejects_non_numeric_values(self, session: Session, test_admin: User) -> None:
        with pytest.raises(ServiceValidationError):
            preferences_service.set_system_settings(session, {"item_type_time_window": "abc"}, test_admin.id)
