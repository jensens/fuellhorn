"""Tests for theme color utilities."""

from app.ui.theme.colors import get_contrast_text_color


class TestGetContrastTextColor:
    """Tests for get_contrast_text_color function."""

    def test_dark_background_returns_white(self) -> None:
        """Dark background should return white text."""
        assert get_contrast_text_color("#000000") == "white"
        assert get_contrast_text_color("#1F2937") == "white"
        assert get_contrast_text_color("#4A7C59") == "white"

    def test_light_background_returns_dark(self) -> None:
        """Light background should return dark text."""
        assert get_contrast_text_color("#FFFFFF") == "#1F2937"
        assert get_contrast_text_color("#F3F4F6") == "#1F2937"

    def test_with_hash_prefix(self) -> None:
        """Should work with # prefix."""
        assert get_contrast_text_color("#000000") == "white"

    def test_without_hash_prefix(self) -> None:
        """Should work without # prefix."""
        assert get_contrast_text_color("000000") == "white"

    def test_invalid_hex_returns_default(self) -> None:
        """Invalid hex should return default dark gray."""
        assert get_contrast_text_color("invalid") == "#374151"
        assert get_contrast_text_color("FFF") == "#374151"  # Too short
        assert get_contrast_text_color("") == "#374151"

    def test_caching_works(self) -> None:
        """Same color should return cached result."""
        # Call twice with same color
        result1 = get_contrast_text_color("#4A7C59")
        result2 = get_contrast_text_color("#4A7C59")
        assert result1 == result2
