"""UI-Test: Der gemeinsame Seitenkopf aus app.startup landet serverseitig in jeder Seite (Issue #375).

Vorher wurde das Head-HTML erst im on_connect-Handler per insertAdjacentHTML
nachgeschoben; <script>-Tags darin wurden nie ausgeführt.
"""

from nicegui.testing import User


async def test_rendered_login_page_contains_pwa_head_tags(user: User) -> None:
    response = await user.http_client.get("/login")

    assert response.status_code == 200
    assert '<link rel="manifest" href="/manifest.json">' in response.text
    assert '<script src="/static/js/swipe-card.js"></script>' in response.text
    assert '<link rel="apple-touch-icon" href="/apple-touch-icon.png">' in response.text
    assert '<link rel="stylesheet" href="/static/css/solarpunk-theme.css">' in response.text
