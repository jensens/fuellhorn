"""Login kehrt zur angeforderten Seite zurück; nur relative Pfade (Issue #402).

Vorher landete man nach dem Login immer im Dashboard, auch wenn man z.B. den Wizard
direkt aufgerufen hatte.
"""

from app.ui.auth import safe_redirect_target
from nicegui.testing import User as TestUser
import pytest


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("/items/add", "/items/add"),
        ("/items?filter=expiring", "/items?filter=expiring"),
        (None, "/dashboard"),
        ("", "/dashboard"),
        ("https://evil.example/", "/dashboard"),
        ("//evil.example/", "/dashboard"),
        ("/\\evil.example", "/dashboard"),
        ("javascript:alert(1)", "/dashboard"),
        ("dashboard", "/dashboard"),
        ("/login?next=/items", "/dashboard"),
    ],
)
def test_safe_redirect_target_accepts_only_relative_paths(target: str | None, expected: str) -> None:
    assert safe_redirect_target(target) == expected


async def _login(user: TestUser) -> None:
    user.find("Benutzername").type("admin")
    user.find("Passwort").type("password123")
    user.find("Anmelden").click()


async def test_protected_page_redirects_to_login_and_back(user: TestUser) -> None:
    # Session-Cookie zuerst: in der User-Simulation folgt die Weiterleitung aus dem Seitenaufbau noch vor dem
    # Set-Cookie der ersten Antwort und landet in einer zweiten Sitzung; ein Browser hat das Cookie längst
    await user.open("/login")
    await user.open("/items/add")
    await user.should_see("Anmelden")

    await _login(user)

    await user.should_see("Schritt 1 von 3")


async def test_query_string_survives_the_round_trip(user: TestUser) -> None:
    await user.open("/login")
    await user.open("/items?filter=expiring")
    await user.should_see("Anmelden")

    await _login(user)

    await user.should_see("Filter zurücksetzen")


async def test_external_next_target_is_ignored(user: TestUser) -> None:
    await user.open("/login?next=https://evil.example/")
    await user.should_see("Anmelden")

    await _login(user)

    await user.should_see("Willkommen admin!")
    await user.should_see("Übersicht")
