"""preferences_service.get_system_defaults: Hardcoded-Defaults, von Systemeinstellungen überlagert (Issue #397).

Die Admin-Seite hielt eigene Default-Konstanten parallel zu ``HARDCODED_DEFAULTS``.
"""

from app.models.user import User
from app.services import preferences_service
from sqlmodel import Session


def test_system_defaults_fall_back_to_hardcoded(session: Session) -> None:
    assert preferences_service.get_system_defaults(session) == preferences_service.HARDCODED_DEFAULTS


def test_system_defaults_use_stored_settings_as_int(session: Session, test_admin: User) -> None:
    assert test_admin.id is not None
    preferences_service.set_system_settings(
        session, {"item_type_time_window": "15", "expiry_warning_days": "10"}, test_admin.id
    )

    defaults = preferences_service.get_system_defaults(session)

    assert defaults["item_type_time_window"] == 15
    assert defaults["expiry_warning_days"] == 10
    assert defaults["category_time_window"] == preferences_service.HARDCODED_DEFAULTS["category_time_window"]
