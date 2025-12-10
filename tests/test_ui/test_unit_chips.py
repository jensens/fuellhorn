"""Tests for unit chips component."""

from app.ui.components.unit_chips import UNITS
from app.ui.components.unit_chips import get_available_units


class TestGetAvailableUnits:
    """Tests for get_available_units function."""

    def test_returns_list(self) -> None:
        """Should return a list."""
        result = get_available_units()
        assert isinstance(result, list)

    def test_contains_standard_units(self) -> None:
        """Should contain standard units."""
        result = get_available_units()
        assert "g" in result
        assert "kg" in result
        assert "ml" in result
        assert "l" in result
        assert "Stück" in result
        assert "Packung" in result

    def test_returns_copy_not_original(self) -> None:
        """Should return a copy, not the original list."""
        result = get_available_units()
        result.append("test")
        # Original should not be modified
        assert "test" not in get_available_units()
        assert "test" not in UNITS

    def test_has_correct_count(self) -> None:
        """Should have 6 units."""
        result = get_available_units()
        assert len(result) == 6


class TestUnitsConstant:
    """Tests for UNITS constant."""

    def test_units_is_list(self) -> None:
        """UNITS should be a list."""
        assert isinstance(UNITS, list)

    def test_units_has_all_standard_units(self) -> None:
        """UNITS should have all standard units."""
        expected = ["g", "kg", "ml", "l", "Stück", "Packung"]
        assert UNITS == expected
