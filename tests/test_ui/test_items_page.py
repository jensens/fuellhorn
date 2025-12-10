"""Tests for items page helper functions."""

from app.models.item import Item
from app.models.item import ItemType
from app.ui.pages.items import ITEM_TYPE_LABELS
from app.ui.pages.items import SORT_OPTIONS
from app.ui.pages.items import _build_item_category_map
from app.ui.pages.items import _filter_items
from app.ui.pages.items import _filter_items_by_categories
from app.ui.pages.items import _sort_items
from datetime import date
from datetime import datetime


def _create_test_item(
    id: int,
    product_name: str,
    location_id: int = 1,
    item_type: ItemType = ItemType.PURCHASED_FRESH,
    category_id: int | None = None,
    best_before_date: date | None = None,
    created_at: datetime | None = None,
) -> Item:
    """Create a test item."""
    return Item(
        id=id,
        product_name=product_name,
        location_id=location_id,
        item_type=item_type,
        category_id=category_id,
        quantity=1,
        unit="Stück",
        best_before_date=best_before_date or date(2025, 12, 31),
        created_at=created_at or datetime(2025, 1, 1, 12, 0, 0),
    )


class TestBuildItemCategoryMap:
    """Tests for _build_item_category_map function."""

    def test_builds_map_with_categories(self) -> None:
        """Should build map from item ID to category ID."""
        items = [
            _create_test_item(1, "Item 1", category_id=10),
            _create_test_item(2, "Item 2", category_id=20),
            _create_test_item(3, "Item 3", category_id=10),
        ]
        result = _build_item_category_map(items)
        assert result == {1: 10, 2: 20, 3: 10}

    def test_handles_none_category(self) -> None:
        """Should include None for items without category."""
        items = [
            _create_test_item(1, "Item 1", category_id=10),
            _create_test_item(2, "Item 2", category_id=None),
        ]
        result = _build_item_category_map(items)
        assert result == {1: 10, 2: None}

    def test_empty_list(self) -> None:
        """Should return empty dict for empty list."""
        result = _build_item_category_map([])
        assert result == {}


class TestFilterItems:
    """Tests for _filter_items function."""

    def test_filter_by_search_term(self) -> None:
        """Should filter items by product name."""
        items = [
            _create_test_item(1, "Apple"),
            _create_test_item(2, "Banana"),
            _create_test_item(3, "Apricot"),
        ]
        result = _filter_items(items, "ap", None, None)
        assert len(result) == 2
        assert all("ap" in item.product_name.lower() for item in result)

    def test_filter_by_search_term_case_insensitive(self) -> None:
        """Should filter case-insensitively."""
        items = [
            _create_test_item(1, "Apple"),
            _create_test_item(2, "APPLE"),
            _create_test_item(3, "Banana"),
        ]
        result = _filter_items(items, "apple", None, None)
        assert len(result) == 2

    def test_filter_by_location(self) -> None:
        """Should filter items by location ID."""
        items = [
            _create_test_item(1, "Item 1", location_id=1),
            _create_test_item(2, "Item 2", location_id=2),
            _create_test_item(3, "Item 3", location_id=1),
        ]
        result = _filter_items(items, "", 1, None)
        assert len(result) == 2
        assert all(item.location_id == 1 for item in result)

    def test_filter_by_item_type(self) -> None:
        """Should filter items by item type."""
        items = [
            _create_test_item(1, "Item 1", item_type=ItemType.PURCHASED_FRESH),
            _create_test_item(2, "Item 2", item_type=ItemType.PURCHASED_FROZEN),
            _create_test_item(3, "Item 3", item_type=ItemType.PURCHASED_FRESH),
        ]
        result = _filter_items(items, "", None, ItemType.PURCHASED_FRESH.value)
        assert len(result) == 2
        assert all(item.item_type == ItemType.PURCHASED_FRESH for item in result)

    def test_no_filter_returns_all(self) -> None:
        """Should return all items when no filters applied."""
        items = [
            _create_test_item(1, "Item 1"),
            _create_test_item(2, "Item 2"),
        ]
        result = _filter_items(items, "", None, None)
        assert len(result) == 2

    def test_combined_filters(self) -> None:
        """Should apply all filters together."""
        items = [
            _create_test_item(1, "Apple", location_id=1, item_type=ItemType.PURCHASED_FRESH),
            _create_test_item(2, "Apricot", location_id=2, item_type=ItemType.PURCHASED_FRESH),
            _create_test_item(3, "Apple", location_id=1, item_type=ItemType.PURCHASED_FROZEN),
        ]
        result = _filter_items(items, "apple", 1, ItemType.PURCHASED_FRESH.value)
        assert len(result) == 1
        assert result[0].product_name == "Apple"

    def test_location_zero_means_all(self) -> None:
        """Location ID 0 should not filter by location."""
        items = [
            _create_test_item(1, "Item 1", location_id=1),
            _create_test_item(2, "Item 2", location_id=2),
        ]
        result = _filter_items(items, "", 0, None)
        assert len(result) == 2


