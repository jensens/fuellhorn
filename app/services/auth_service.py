"""Auth Service - Business Logic für Authentication und User-Verwaltung."""

from ..models.user import Role
from ..models.user import User
from datetime import datetime
import secrets
from sqlmodel import Session
from sqlmodel import select


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
        ValueError: Bei ungültigen Eingabedaten
    """
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


def get_user_by_remember_token(session: Session, token: str) -> User | None:
    """Ruft einen User nach Remember-Me Token ab.

    Args:
        session: Datenbank-Session
        token: Remember-Me Token

    Returns:
        Der User oder None wenn nicht gefunden
    """
    statement = select(User).where(User.remember_token == token)
    user = session.exec(statement).first()

    return user


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
        AuthenticationError: Wenn Username oder Passwort falsch sind,
                            oder wenn der User deaktiviert/gesperrt ist
    """
    user = get_user_by_username(session, username)

    if user is None:
        raise AuthenticationError("Username oder Passwort falsch")

    if not user.is_active:
        raise AuthenticationError("Benutzer ist deaktiviert")

    # Manuelles Admin-Lock prüfen (separate von IP-basiertem Rate Limiting)
    if user.locked_until is not None and user.locked_until > datetime.now():
        raise AuthenticationError(f"Account ist gesperrt bis {user.locked_until.strftime('%H:%M Uhr')}")

    if not user.check_password(password):
        raise AuthenticationError("Username oder Passwort falsch")

    # Login erfolgreich
    user.last_login = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def generate_remember_token(session: Session, user: User) -> str:
    """Generiert einen Remember-Me Token für einen User.

    Args:
        session: Datenbank-Session
        user: User für den der Token generiert wird

    Returns:
        Der generierte Token (kryptografisch sicher)
    """
    token = secrets.token_urlsafe(32)
    user.remember_token = token

    session.add(user)
    session.commit()
    session.refresh(user)

    return token


def revoke_remember_token(session: Session, user: User) -> None:
    """Widerruft den Remember-Me Token eines Users.

    Args:
        session: Datenbank-Session
        user: User dessen Token widerrufen wird
    """
    user.remember_token = None

    session.add(user)
    session.commit()


def update_user(
    session: Session,
    user_id: int,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role: Role | None = None,
    is_active: bool | None = None,
) -> User:
    """Aktualisiert einen User.

    Nur die übergebenen Felder werden aktualisiert.

    Args:
        session: Datenbank-Session
        user_id: ID des zu aktualisierenden Users
        username: Neuer Username (optional)
        email: Neue Email (optional)
        password: Neues Passwort (optional, wird gehasht)
        role: Neue Rolle (optional)
        is_active: Aktiv-Status (optional)

    Returns:
        Der aktualisierte User

    Raises:
        UserNotFoundError: Wenn der User nicht existiert
    """
    user = get_user(session, user_id)

    # Nur übergebene Werte aktualisieren
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password is not None:
        user.set_password(password)
    if role is not None:
        user.role = role.value
    if is_active is not None:
        user.is_active = is_active

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def delete_user(session: Session, user_id: int) -> None:
    """Löscht einen User.

    Args:
        session: Datenbank-Session
        user_id: ID des zu löschenden Users

    Raises:
        UserNotFoundError: Wenn der User nicht existiert
    """
    user = get_user(session, user_id)

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
