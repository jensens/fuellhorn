"""Preferences Service - Manages user preferences and system defaults.

This service handles the preference hierarchy:
1. User-Einstellung > 2. System-Default > 3. Hardcoded Default

Smart Defaults are stored per-user in the database instead of browser storage,
allowing proper separation when multiple users share a device.
"""

from ..models.system_settings import SystemSettings
from ..models.user import User
from datetime import datetime
import re
from sqlmodel import Session
from sqlmodel import select
from typing import Any


# Hardcoded defaults (fallback values)
HARDCODED_DEFAULTS = {
    "item_type_time_window": 30,  # Minutes
    "category_time_window": 30,  # Minutes
    "location_time_window": 60,  # Minutes
    "expiry_critical_days": 3,  # Days before expiry for critical status
    "expiry_warning_days": 7,  # Days before expiry for warning status
}

# Minimum password length
MIN_PASSWORD_LENGTH = 8


def get_preference(
    session: Session,
    user: User,
    key: str,
    hardcoded_default: Any,
) -> Any:
    """Get a preference value with hierarchy resolution.

    Hierarchy:
    1. User-Einstellung (if set)
    2. System-Default (if set by admin)
    3. Hardcoded Default

    Args:
        session: Database session.
        user: The user to get preference for.
        key: The preference key.
        hardcoded_default: Fallback value if nothing is set.

    Returns:
        The preference value from the highest priority source.
    """
    # 1. Check user preference
    if user.preferences and key in user.preferences:
        return user.preferences[key]

    # 2. Check system setting
    system_setting = get_system_setting(session, key)
    if system_setting:
        # System settings are stored as strings, try to parse as int
        try:
            return int(system_setting.value)
        except ValueError:
            return system_setting.value

    # 3. Return hardcoded default
    return hardcoded_default


def set_user_preference(
    session: Session,
    user: User,
    key: str,
    value: Any,
) -> None:
    """Set a user preference.

    Args:
        session: Database session.
        user: The user to set preference for.
        key: The preference key.
        value: The preference value.
    """
    # Create a new dict to trigger SQLAlchemy change detection
    # (JSON columns don't track mutations in-place)
    prefs = dict(user.preferences) if user.preferences else {}
    prefs[key] = value
    user.preferences = prefs

    session.add(user)
    session.commit()
    session.refresh(user)


def get_system_setting(session: Session, key: str) -> SystemSettings | None:
    """Get a system setting by key.

    Args:
        session: Database session.
        key: The setting key.

    Returns:
        The SystemSettings object or None if not found.
    """
    statement = select(SystemSettings).where(SystemSettings.key == key)
    return session.exec(statement).first()


def set_system_setting(
    session: Session,
    key: str,
    value: str,
    updated_by_id: int,
) -> SystemSettings:
    """Set a system setting (creates or updates).

    Args:
        session: Database session.
        key: The setting key.
        value: The setting value (as string).
        updated_by_id: ID of the user making the change.

    Returns:
        The created/updated SystemSettings object.
    """
    existing = get_system_setting(session, key)

    if existing:
        existing.value = value
        existing.updated_at = datetime.now()
        existing.updated_by = updated_by_id
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    new_setting = SystemSettings(
        key=key,
        value=value,
        updated_by=updated_by_id,
    )
    session.add(new_setting)
    session.commit()
    session.refresh(new_setting)
    return new_setting


def get_all_user_preferences(session: Session, user: User) -> dict[str, Any]:
    """Get all user preferences with defaults applied.

    Args:
        session: Database session.
        user: The user to get preferences for.

    Returns:
        Dictionary with all preference keys and their values.
    """
    result = {}

    for key, default_value in HARDCODED_DEFAULTS.items():
        result[key] = get_preference(session, user, key, default_value)

    return result


def change_user_password(
    session: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    """Change a user's password after verifying current password.

    Args:
        session: Database session.
        user: The user whose password to change.
        current_password: The current password for verification.
        new_password: The new password to set.

    Returns:
        True if password was changed, False if current password was wrong.

    Raises:
        ValueError: If new password is too short.
    """
    # Validate new password length
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Neues Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben")

    # Verify current password
    if not user.check_password(current_password):
        return False

    # Set new password
    user.set_password(new_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return True


def change_user_email(
    session: Session,
    user: User,
    new_email: str,
) -> bool:
    """Change a user's email address.

    Args:
        session: Database session.
        user: The user whose email to change.
        new_email: The new email address.

    Returns:
        True if email was changed.

    Raises:
        ValueError: If email format is invalid or email already exists.
    """
    # Validate email format
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_pattern, new_email):
        raise ValueError("ungültige E-Mail-Adresse")

    # Check if email already exists (for another user)
    statement = select(User).where(User.email == new_email, User.id != user.id)
    existing = session.exec(statement).first()
    if existing:
        raise ValueError("E-Mail-Adresse ist bereits vergeben")

    user.email = new_email
    session.add(user)
    session.commit()
    session.refresh(user)
    return True


def save_last_item_entry(
    session: Session,
    user: User,
    last_entry: dict[str, Any],
) -> None:
    """Save the last item entry data for smart defaults.

    Args:
        session: Database session.
        user: The user to save for.
        last_entry: The last item entry data.
    """
    # Create a new dict to trigger SQLAlchemy change detection
    prefs = dict(user.preferences) if user.preferences else {}
    prefs["last_item_entry"] = last_entry
    user.preferences = prefs

    session.add(user)
    session.commit()
    session.refresh(user)


def get_last_item_entry(session: Session, user: User) -> dict[str, Any] | None:
    """Get the last item entry data for smart defaults.

    Args:
        session: Database session.
        user: The user to get data for.

    Returns:
        The last item entry data or None.
    """
    if user.preferences is None:
        return None

    return user.preferences.get("last_item_entry")


def get_expiry_thresholds(session: Session) -> tuple[int, int]:
    """Get expiry threshold settings from database.

    Returns the configured critical and warning days for expiry status calculation.
    Falls back to hardcoded defaults if not set.

    Args:
        session: Database session.

    Returns:
        Tuple of (critical_days, warning_days).
    """
    critical_setting = get_system_setting(session, "expiry_critical_days")
    warning_setting = get_system_setting(session, "expiry_warning_days")

    critical_days = int(critical_setting.value) if critical_setting else HARDCODED_DEFAULTS["expiry_critical_days"]
    warning_days = int(warning_setting.value) if warning_setting else HARDCODED_DEFAULTS["expiry_warning_days"]

    return (critical_days, warning_days)