class TestFilterItemsByCategories:
    """Tests for _filter_items_by_categories function."""

    def test_filter_by_single_category(self) -> None:
        """Should filter items by single category."""
        items = [
            _create_test_item(1, "Item 1"),
            _create_test_item(2, "Item 2"),
            _create_test_item(3, "Item 3"),
        ]
        category_map = {1: 10, 2: 20, 3: 10}
        result = _filter_items_by_categories(items, {10}, category_map)
        assert len(result) == 2

    def test_filter_by_multiple_categories(self) -> None:
        """Should filter items by multiple categories (OR logic)."""
        items = [
            _create_test_item(1, "Item 1"),
            _create_test_item(2, "Item 2"),
            _create_test_item(3, "Item 3"),
        ]
        category_map = {1: 10, 2: 20, 3: 30}
        result = _filter_items_by_categories(items, {10, 20}, category_map)
        assert len(result) == 2

    def test_empty_categories_returns_all(self) -> None:
        """Empty category set should return all items."""
        items = [
            _create_test_item(1, "Item 1"),
            _create_test_item(2, "Item 2"),
        ]
        category_map = {1: 10, 2: 20}
        result = _filter_items_by_categories(items, set(), category_map)
        assert len(result) == 2


class TestSortItems:
    """Tests for _sort_items function."""

    def test_sort_by_best_before_date_ascending(self) -> None:
        """Should sort by best_before_date ascending."""
        items = [
            _create_test_item(1, "Item 1", best_before_date=date(2025, 12, 31)),
            _create_test_item(2, "Item 2", best_before_date=date(2025, 6, 15)),
            _create_test_item(3, "Item 3", best_before_date=date(2025, 9, 1)),
        ]
        result = _sort_items(items, "best_before_date", ascending=True)
        assert result[0].best_before_date == date(2025, 6, 15)
        assert result[1].best_before_date == date(2025, 9, 1)
        assert result[2].best_before_date == date(2025, 12, 31)

    def test_sort_by_best_before_date_descending(self) -> None:
        """Should sort by best_before_date descending."""
        items = [
            _create_test_item(1, "Item 1", best_before_date=date(2025, 6, 15)),
            _create_test_item(2, "Item 2", best_before_date=date(2025, 12, 31)),
        ]
        result = _sort_items(items, "best_before_date", ascending=False)
        assert result[0].best_before_date == date(2025, 12, 31)

    def test_sort_by_product_name_ascending(self) -> None:
        """Should sort by product_name ascending (case-insensitive)."""
        items = [
            _create_test_item(1, "Banana"),
            _create_test_item(2, "apple"),
            _create_test_item(3, "Cherry"),
        ]
        result = _sort_items(items, "product_name", ascending=True)
        assert result[0].product_name == "apple"
        assert result[1].product_name == "Banana"
        assert result[2].product_name == "Cherry"

    def test_sort_by_product_name_descending(self) -> None:
        """Should sort by product_name descending."""
        items = [
            _create_test_item(1, "Apple"),
            _create_test_item(2, "Cherry"),
        ]
        result = _sort_items(items, "product_name", ascending=False)
        assert result[0].product_name == "Cherry"

    def test_sort_by_created_at(self) -> None:
        """Should sort by created_at."""
        items = [
            _create_test_item(1, "Item 1", created_at=datetime(2025, 3, 1)),
            _create_test_item(2, "Item 2", created_at=datetime(2025, 1, 1)),
            _create_test_item(3, "Item 3", created_at=datetime(2025, 2, 1)),
        ]
        result = _sort_items(items, "created_at", ascending=True)
        assert result[0].created_at == datetime(2025, 1, 1)

    def test_unknown_sort_field_returns_unchanged(self) -> None:
        """Unknown sort field should return items unchanged."""
        items = [
            _create_test_item(1, "Item 1"),
            _create_test_item(2, "Item 2"),
        ]
        result = _sort_items(items, "unknown_field", ascending=True)
        assert len(result) == 2


class TestConstants:
    """Tests for module constants."""

    def test_sort_options_has_required_fields(self) -> None:
        """SORT_OPTIONS should have all required sort fields."""
        assert "best_before_date" in SORT_OPTIONS
        assert "product_name" in SORT_OPTIONS
        assert "created_at" in SORT_OPTIONS

    def test_item_type_labels_has_all_types(self) -> None:
        """ITEM_TYPE_LABELS should have label for all item types."""
        # Should have empty string for "all types"
        assert "" in ITEM_TYPE_LABELS
        # Should have all item type values
        for item_type in ItemType:
            assert item_type.value in ITEM_TYPE_LABELS
