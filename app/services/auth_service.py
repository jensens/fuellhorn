"""Auth Service - Business Logic für Authentication und User-Verwaltung."""

from ..models.category import Category
from ..models.item import Item
from ..models.location import Location
from ..models.system_settings import SystemSettings
from ..models.user import Role
from ..models.user import User
from ..models.withdrawal import Withdrawal
from ..services.errors import DuplicateNameError
from ..services.validation import validate_email
from ..services.validation import validate_password
from ..services.validation import validate_username
from datetime import datetime
import logging
from sqlmodel import Session
from sqlmodel import func
from sqlmodel import select


logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Wird geworfen wenn ein User nicht gefunden wurde."""

    pass


class AuthenticationError(Exception):
    """Wird geworfen wenn die Authentifizierung fehlschlägt."""

    pass


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    role: Role = Role.USER,
) -> User:
    """Erstellt einen neuen User.

    Args:
        session: Datenbank-Session
        username: Username (muss eindeutig sein)
        email: Email-Adresse (muss eindeutig sein)
        password: Klartext-Passwort (wird automatisch gehasht)
        role: Rolle des Users (default: USER)

    Returns:
        Der erstellte User

    Raises:
        ServiceValidationError: ungültiger Benutzername, ungültige E-Mail oder zu kurzes Passwort (Issue #383)
        DuplicateNameError: Benutzername oder E-Mail bereits vergeben (Issue #382)
    """
    username = validate_username(username)
    email = validate_email(email)
    validate_password(password)
    _ensure_unique_username(session, username)
    _ensure_unique_email(session, email)

    user = User(
        username=username,
        email=email,
        role=role.value,
    )
    user.set_password(password)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def _ensure_unique_username(session: Session, username: str, exclude_user_id: int | None = None) -> None:
    """Eindeutigkeit VOR dem Insert prüfen: liefert eine deutsche Meldung statt eines dialektabhängigen IntegrityErrors."""
    statement = select(User).where(func.lower(User.username) == username.lower())
    existing = session.exec(statement).first()
    if existing is not None and existing.id != exclude_user_id:
        raise DuplicateNameError("username", username, "Benutzername")


def _ensure_unique_email(session: Session, email: str, exclude_user_id: int | None = None) -> None:
    statement = select(User).where(func.lower(User.email) == email.lower())
    existing = session.exec(statement).first()
    if existing is not None and existing.id != exclude_user_id:
        raise DuplicateNameError("email", email, "E-Mail-Adresse")


def get_user(session: Session, user_id: int) -> User:
    """Ruft einen User nach ID ab.

    Args:
        session: Datenbank-Session
        user_id: ID des Users

    Returns:
        Der User

    Raises:
        UserNotFoundError: Wenn der User nicht existiert
    """
    user = session.get(User, user_id)

    if user is None:
        raise UserNotFoundError(f"User mit ID {user_id} nicht gefunden")

    return user


def get_user_by_username(session: Session, username: str) -> User | None:
    """Ruft einen User nach Username ab.

    Args:
        session: Datenbank-Session
        username: Username

    Returns:
        Der User oder None wenn nicht gefunden
    """
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()

    return user


LOGIN_FAILED_MESSAGE = "Username oder Passwort falsch"


def authenticate_user(session: Session, username: str, password: str) -> User:
    """Authentifiziert einen User mit Username und Passwort.

    Hinweis: Brute-Force-Schutz (Rate Limiting) wird auf IP-Ebene
    im Login-Handler implementiert, nicht hier.

    Args:
        session: Datenbank-Session
        username: Username
        password: Klartext-Passwort

    Returns:
        Der authentifizierte User

    Raises:
        AuthenticationError: immer mit derselben Meldung, egal ob der Benutzer unbekannt,
            deaktiviert oder das Passwort falsch ist (kein User-Enumeration-Leck, Issue #402);
            der eigentliche Grund steht im Log.
    """
    user = get_user_by_username(session, username)

    if user is None:
        raise AuthenticationError(LOGIN_FAILED_MESSAGE)

    if not user.is_active:
        logger.info("Login abgelehnt: Benutzer %r ist deaktiviert", username)
        raise AuthenticationError(LOGIN_FAILED_MESSAGE)

    if not user.check_password(password):
        raise AuthenticationError(LOGIN_FAILED_MESSAGE)

    # Login erfolgreich
    user.last_login = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


SELF_CHANGE_MESSAGE = (
    "Die eigene Rolle und der eigene Aktiv-Status lassen sich nicht ändern, das eigene Konto nicht löschen."
)


def count_active_admins(session: Session) -> int:
    """Anzahl aktiver Admins (nur die zählen für den Zugang zur Verwaltung)."""
    statement = (
        select(func.count()).select_from(User).where(User.role == Role.ADMIN.value).where(User.is_active == True)  # noqa: E712
    )
    return session.exec(statement).one()


def _is_active_admin(user: User) -> bool:
    return user.role == Role.ADMIN.value and user.is_active


def _ensure_another_active_admin_remains(session: Session, user: User, action: str) -> None:
    """Verweigert ``action`` an ``user``, wenn danach kein aktiver Admin mehr übrig wäre (Issue #380)."""
    if _is_active_admin(user) and count_active_admins(session) <= 1:
        raise ValueError(
            f"'{user.username}' ist der letzte aktive Admin und kann nicht {action} werden. "
            "Zuerst einen weiteren Admin anlegen."
        )


def update_user(
    session: Session,
    user_id: int,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role: Role | None = None,
    is_active: bool | None = None,
    acting_user_id: int | None = None,
) -> User:
    """Aktualisiert einen User.

    Nur die übergebenen Felder werden aktualisiert. Rolle und Aktiv-Status des
    eigenen Kontos sind tabu, und der letzte aktive Admin kann weder degradiert
    noch deaktiviert werden (Issue #380).

    Args:
        session: Datenbank-Session
        user_id: ID des zu aktualisierenden Users
        username: Neuer Username (optional)
        email: Neue Email (optional)
        password: Neues Passwort (optional, wird gehasht)
        role: Neue Rolle (optional)
        is_active: Aktiv-Status (optional)
        acting_user_id: ID des handelnden Nutzers (für den Selbstschutz)

    Returns:
        Der aktualisierte User

    Raises:
        UserNotFoundError: Wenn der User nicht existiert
        ValueError: Selbst-Degradierung/-Deaktivierung oder letzter aktiver Admin
    """
    user = get_user(session, user_id)

    demotes = role is not None and role != Role.ADMIN and user.role == Role.ADMIN.value
    deactivates = is_active is False and user.is_active
    if acting_user_id == user_id and (demotes or deactivates):
        raise ValueError(SELF_CHANGE_MESSAGE)
    if demotes:
        _ensure_another_active_admin_remains(session, user, "degradiert")
    if deactivates:
        _ensure_another_active_admin_remains(session, user, "deaktiviert")

    # Nur übergebene Werte aktualisieren (Validierung zentral, Issue #383)
    if username is not None:
        username = validate_username(username)
        _ensure_unique_username(session, username, exclude_user_id=user_id)
        user.username = username
    if email is not None:
        email = validate_email(email)
        _ensure_unique_email(session, email, exclude_user_id=user_id)
        user.email = email
    if password is not None:
        validate_password(password)
        user.set_password(password)
    if role is not None:
        user.role = role.value
    if is_active is not None:
        user.is_active = is_active

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def count_user_references(session: Session, user_id: int) -> dict[str, int]:
    """Zählt Datensätze, die auf den Benutzer verweisen (nur Einträge > 0)."""
    references = {
        "Artikel": select(func.count()).select_from(Item).where(Item.created_by == user_id),
        "Entnahmen": select(func.count()).select_from(Withdrawal).where(Withdrawal.withdrawn_by == user_id),
        "Kategorien": select(func.count()).select_from(Category).where(Category.created_by == user_id),
        "Lagerorte": select(func.count()).select_from(Location).where(Location.created_by == user_id),
        "Einstellungen": select(func.count()).select_from(SystemSettings).where(SystemSettings.updated_by == user_id),
    }
    return {label: count for label, statement in references.items() if (count := session.exec(statement).one())}


def delete_user(session: Session, user_id: int, acting_user_id: int | None = None) -> None:
    """Löscht einen User ohne Referenzen.

    Benutzer, die Artikel, Entnahmen, Kategorien, Lagerorte oder Einstellungen
    angelegt haben, lassen sich nicht löschen (Fremdschlüssel, Nachvollziehbarkeit);
    der Weg ist das Deaktivieren (Issue #379). Das eigene Konto und der letzte
    aktive Admin sind ebenfalls geschützt (Issue #380).

    Args:
        session: Datenbank-Session
        user_id: ID des zu löschenden Users
        acting_user_id: ID des handelnden Nutzers (für den Selbstschutz)

    Raises:
        UserNotFoundError: Wenn der User nicht existiert
        ValueError: Eigenes Konto, letzter aktiver Admin oder noch referenziert
    """
    user = get_user(session, user_id)

    if acting_user_id == user_id:
        raise ValueError(SELF_CHANGE_MESSAGE)
    _ensure_another_active_admin_remains(session, user, "gelöscht")

    references = count_user_references(session, user_id)
    if references:
        details = ", ".join(f"{count} {label}" for label, count in references.items())
        raise ValueError(
            f"Benutzer '{user.username}' kann nicht gelöscht werden: {details} verweisen auf ihn. "
            "Benutzer stattdessen deaktivieren."
        )

    session.delete(user)
    session.commit()


def list_users(session: Session) -> list[User]:
    """Listet alle Users auf.

    Args:
        session: Datenbank-Session

    Returns:
        Liste aller Users
    """
    statement = select(User)
    users = session.exec(statement).all()

    return list(users)
