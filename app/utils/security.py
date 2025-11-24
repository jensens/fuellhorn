"""Security utilities for Fuellhorn."""

import re


def sanitize_filename(filename: str | None) -> str:
    """Sanitize filename for safe use in HTTP headers.

    Removes dangerous characters that could be used for header injection attacks:
    - CRLF characters (\\r, \\n)
    - Special characters except alphanumeric, dots, dashes, underscores
    - Limits length to 255 characters

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename safe for use in Content-Disposition headers.
        Returns "download" if filename is None or empty.

    Examples:
        >>> sanitize_filename('image.jpg')
        'image.jpg'
        >>> sanitize_filename('test\\r\\nSet-Cookie: evil')
        'testSet-Cookie_evil'
        >>> sanitize_filename(None)
        'download'
    """
    if not filename:
        return "download"

    # Nur ASCII alphanumerisch, Punkt, Bindestrich, Underscore erlauben
    # Alle anderen Zeichen (inkl. Unicode) werden durch Underscore ersetzt
    safe_filename = re.sub(r"[^\w\-\.]", "_", filename, flags=re.ASCII)

    # Länge auf 255 Zeichen begrenzen
    safe_filename = safe_filename[:255]

    # Falls nach Sanitization leer, default verwenden
    if not safe_filename or safe_filename == ".":
        return "download"

    return safe_filename


def escape_like_pattern(pattern: str) -> str:
    """Escape LIKE wildcards in user input for SQL queries.

    Escapes special LIKE wildcards to prevent DoS attacks via excessive wildcards:
    - % (matches any string)
    - _ (matches any single character)
    - \\ (escape character itself)

    Args:
        pattern: User input to be used in LIKE query

    Returns:
        Escaped pattern safe for use in SQL LIKE queries

    Examples:
        >>> escape_like_pattern("test%pattern")
        'test\\\\%pattern'
        >>> escape_like_pattern("file_name")
        'file\\\\_name'
        >>> escape_like_pattern("normal text")
        'normal text'
    """
    # Escape backslash first (to avoid double-escaping)
    escaped = pattern.replace("\\", "\\\\")
    # Escape LIKE wildcards
    escaped = escaped.replace("%", r"\%")
    escaped = escaped.replace("_", r"\_")
    return escaped
