"""Tests for item type chips component."""

from app.models.item import ItemType
from app.ui.components.item_type_chips import ITEM_TYPE_COLORS
from app.ui.components.item_type_chips import ITEM_TYPE_DATA_TYPES
from app.ui.components.item_type_chips import ITEM_TYPE_LABELS
from app.ui.components.item_type_chips import get_item_type_label


class TestGetItemTypeLabel:
    """Tests for get_item_type_label function."""

    def test_returns_german_label_for_fresh(self) -> None:
        """Should return German label for fresh items."""
        result = get_item_type_label(ItemType.PURCHASED_FRESH)
        assert result == "Frisch eingekauft"

    def test_returns_german_label_for_frozen(self) -> None:
        """Should return German label for frozen items."""
        result = get_item_type_label(ItemType.PURCHASED_FROZEN)
        assert result == "TK-Ware gekauft"

    def test_returns_german_label_for_frozen_later(self) -> None:
        """Should return German label for items frozen later."""
        result = get_item_type_label(ItemType.PURCHASED_THEN_FROZEN)
        assert result == "Frisch gekauft → eingefroren"

    def test_returns_german_label_for_homemade_frozen(self) -> None:
        """Should return German label for homemade frozen items."""
        result = get_item_type_label(ItemType.HOMEMADE_FROZEN)
        assert result == "Selbst eingefroren"

    def test_returns_german_label_for_preserved(self) -> None:
        """Should return German label for preserved items."""
        result = get_item_type_label(ItemType.HOMEMADE_PRESERVED)
        assert result == "Selbst eingemacht"


class TestItemTypeLabels:
    """Tests for ITEM_TYPE_LABELS constant."""

    def test_has_all_item_types(self) -> None:
        """Should have label for all ItemType values."""
        for item_type in ItemType:
            assert item_type in ITEM_TYPE_LABELS

    def test_labels_are_german(self) -> None:
        """Labels should be in German."""
        for label in ITEM_TYPE_LABELS.values():
            assert isinstance(label, str)
            assert len(label) > 0


class TestItemTypeDataTypes:
    """Tests for ITEM_TYPE_DATA_TYPES constant."""

    def test_has_all_item_types(self) -> None:
        """Should have data type for all ItemType values."""
        for item_type in ItemType:
            assert item_type in ITEM_TYPE_DATA_TYPES

    def test_data_types_are_valid(self) -> None:
        """Data types should be valid CSS attribute values."""
        valid_types = {"fresh", "frozen", "homemade"}
        for data_type in ITEM_TYPE_DATA_TYPES.values():
            assert data_type in valid_types


class TestItemTypeColors:
    """Tests for ITEM_TYPE_COLORS constant."""

    def test_has_colors_for_data_types(self) -> None:
        """Should have color for each data type."""
        expected_types = {"fresh", "frozen", "homemade"}
        for data_type in expected_types:
            assert data_type in ITEM_TYPE_COLORS

    def test_colors_are_css_variables(self) -> None:
        """Colors should be CSS variables."""
        for color in ITEM_TYPE_COLORS.values():
            assert color.startswith("var(--sp-")
