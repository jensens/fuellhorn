"""Unit Tests for the Solarpunk Icon System.

Tests the icon loading, registry, and helper functions.
"""

from app.ui.theme.icons import ICON_CATEGORIES
from app.ui.theme.icons import get_icon_svg
from app.ui.theme.icons import get_icon_svg_inline
from app.ui.theme.icons import icon_exists
from app.ui.theme.icons import list_icons
import pytest


class TestIconRegistry:
    """Tests for the icon registry."""

    def test_icon_categories_not_empty(self) -> None:
        """Verify registry has all expected categories."""
        expected_categories = {
            "actions",
            "categories",
            "item-types",
            "locations",
            "misc",
            "navigation",
            "status",
        }
        assert set(ICON_CATEGORIES.keys()) == expected_categories

    def test_status_icons_complete(self) -> None:
        """Verify all status icons are registered."""
        expected = {"calendar", "critical", "expired", "info", "ok", "warning"}
        assert set(ICON_CATEGORIES["status"]) == expected

    def test_navigation_icons_complete(self) -> None:
        """Verify all navigation icons are registered."""
        expected = {"add", "home", "inventory"}
        assert set(ICON_CATEGORIES["navigation"]) == expected


class TestGetIconSvg:
    """Tests for get_icon_svg function."""

    def test_get_status_ok_icon(self) -> None:
        """Load ok status icon successfully."""
        svg = get_icon_svg("status/ok")
        assert "<svg" in svg
        assert "currentColor" in svg

    def test_get_navigation_home_icon(self) -> None:
        """Load home navigation icon successfully."""
        svg = get_icon_svg("navigation/home")
        assert "<svg" in svg

    def test_icon_not_found_raises_error(self) -> None:
        """Raise FileNotFoundError for missing icons."""
        with pytest.raises(FileNotFoundError):
            get_icon_svg("nonexistent/icon")


class TestGetIconSvgInline:
    """Tests for get_icon_svg_inline function."""

    def test_adds_size_attributes(self) -> None:
        """Inline function adds width and height attributes."""
        svg = get_icon_svg_inline("status/ok", size="32px")
        assert 'width="32px"' in svg
        assert 'height="32px"' in svg

    def test_default_size_24px(self) -> None:
        """Default size is 24px."""
        svg = get_icon_svg_inline("status/ok")
        assert 'width="24px"' in svg
        assert 'height="24px"' in svg


class TestIconExists:
    """Tests for icon_exists function."""

    def test_existing_icon_returns_true(self) -> None:
        """Return True for existing icons."""
        assert icon_exists("status/ok") is True
        assert icon_exists("navigation/home") is True

    def test_missing_icon_returns_false(self) -> None:
        """Return False for missing icons."""
        assert icon_exists("nonexistent/icon") is False


class TestListIcons:
    """Tests for list_icons function."""

    def test_list_all_icons(self) -> None:
        """List all icons returns 67 icons."""
        all_icons = list_icons()
        assert len(all_icons) == 67

    def test_list_icons_by_category(self) -> None:
        """List icons filtered by category."""
        status_icons = list_icons("status")
        assert len(status_icons) == 6
        assert "status/ok" in status_icons
        assert "status/warning" in status_icons

    def test_list_icons_invalid_category(self) -> None:
        """Return empty list for invalid category."""
        icons = list_icons("nonexistent")
        assert icons == []

    def test_list_icons_format(self) -> None:
        """Icons are in category/name format."""
        icons = list_icons("navigation")
        for icon in icons:
            assert "/" in icon
            category, name = icon.split("/")
            assert category == "navigation"
