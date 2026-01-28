"""Tests for PWA (Progressive Web App) support."""

from nicegui.testing import User


async def test_manifest_json_is_accessible(user: User) -> None:
    """Manifest.json is accessible via static files."""
    response = await user.http_client.get("/static/manifest.json")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fuellhorn - Lebensmittelvorrats-Verwaltung"
    assert data["short_name"] == "Fuellhorn"
    assert data["display"] == "standalone"


async def test_manifest_contains_required_icons(user: User) -> None:
    """Manifest.json contains required PWA icons."""
    response = await user.http_client.get("/static/manifest.json")

    assert response.status_code == 200
    data = response.json()
    icons = data["icons"]
    sizes = [icon["sizes"] for icon in icons]
    assert "192x192" in sizes
    assert "512x512" in sizes


async def test_manifest_has_correct_theme_colors(user: User) -> None:
    """Manifest.json has correct Solarpunk theme colors."""
    response = await user.http_client.get("/static/manifest.json")

    assert response.status_code == 200
    data = response.json()
    # Solarpunk Fern color
    assert data["theme_color"] == "#4A7C59"
    # Solarpunk Cream color
    assert data["background_color"] == "#FAF7F0"


async def test_pwa_icons_are_accessible(user: User) -> None:
    """PWA icons are accessible via static files."""
    icon_192_response = await user.http_client.get("/static/pwa/fuellhorn-icon-192.png")
    icon_512_response = await user.http_client.get("/static/pwa/fuellhorn-icon-512.png")
    apple_icon_response = await user.http_client.get("/static/pwa/fuellhorn-icon-180.png")

    assert icon_192_response.status_code == 200
    assert icon_512_response.status_code == 200
    assert apple_icon_response.status_code == 200
