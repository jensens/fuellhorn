"""Tests for security utilities."""

from app.utils.security import escape_like_pattern
from app.utils.security import sanitize_filename


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_valid_filename_unchanged(self) -> None:
        """Normal filename passes through unchanged."""
        assert sanitize_filename("image.jpg") == "image.jpg"

    def test_filename_with_underscore_and_dash(self) -> None:
        """Filename with underscore and dash is unchanged."""
        assert sanitize_filename("my_file-name.txt") == "my_file-name.txt"

    def test_none_returns_download(self) -> None:
        """None returns default 'download'."""
        assert sanitize_filename(None) == "download"

    def test_empty_string_returns_download(self) -> None:
        """Empty string returns default 'download'."""
        assert sanitize_filename("") == "download"

    def test_crlf_injection_removed(self) -> None:
        """CRLF characters are replaced with underscore."""
        result = sanitize_filename("test\r\nSet-Cookie: evil")
        assert "\r" not in result
        assert "\n" not in result
        assert "Set-Cookie" not in result or "_" in result

    def test_special_characters_replaced(self) -> None:
        """Special characters are replaced with underscores."""
        result = sanitize_filename("file<>name|with*special?chars")
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert "*" not in result
        assert "?" not in result

    def test_unicode_replaced(self) -> None:
        """Unicode characters are replaced with underscore."""
        result = sanitize_filename("文件名.txt")
        assert "_" in result
        assert result.endswith(".txt")

    def test_length_limited_to_255(self) -> None:
        """Filename is truncated to 255 characters."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_only_dot_returns_download(self) -> None:
        """Single dot returns default 'download'."""
        assert sanitize_filename(".") == "download"

    def test_spaces_replaced(self) -> None:
        """Spaces are replaced with underscore."""
        result = sanitize_filename("my file name.txt")
        assert " " not in result
        assert "_" in result


class TestEscapeLikePattern:
    """Tests for escape_like_pattern function."""

    def test_normal_text_unchanged(self) -> None:
        """Normal text without wildcards passes through unchanged."""
        assert escape_like_pattern("normal text") == "normal text"

    def test_percent_escaped(self) -> None:
        """Percent sign is escaped."""
        result = escape_like_pattern("test%pattern")
        assert r"\%" in result

    def test_underscore_escaped(self) -> None:
        """Underscore is escaped."""
        result = escape_like_pattern("file_name")
        assert r"\_" in result

    def test_backslash_escaped(self) -> None:
        """Backslash is escaped first to avoid double-escaping."""
        result = escape_like_pattern("path\\file")
        assert "\\\\" in result

    def test_multiple_wildcards(self) -> None:
        """Multiple wildcards are all escaped."""
        result = escape_like_pattern("a%b_c%d")
        assert result.count(r"\%") == 2
        assert result.count(r"\_") == 1

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert escape_like_pattern("") == ""

    def test_backslash_before_percent(self) -> None:
        """Backslash followed by percent both escaped correctly."""
        result = escape_like_pattern("test\\%value")
        # Backslash becomes \\, percent becomes \%
        assert "\\\\" in result
        assert r"\%" in result
