"""Pytest fixtures für Playwright E2E Tests.

Diese Fixtures starten einen echten Server als separaten Prozess
und verwenden Playwright für Browser-Automatisierung.

Performance-Optimierung:
- Server wird pro Test-MODUL gestartet (nicht pro Test)
- Datenbank wird vor jedem Test zurückgesetzt
- Spart ~2-3s Server-Startup pro Test

Parallelisierung:
- Maximal 4 Worker für E2E Tests (um System-Overload zu vermeiden)
- Jeder Worker bekommt eigenen Server-Prozess

Jeder Test bekommt:
- Frischen DB-Zustand (via Reset-Endpoint)
- Admin-User ist automatisch angelegt
- Perfekte Test-Isolation

WICHTIG: E2E-Tests werden standardmäßig übersprungen, da sie
die asyncio Event Loop für UI-Tests korrumpieren können.
Zum Ausführen: `uv run pytest -m e2e --run-e2e`
"""

import os
from pathlib import Path
import pytest
import socket
import subprocess
import sys
import time


# Maximum parallel workers for E2E tests to prevent system overload
E2E_MAX_WORKERS = 4


def pytest_xdist_auto_num_workers(config) -> int:
    """Limit xdist auto-workers for E2E tests to prevent system overload.

    When running with -n auto, xdist uses CPU count. For E2E tests,
    we limit this to E2E_MAX_WORKERS (4) to prevent system overload
    since each worker starts its own server process.
    """
    return E2E_MAX_WORKERS


def pytest_collection_modifyitems(config, items):
    """Mark all tests in this directory as e2e and skip unless --run-e2e is set."""
    run_e2e = config.getoption("--run-e2e", default=False)
    skip_e2e = pytest.mark.skip(reason="E2E-Tests benötigen --run-e2e Flag")

    for item in items:
        # Only mark tests in this directory
        if "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            if not run_e2e:
                item.add_marker(skip_e2e)


def pytest_addoption(parser):
    """Add --run-e2e command line option."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests (default: skip)",
    )


def _find_free_port() -> int:
    """Finde einen freien Port für den Test-Server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 30.0) -> bool:
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


@pytest.fixture(scope="module")
def _module_server():
    """Interner Fixture: Startet Server einmal pro Test-Modul.

    Nicht direkt verwenden - nutze stattdessen `live_server`.
    """
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Pfad zum Server-Script
    server_script = Path(__file__).parent / "_server.py"

    # Saubere Umgebung für den Server-Prozess erstellen
    # (ohne pytest/NiceGUI Test-Mode Variablen)
    clean_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("NICEGUI_") and k != "TESTING" and not k.startswith("PYTEST")
    }

    # Server als separaten Prozess starten mit sauberer Umgebung
    proc = subprocess.Popen(
        [sys.executable, str(server_script), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=clean_env,
    )

    # Warten bis Server bereit ist
    if not _wait_for_server(url):
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        pytest.fail(
            f"Server wurde nicht rechtzeitig gestartet auf {url}\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}"
        )

    yield url

    # Server beenden
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _reset_test_data(url: str) -> None:
    """Reset database to initial seed state."""
    import httpx

    response = httpx.get(f"{url}/api/test/reset", timeout=5.0)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to reset test data: {response.text}")


@pytest.fixture(scope="function")
def live_server(_module_server: str):
    """Server-URL für E2E Tests mit frischem DB-Zustand.

    Yields:
        str: Die Base-URL des Servers (z.B. "http://127.0.0.1:8765")

    Jeder Test bekommt:
    - Frischen DB-Zustand (Items, Withdrawals, LoginAttempts gelöscht)
    - Admin-User automatisch angelegt (username: admin, password: admin)
    - Kategorien und Lagerorte vorhanden
    - Perfekte Isolation von anderen Tests

    Performance:
    - Server startet nur einmal pro Test-Modul
    - Nur DB-Reset zwischen Tests (~50ms statt ~3s Server-Neustart)

    Beispiel:
        def test_login(page, live_server):
            page.goto(f"{live_server}/login")
            page.fill("input[type='text']", "admin")
            page.fill("input[type='password']", "admin")
            page.click("button:has-text('Anmelden')")
    """
    # Reset DB vor jedem Test für sauberen Zustand
    _reset_test_data(_module_server)
    yield _module_server
