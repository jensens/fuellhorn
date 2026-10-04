"""Konfiguration für die Fuellhorn Anwendung.

Liest Environment-Variablen und stellt Konfigurations-Objekte bereit.
"""

from collections.abc import Mapping
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Literal


# Lade .env Datei wenn vorhanden
load_dotenv()

SQLITE_FILE_PREFIX = "sqlite:///"


def resolve_data_dir(env: Mapping[str, str] | None = None, cwd: Path | None = None) -> Path:
    """Bestimmt das Datenverzeichnis: ``FUELLHORN_DATA_DIR`` oder ``<Arbeitsverzeichnis>/data``.

    Bewusst nicht relativ zum Paket: Im installierten Wheel läge das Verzeichnis
    in ``site-packages`` und damit außerhalb eines gemounteten Volumes (Issue #371).
    """
    environment = os.environ if env is None else env
    configured = environment.get("FUELLHORN_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    return (cwd or Path.cwd()) / "data"


def ensure_sqlite_directory(url: str) -> None:
    """Legt das Verzeichnis der SQLite-Datei an; In-Memory-URLs werden ignoriert.

    Raises:
        RuntimeError: Wenn das Verzeichnis nicht angelegt werden kann oder nicht beschreibbar ist.
    """
    if not url.startswith(SQLITE_FILE_PREFIX):
        return
    file_part = url.removeprefix(SQLITE_FILE_PREFIX).split("?", 1)[0]
    if not file_part or file_part.startswith(":memory:"):
        return

    directory = Path(file_part).parent
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Datenverzeichnis {directory} kann nicht angelegt werden ({exc.strerror}). "
            "FUELLHORN_DATA_DIR auf ein beschreibbares Verzeichnis setzen oder DATABASE_URL anpassen."
        ) from exc
    if not os.access(directory, os.W_OK):
        raise RuntimeError(
            f"Datenverzeichnis {directory} ist nicht beschreibbar. "
            "FUELLHORN_DATA_DIR auf ein beschreibbares Verzeichnis setzen oder DATABASE_URL anpassen."
        )


# Datenverzeichnis (SQLite-Datei, später evtl. Uploads)
DATA_DIR = resolve_data_dir()


def parse_trusted_proxies(value: str) -> frozenset[str]:
    """Parst TRUSTED_PROXIES (kommagetrennte IPs) in eine Menge.

    Nur wenn der direkte Peer eines Requests in dieser Menge ist, wird der
    X-Forwarded-For-Header für die Client-IP (Login-Rate-Limiting) ausgewertet.
    Leer bedeutet: keinem Proxy vertrauen, immer die Peer-IP verwenden.
    """
    return frozenset(part.strip() for part in value.split(",") if part.strip())


class Config:
    """Haupt-Konfiguration für die Anwendung."""

    # Datenbank
    DB_TYPE: Literal["sqlite", "postgresql"] = os.getenv("DB_TYPE", "sqlite")  # type: ignore
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"{SQLITE_FILE_PREFIX}{DATA_DIR / 'fuellhorn.db'}",
    )

    # Sicherheit / Security
    # SECRET_KEY: Main application secret for cryptographic operations
    # Used for: Session signing, CSRF tokens, general app security
    # Must be: Strong random string (min 32 chars), never committed to git
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    _secret_key = os.getenv("SECRET_KEY")
    if not _secret_key:
        raise RuntimeError("SECRET_KEY environment variable must be set! Never use default secrets in production.")
    SECRET_KEY: str = _secret_key

    # App
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # Reverse Proxy: IPs, deren X-Forwarded-For-Header vertraut wird (Issue #364)
    TRUSTED_PROXIES: frozenset[str] = parse_trusted_proxies(os.getenv("TRUSTED_PROXIES", ""))

    # Session
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 Stunden default
    REMEMBER_ME_MAX_AGE: int = int(os.getenv("REMEMBER_ME_MAX_AGE", "2592000"))  # 30 Tage default

    @classmethod
    def get_database_url(cls) -> str:
        """Gibt die Datenbank-URL zurück.

        Für SQLite wird das Verzeichnis der Datenbankdatei angelegt.
        Für PostgreSQL wird automatisch der psycopg3 Dialekt verwendet.
        URLs mit postgresql:// werden zu postgresql+psycopg:// konvertiert.
        """
        if cls.DB_TYPE == "sqlite":
            ensure_sqlite_directory(cls.DATABASE_URL)
            return cls.DATABASE_URL

        # PostgreSQL: Sicherstellen dass psycopg3 Dialekt verwendet wird
        url = cls.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            # Heroku-style URLs
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


# Singleton-Instanz
config = Config()

# File upload limits (für später, z.B. Barcode-Bilder in Post-MVP)
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB in bytes


def get_storage_secret() -> str:
    """Gibt das Password Hashing Secret (Pepper) zurück.

    FUELLHORN_SECRET: Password hashing pepper (additional secret layer)
    Used for: Adding a secret salt to bcrypt password hashes
    Must be: Strong random string (min 32 chars), never committed to git
    Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

    CRITICAL WARNING: NEVER change this value in production!
    Changing this value will invalidate ALL existing user passwords,
    making it impossible for users to log in. If you must rotate this secret,
    you need a migration strategy to rehash all passwords.

    Raises:
        RuntimeError: Wenn FUELLHORN_SECRET nicht gesetzt ist.

    Returns:
        Das Storage Secret aus der Environment-Variable.
    """
    secret = os.getenv("FUELLHORN_SECRET")
    if not secret:
        raise RuntimeError(
            "FUELLHORN_SECRET environment variable must be set! Never use default secrets in production."
        )
    return secret
