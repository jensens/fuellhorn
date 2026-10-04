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


# Datenverzeichnis (SQLite-Datei, NiceGUI-Storage, später evtl. Uploads)
DATA_DIR = resolve_data_dir()


def resolve_storage_path(env: Mapping[str, str] | None = None, data_dir: Path | None = None) -> Path:
    """Verzeichnis für den NiceGUI-Storage (Login-Sitzungen): ``NICEGUI_STORAGE_PATH`` oder ``<DATA_DIR>/.nicegui``.

    NiceGUI schreibt die Sitzungsdateien standardmäßig nach ``./.nicegui`` im Arbeitsverzeichnis.
    Im Container liegt das nicht auf dem Volume, jeder Neustart meldete alle Benutzer ab (Issue #429).
    """
    environment = os.environ if env is None else env
    configured = environment.get("NICEGUI_STORAGE_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (DATA_DIR if data_dir is None else data_dir) / ".nicegui"


STORAGE_PATH = resolve_storage_path()


def parse_trusted_proxies(value: str) -> frozenset[str]:
    """Parst TRUSTED_PROXIES (kommagetrennte IPs) in eine Menge.

    Nur wenn der direkte Peer eines Requests in dieser Menge ist, wird der
    X-Forwarded-For-Header für die Client-IP (Login-Rate-Limiting) ausgewertet.
    Leer bedeutet: keinem Proxy vertrauen, immer die Peer-IP verwenden.
    """
    return frozenset(part.strip() for part in value.split(",") if part.strip())


SUPPORTED_DB_TYPES = ("sqlite", "postgresql")


def parse_db_type(value: str) -> Literal["sqlite", "postgresql"]:
    """Prüft DB_TYPE und bricht mit klarer Meldung ab statt später an einer kryptischen Stelle."""
    normalized = value.strip().lower()
    if normalized == "sqlite":
        return "sqlite"
    if normalized == "postgresql":
        return "postgresql"
    raise RuntimeError(f"DB_TYPE muss 'sqlite' oder 'postgresql' sein, nicht {value!r}.")


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"


class Config:
    """Haupt-Konfiguration für die Anwendung."""

    # Datenbank
    DB_TYPE: Literal["sqlite", "postgresql"] = parse_db_type(os.getenv("DB_TYPE", "sqlite"))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"{SQLITE_FILE_PREFIX}{DATA_DIR / 'fuellhorn.db'}",
    )
    # NiceGUI-Storage (Sitzungen) im Datenverzeichnis, siehe resolve_storage_path (Issue #429)
    STORAGE_PATH: Path = STORAGE_PATH
    # SQL-Statements samt Parametern loggen: bewusst getrennt von DEBUG, weil das
    # Passwort-Hashes, Tokens und IPs in die Logs schreibt (Issue #374)
    SQL_ECHO: bool = _env_flag("SQL_ECHO")

    # App
    DEBUG: bool = _env_flag("DEBUG")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    # Migrationen beim App-Start überspringen, wenn sie extern laufen
    # (Helm: Init-Container oder Hook-Job statt in jedem Pod, Issue #377)
    SKIP_MIGRATIONS: bool = _env_flag("FUELLHORN_SKIP_MIGRATIONS")

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
    """Gibt das NiceGUI Storage Secret zurück.

    FUELLHORN_SECRET signiert die Session-Cookies von ``app.storage.user``
    (NiceGUI ``storage_secret``). Es ist kein bcrypt-Pepper: Passwort-Hashes
    hängen nicht davon ab. Eine Rotation meldet lediglich alle Nutzer ab.
    Muss ein starker Zufallswert sein (min. 32 Zeichen), nie ins Repository:
    python -c "import secrets; print(secrets.token_urlsafe(32))"

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
