"""Tests: zentrale Eingabevalidierung in den Services (Issue #383)."""

from app.models import User
from app.models.category_shelf_life import StorageType
from app.models.location import LocationType
from app.services import auth_service
from app.services import category_service
from app.services import location_service
from app.services import shelf_life_service
from app.services import validation
from app.services.errors import ServiceValidationError
import pytest
from sqlmodel import Session


class TestRules:
    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_require_non_empty_rejects_blank(self, value: str | None) -> None:
        with pytest.raises(ServiceValidationError, match="darf nicht leer sein"):
            validation.require_non_empty(value, "Name")

    def test_require_non_empty_trims(self) -> None:
        assert validation.require_non_empty("  Gemüse ", "Name") == "Gemüse"

    @pytest.mark.parametrize("value", ["a b", "ab", "x" * 51, "ü§"])
    def test_invalid_usernames(self, value: str) -> None:
        with pytest.raises(ServiceValidationError, match="Benutzername"):
            validation.validate_username(value)

    def test_valid_username_is_trimmed(self) -> None:
        assert validation.validate_username(" max.muster ") == "max.muster"

    @pytest.mark.parametrize("value", ["foo", "a@b", "@example.com", "a b@example.com"])
    def test_invalid_emails(self, value: str) -> None:
        with pytest.raises(ServiceValidationError, match="E-Mail"):
            validation.validate_email(value)

    def test_valid_email_is_trimmed(self) -> None:
        assert validation.validate_email(" max@example.com ") == "max@example.com"

    @pytest.mark.parametrize("value", ["", "1", "1234567", None, " 12345678"])
    def test_invalid_passwords(self, value: str | None) -> None:
        with pytest.raises(ServiceValidationError, match="Passwort"):
            validation.validate_password(value)

    def test_valid_password(self) -> None:
        assert validation.validate_password("geheim-123") == "geheim-123"

    @pytest.mark.parametrize("value", ["red", "#12", "#GGGGGG", "red; background:url(x)", "#FF5733; color: red"])
    def test_invalid_colors(self, value: str) -> None:
        with pytest.raises(ServiceValidationError, match="Farbe"):
            validation.validate_hex_color(value)

    def test_valid_colors(self) -> None:
        assert validation.validate_hex_color("#ff5733") == "#FF5733"
        assert validation.validate_hex_color("#abc") == "#abc"
        assert validation.validate_hex_color(None) is None
        assert validation.validate_hex_color("  ") is None

    @pytest.mark.parametrize(("months_min", "months_max"), [(0, 12), (1, 37), (12, 6), (99, 0)])
    def test_invalid_shelf_life_ranges(self, months_min: int, months_max: int) -> None:
        with pytest.raises(ServiceValidationError, match="Haltbarkeit"):
            validation.validate_shelf_life_months(months_min, months_max)

    def test_valid_shelf_life_range(self) -> None:
        assert validation.validate_shelf_life_months(1, 36) == (1, 36)


class TestServicesUseValidation:
    def test_create_user_rejects_short_password(self, session: Session) -> None:
        with pytest.raises(ServiceValidationError, match="Passwort"):
            auth_service.create_user(session, username="kurz", email="kurz@example.com", password="1")

    def test_create_user_rejects_bad_username_and_email(self, session: Session) -> None:
        with pytest.raises(ServiceValidationError, match="Benutzername"):
            auth_service.create_user(session, username="a b", email="ok@example.com", password="geheim-123")
        with pytest.raises(ServiceValidationError, match="E-Mail"):
            auth_service.create_user(session, username="okay", email="foo", password="geheim-123")

    def test_create_user_trims_username_and_email(self, session: Session) -> None:
        user = auth_service.create_user(session, username=" neu ", email=" neu@example.com ", password="geheim-123")

        assert (user.username, user.email) == ("neu", "neu@example.com")

    def test_update_user_rejects_short_password(self, session: Session) -> None:
        user = auth_service.create_user(session, username="neu", email="neu@example.com", password="geheim-123")

        with pytest.raises(ServiceValidationError, match="Passwort"):
            auth_service.update_user(session, user.id, password="kurz")

    def test_create_category_rejects_blank_name_and_bad_color(self, session: Session, test_admin: User) -> None:
        with pytest.raises(ServiceValidationError, match="leer"):
            category_service.create_category(session, name="  ", created_by=test_admin.id)
        with pytest.raises(ServiceValidationError, match="Farbe"):
            category_service.create_category(session, name="Rot", created_by=test_admin.id, color="red")

    def test_update_category_rejects_css_injection(self, session: Session, test_admin: User) -> None:
        category = category_service.create_category(session, name="Gemüse", created_by=test_admin.id)

        with pytest.raises(ServiceValidationError, match="Farbe"):
            category_service.update_category(session, category.id, color="red; background:url(x)")

    def test_create_location_rejects_blank_name(self, session: Session, test_admin: User) -> None:
        with pytest.raises(ServiceValidationError, match="leer"):
            location_service.create_location(
                session, name=" ", location_type=LocationType.CHILLED, created_by=test_admin.id
            )

    def test_shelf_life_rejects_out_of_range_months(self, session: Session, test_admin: User) -> None:
        category = category_service.create_category(session, name="Fleisch", created_by=test_admin.id)

        with pytest.raises(ServiceValidationError, match="Haltbarkeit"):
            shelf_life_service.create_shelf_life(
                session, category_id=category.id, storage_type=StorageType.FROZEN, months_min=99, months_max=0
            )
