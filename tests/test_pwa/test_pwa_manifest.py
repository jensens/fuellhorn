"""Tests for PWA (Progressive Web App) support."""

from nicegui.testing import User


async def test_manifest_json_is_accessible_at_root(user: User) -> None:
    """Manifest.json is accessible at root URL for browser compatibility."""
    response = await user.http_client.get("/manifest.json")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fuellhorn - Lebensmittelvorrats-Verwaltung"
    assert data["short_name"] == "Fuellhorn"
    assert data["display"] == "standalone"


async def test_manifest_contains_required_icons(user: User) -> None:
    """Manifest.json contains required PWA icons with root URLs."""
    response = await user.http_client.get("/manifest.json")

    assert response.status_code == 200
    data = response.json()
    icons = data["icons"]
    sizes = [icon["sizes"] for icon in icons]
    assert "192x192" in sizes
    assert "512x512" in sizes
    # Icons should use root URLs
    sources = [icon["src"] for icon in icons]
    assert "/icon-192.png" in sources
    assert "/icon-512.png" in sources


async def test_manifest_has_correct_theme_colors(user: User) -> None:
    """Manifest.json has correct Solarpunk theme colors."""
    response = await user.http_client.get("/manifest.json")

    assert response.status_code == 200
    data = response.json()
    # Solarpunk Fern color
    assert data["theme_color"] == "#4A7C59"
    # Solarpunk Cream color
    assert data["background_color"] == "#FAF7F0"


async def test_pwa_icons_are_accessible_at_root(user: User) -> None:
    """PWA icons are accessible at root URLs for browser compatibility."""
    icon_192_response = await user.http_client.get("/icon-192.png")
    icon_512_response = await user.http_client.get("/icon-512.png")
    apple_icon_response = await user.http_client.get("/apple-touch-icon.png")

    assert icon_192_response.status_code == 200
    assert icon_512_response.status_code == 200
    assert apple_icon_response.status_code == 200
