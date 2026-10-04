"""Unit Tests: einheitliche Mengenformatierung für Karte, Bottom-Sheet und Toast (Issue #365)."""

from app.ui.utils.quantity import format_quantity


def test_whole_numbers_have_no_decimals() -> None:
    """500.0 → '500'."""
    assert format_quantity(500.0) == "500"


def test_decimals_are_kept() -> None:
    """0.5 → '0.5', 1.25 → '1.25'."""
    assert (format_quantity(0.5), format_quantity(1.25)) == ("0.5", "1.25")


def test_float_noise_is_hidden() -> None:
    """0.1 + 0.2 → '0.3', nie '0.30000000000000004'."""
    assert format_quantity(0.1 + 0.2) == "0.3"


def test_tiny_residue_is_zero() -> None:
    """Binärbruch-Rest unterhalb der Auflösung wird als 0 angezeigt."""
    assert format_quantity(5.551115123125783e-17) == "0"


def test_unit_is_appended_when_given() -> None:
    """Mit Einheit: '2.5 kg'."""
    assert format_quantity(2.5, "kg") == "2.5 kg"
