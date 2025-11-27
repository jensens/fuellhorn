"""Pytest fixtures für Playwright E2E Tests.

Diese Fixtures starten einen echten Server in einem Subprocess
und verwenden Playwright für Browser-Automatisierung.

Jeder Test bekommt:
- Frischen Server mit eigener in-memory SQLite DB
- Admin-User ist automatisch angelegt
- Perfekte Test-Isolation
"""

from multiprocessing import Process
import os
import pytest
import socket
import time


def _find_free_port() -> int:
    """Finde einen freien Port für den Test-Server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    """Starte den NiceGUI/FastAPI Server.

    Diese Funktion läuft in einem separaten Prozess.
    Jeder Prozess hat seine eigene in-memory SQLite DB.
    """
    # Setze Umgebungsvariablen für Test-Modus
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-e2e-tests"
    os.environ["FUELLHORN_SECRET"] = "test-fuellhorn-secret-for-e2e-tests"

    # Importiere die App erst im Subprocess
    # damit jeder Test eine frische DB bekommt
    import app.api.health as _api_health  # noqa: F401
    from app.database import create_db_and_tables
    from app.database import get_session
    from app.models import User
    import app.ui.pages as _pages  # noqa: F401
    import app.ui.test_pages as _test_pages  # noqa: F401
    from nicegui import ui

    # Datenbank initialisieren (in-memory SQLite)
    create_db_and_tables()

    # Admin-User erstellen
    with next(get_session()) as session:
        admin = User(
            username="admin",
            email="admin@test.com",
            is_active=True,
            role="admin",
        )
        admin.set_password("admin")  # Einfaches Passwort für E2E Tests
        session.add(admin)
        session.commit()

    # Server starten
    ui.run(
        host="127.0.0.1",
        port=port,
        title="Füllhorn - E2E Test",
        storage_secret="test-storage-secret",
        reload=False,
        show=False,
    )


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    """Warte bis der Server erreichbar ist."""
    import httpx

    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(f"{url}/api/health", timeout=1.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


@pytest.fixture(scope="function")
def live_server():
    """Starte einen frischen Server für jeden Test.

    Yields:
        str: Die Base-URL des Servers (z.B. "http://127.0.0.1:8765")

    Jeder Test bekommt:
    - Frischen Server in eigenem Prozess
    - Eigene in-memory SQLite DB
    - Admin-User automatisch angelegt (username: admin, password: admin)
    - Perfekte Isolation von anderen Tests

    Beispiel:
        def test_login(page, live_server):
            page.goto(f"{live_server}/login")
            page.fill("input[type='text']", "admin")
            page.fill("input[type='password']", "admin")
            page.click("button:has-text('Anmelden')")
    """
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Server in Subprocess starten
    proc = Process(target=_run_server, args=(port,), daemon=True)
    proc.start()

    # Warten bis Server bereit ist
    if not _wait_for_server(url):
        proc.terminate()
        proc.join(timeout=5)
        pytest.fail(f"Server wurde nicht rechtzeitig gestartet auf {url}")

    yield url

    # Server beenden
    proc.terminate()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=5)
