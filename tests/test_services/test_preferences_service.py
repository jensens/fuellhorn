"""Tests for Preferences Service.

Tests the preference hierarchy:
1. User-Einstellung > 2. System-Default > 3. Hardcoded Default
"""

from app.models.system_settings import SystemSettings
from app.models.user import Role
from app.models.user import User
from app.services import preferences_service
from collections.abc import Generator
from datetime import datetime
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create In-Memory SQLite session for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_admin")
def test_admin_fixture(session: Session) -> User:
    """Create admin test user."""
    user = User(
        username="admin",
        email="admin@example.com",
        is_active=True,
        role=Role.ADMIN.value,
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create regular test user."""
    user = User(
        username="user",
        email="user@example.com",
        is_active=True,
        role=Role.USER.value,
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestPreferencesService:
    """Tests for preferences service."""

    def test_get_preference_returns_hardcoded_default_when_no_settings(self, session: Session, test_user: User) -> None:
        """Test: Returns hardcoded default when no user or system settings exist."""
        # User has no preferences, no system settings exist
        value = preferences_service.get_preference(
            session=session,
            user=test_user,
            key="item_type_time_window",
            hardcoded_default=30,
        )

        assert value == 30

    def test_get_preference_returns_system_default_when_no_user_setting(
        self, session: Session, test_user: User, test_admin: User
    ) -> None:
        """Test: Returns system default when user has no preference."""
        # Create system setting
        system_setting = SystemSettings(
            key="item_type_time_window",
            value="45",
            updated_by=test_admin.id,
        )
        session.add(system_setting)
        session.commit()

        # User has no preferences
        value = preferences_service.get_preference(
            session=session,
            user=test_user,
            key="item_type_time_window",
            hardcoded_default=30,
        )

        assert value == 45

    def test_get_preference_returns_user_setting_over_system_default(
        self, session: Session, test_user: User, test_admin: User
    ) -> None:
        """Test: User preference takes precedence over system default."""
        # Create system setting
        system_setting = SystemSettings(
            key="item_type_time_window",
            value="45",
            updated_by=test_admin.id,
        )
        session.add(system_setting)
        session.commit()

        # Set user preference
        test_user.preferences = {"item_type_time_window": 60}
        session.add(test_user)
        session.commit()

        value = preferences_service.get_preference(
            session=session,
            user=test_user,
            key="item_type_time_window",
            hardcoded_default=30,
        )

        assert value == 60

    def test_set_user_preference(self, session: Session, test_user: User) -> None:
        """Test: Set user preference."""
        preferences_service.set_user_preference(
            session=session,
            user=test_user,
            key="item_type_time_window",
            value=45,
        )

        session.refresh(test_user)
        assert test_user.preferences is not None
        assert test_user.preferences["item_type_time_window"] == 45

    def test_set_user_preference_preserves_other_preferences(self, session: Session, test_user: User) -> None:
        """Test: Setting one preference preserves others."""
        # Set initial preference
        test_user.preferences = {"category_time_window": 30}
        session.add(test_user)
        session.commit()

        # Set another preference
        preferences_service.set_user_preference(
            session=session,
            user=test_user,
            key="item_type_time_window",
            value=45,
        )

        session.refresh(test_user)
        assert test_user.preferences["category_time_window"] == 30
        assert test_user.preferences["item_type_time_window"] == 45

    def test_get_system_setting(self, session: Session, test_admin: User) -> None:
        """Test: Get system setting by key."""
        system_setting = SystemSettings(
            key="item_type_time_window",
            value="45",
            updated_by=test_admin.id,
        )
        session.add(system_setting)
        session.commit()

        result = preferences_service.get_system_setting(session, "item_type_time_window")

        assert result is not None
        assert result.value == "45"

    def test_get_system_setting_returns_none_when_not_found(self, session: Session) -> None:
        """Test: Returns None when system setting not found."""
        result = preferences_service.get_system_setting(session, "nonexistent_key")
        assert result is None

    def test_set_system_setting_creates_new(self, session: Session, test_admin: User) -> None:
        """Test: Set system setting creates new entry."""
        preferences_service.set_system_setting(
            session=session,
            key="item_type_time_window",
            value="45",
            updated_by_id=test_admin.id,
        )

        result = preferences_service.get_system_setting(session, "item_type_time_window")
        assert result is not None
        assert result.value == "45"
        assert result.updated_by == test_admin.id

    def test_set_system_setting_updates_existing(self, session: Session, test_admin: User) -> None:
        """Test: Set system setting updates existing entry."""
        # Create initial setting
        system_setting = SystemSettings(
            key="item_type_time_window",
            value="30",
            updated_by=test_admin.id,
        )
        session.add(system_setting)
        session.commit()

        # Update setting
        preferences_service.set_system_setting(
            session=session,
            key="item_type_time_window",
            value="60",
            updated_by_id=test_admin.id,
        )

        result = preferences_service.get_system_setting(session, "item_type_time_window")
        assert result is not None
        assert result.value == "60"

    def test_get_all_user_preferences(self, session: Session, test_user: User) -> None:
        """Test: Get all user preferences with defaults."""
        test_user.preferences = {"item_type_time_window": 45}
        session.add(test_user)
        session.commit()

        prefs = preferences_service.get_all_user_preferences(session, test_user)

        assert prefs["item_type_time_window"] == 45
        # Should have defaults for other settings
        assert "category_time_window" in prefs
        assert "location_time_window" in prefs


class TestPasswordChange:
    """Tests for password change functionality."""

    def test_change_password_success(self, session: Session, test_user: User) -> None:
        """Test: Password change with correct current password."""
        result = preferences_service.change_user_password(
            session=session,
            user=test_user,
            current_password="password123",
            new_password="newpassword456",
        )

        assert result is True
        session.refresh(test_user)
        assert test_user.check_password("newpassword456")

    def test_change_password_wrong_current_password(self, session: Session, test_user: User) -> None:
        """Test: Password change fails with wrong current password."""
        result = preferences_service.change_user_password(
            session=session,
            user=test_user,
            current_password="wrongpassword",
            new_password="newpassword456",
        )

        assert result is False
        session.refresh(test_user)
        # Password should not have changed
        assert test_user.check_password("password123")

    def test_change_password_too_short(self, session: Session, test_user: User) -> None:
        """Test: Password change fails when new password is too short."""
        with pytest.raises(ValueError, match="mindestens 8 Zeichen"):
            preferences_service.change_user_password(
                session=session,
                user=test_user,
                current_password="password123",
                new_password="short",
            )


class TestEmailChange:
    """Tests for email change functionality."""

    def test_change_email_success(self, session: Session, test_user: User) -> None:
        """Test: Email change successful."""
        result = preferences_service.change_user_email(
            session=session,
            user=test_user,
            new_email="newemail@example.com",
        )

        assert result is True
        session.refresh(test_user)
        assert test_user.email == "newemail@example.com"

    def test_change_email_invalid_format(self, session: Session, test_user: User) -> None:
        """Test: Email change fails with invalid format."""
        with pytest.raises(ValueError, match="ungültige E-Mail"):
            preferences_service.change_user_email(
                session=session,
                user=test_user,
                new_email="not-an-email",
            )

    def test_change_email_already_exists(self, session: Session, test_user: User, test_admin: User) -> None:
        """Test: Email change fails when email already exists."""
        with pytest.raises(ValueError, match="bereits vergeben"):
            preferences_service.change_user_email(
                session=session,
                user=test_user,
                new_email=test_admin.email,
            )


class TestLastItemEntryPreferences:
    """Tests for last item entry preferences (smart defaults)."""

    def test_save_last_item_entry(self, session: Session, test_user: User) -> None:
        """Test: Save last item entry to user preferences."""
        last_entry = {
            "timestamp": datetime.now().isoformat(),
            "item_type": "homemade_frozen",
            "unit": "kg",
            "location_id": 1,
            "category_ids": [1, 2],
            "best_before_date": "2025-12-31",
        }

        preferences_service.save_last_item_entry(
            session=session,
            user=test_user,
            last_entry=last_entry,
        )

        session.refresh(test_user)
        assert test_user.preferences is not None
        assert test_user.preferences["last_item_entry"] == last_entry

    def test_get_last_item_entry(self, session: Session, test_user: User) -> None:
        """Test: Get last item entry from user preferences."""
        last_entry = {
            "timestamp": datetime.now().isoformat(),
            "item_type": "homemade_frozen",
            "unit": "kg",
            "location_id": 1,
            "category_ids": [1, 2],
            "best_before_date": "2025-12-31",
        }
        test_user.preferences = {"last_item_entry": last_entry}
        session.add(test_user)
        session.commit()

        result = preferences_service.get_last_item_entry(session, test_user)

        assert result == last_entry

    def test_get_last_item_entry_returns_none_when_not_set(self, session: Session, test_user: User) -> None:
        """Test: Returns None when no last item entry."""
        result = preferences_service.get_last_item_entry(session, test_user)
        assert result is None
