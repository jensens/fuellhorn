"""Pytest fixtures für Playwright E2E Tests.

Diese Fixtures starten einen echten Server als separaten Prozess
und verwenden Playwright für Browser-Automatisierung.

Jeder Test bekommt:
- Frischen Server mit eigener in-memory SQLite DB
- Admin-User ist automatisch angelegt
- Perfekte Test-Isolation
"""

import os
from pathlib import Path
import pytest
import socket
import subprocess
import sys
import time


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
