"""Konfiguration für die Fuellhorn Anwendung.

Liest Environment-Variablen und stellt Konfigurations-Objekte bereit.
"""

from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Literal


# Lade .env Datei wenn vorhanden
load_dotenv()

# Projekt-Root
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"


class Config:
    """Haupt-Konfiguration für die Anwendung."""

    # Datenbank
    DB_TYPE: Literal["sqlite", "postgresql"] = os.getenv("DB_TYPE", "sqlite")  # type: ignore
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'fuellhorn.db'}",
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

    # Session
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 Stunden default
    REMEMBER_ME_MAX_AGE: int = int(os.getenv("REMEMBER_ME_MAX_AGE", "2592000"))  # 30 Tage default

    @classmethod
    def get_database_url(cls) -> str:
        """Gibt die Datenbank-URL zurück."""
        if cls.DB_TYPE == "sqlite":
            # Stelle sicher, dass das data/ Verzeichnis existiert
            DATA_DIR.mkdir(exist_ok=True)
        return cls.DATABASE_URL


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
