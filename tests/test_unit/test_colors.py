"""Tests for theme color utilities."""

from app.ui.theme.colors import get_contrast_text_color
from app.ui.theme.colors import hex_to_rgb
from app.ui.theme.colors import with_alpha


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


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_black(self) -> None:
        """Black should be (0, 0, 0)."""
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_white(self) -> None:
        """White should be (255, 255, 255)."""
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_red(self) -> None:
        """Red should be (255, 0, 0)."""
        assert hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_green(self) -> None:
        """Green should be (0, 255, 0)."""
        assert hex_to_rgb("#00FF00") == (0, 255, 0)

    def test_blue(self) -> None:
        """Blue should be (0, 0, 255)."""
        assert hex_to_rgb("#0000FF") == (0, 0, 255)

    def test_without_hash(self) -> None:
        """Should work without # prefix."""
        assert hex_to_rgb("4A7C59") == (74, 124, 89)

    def test_lowercase(self) -> None:
        """Should work with lowercase hex."""
        assert hex_to_rgb("#ffffff") == (255, 255, 255)


class TestWithAlpha:
    """Tests for with_alpha function."""

    def test_full_opacity(self) -> None:
        """Alpha 1 should give full opacity."""
        result = with_alpha("#000000", 1.0)
        assert result == "rgba(0, 0, 0, 1.0)"

    def test_half_opacity(self) -> None:
        """Alpha 0.5 should give half opacity."""
        result = with_alpha("#FFFFFF", 0.5)
        assert result == "rgba(255, 255, 255, 0.5)"

    def test_zero_opacity(self) -> None:
        """Alpha 0 should give full transparency."""
        result = with_alpha("#FF0000", 0)
        assert result == "rgba(255, 0, 0, 0)"

    def test_custom_color(self) -> None:
        """Custom color with alpha."""
        result = with_alpha("#4A7C59", 0.8)
        assert result == "rgba(74, 124, 89, 0.8)"
