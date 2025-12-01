"""UI Tests for Items Page - Card list view of inventory."""

from nicegui.testing import User as TestUser


async def test_items_page_requires_auth(user: TestUser) -> None:
    """Test that items page redirects to login when not authenticated."""
    await user.open("/items")
    # Should redirect to login page
    await user.should_see("Anmelden")


async def test_items_page_renders_when_authenticated(user: TestUser) -> None:
    """Test that items page renders correctly when authenticated."""
    # First login
    await user.open("/test-login-admin")
    # Then navigate to items
    await user.open("/items")
    await user.should_see("Vorrat")


async def test_items_page_shows_bottom_navigation(user: TestUser) -> None:
    """Test that items page has bottom navigation."""
    await user.open("/test-login-admin")
    await user.open("/items")
    # Bottom nav should be visible with navigation options
    await user.should_see("Vorrat")


async def test_items_page_shows_items_as_cards(user: TestUser) -> None:
    """Test that items are displayed as cards."""
    await user.open("/test-items-page-with-items")
    # Should see item names from test data
    await user.should_see("Tomaten")


async def test_items_page_shows_multiple_items(user: TestUser) -> None:
    """Test that multiple items are shown as cards."""
    await user.open("/test-items-page-with-items")
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")


async def test_items_page_shows_expiry_status(user: TestUser) -> None:
    """Test that expiry status is visible on items."""
    await user.open("/test-items-page-with-items")
    # Should see expiry info (MHD for frozen items)
    await user.should_see("MHD")


async def test_items_page_excludes_consumed_items(user: TestUser) -> None:
    """Test that consumed items are not shown."""
    await user.open("/test-items-page-with-consumed")
    # Should see active item
    await user.should_see("Aktiver Artikel")
    # Should NOT see consumed item (using should_not_see)


async def test_items_page_shows_empty_state(user: TestUser) -> None:
    """Test that empty state is shown when no items exist."""
    await user.open("/test-items-page-empty")
    await user.should_see("Keine Artikel")


async def test_items_page_shows_location(user: TestUser) -> None:
    """Test that item location is displayed."""
    await user.open("/test-items-page-with-items")
    await user.should_see("Tiefkühltruhe")


async def test_items_page_shows_quantity(user: TestUser) -> None:
    """Test that item quantity and unit are displayed."""
    await user.open("/test-items-page-with-items")
    await user.should_see("500 g")


# Search functionality tests (Issue #10)


async def test_items_page_shows_search_field(user: TestUser) -> None:
    """Test that search field is displayed at top of items page."""
    await user.open("/test-items-page-with-search")
    await user.should_see("Suchen")


async def test_items_page_search_filters_by_name(user: TestUser) -> None:
    """Test that search filters items by product name."""
    await user.open("/test-items-page-with-search")
    # Should see both items initially
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")
    # Type in search
    user.find("Suchen").type("Tomat")
    await user.should_see("Tomaten")
    await user.should_not_see("Hackfleisch")


async def test_items_page_search_case_insensitive(user: TestUser) -> None:
    """Test that search is case-insensitive."""
    await user.open("/test-items-page-with-search")
    # Search with lowercase
    user.find("Suchen").type("tomaten")
    await user.should_see("Tomaten")


async def test_items_page_search_empty_shows_all(user: TestUser) -> None:
    """Test that empty search shows all items."""
    await user.open("/test-items-page-with-search")
    # Initially empty search shows all
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")


async def test_items_page_search_no_results(user: TestUser) -> None:
    """Test that search with no matches shows appropriate message."""
    await user.open("/test-items-page-with-search")
    user.find("Suchen").type("xyz-nicht-vorhanden")
    await user.should_not_see("Tomaten")
    await user.should_not_see("Hackfleisch")
    await user.should_see("Keine Artikel")


# Consumed items toggle tests (Issue #17)


async def test_items_page_has_consumed_toggle(user: TestUser) -> None:
    """Test that items page has a toggle to show consumed items."""
    await user.open("/test-items-page-with-consumed-toggle")
    await user.should_see("Entnommene anzeigen")


async def test_items_page_toggle_shows_consumed_when_enabled(user: TestUser) -> None:
    """Test that consumed items are shown when toggle is enabled."""
    await user.open("/test-items-page-with-consumed-toggle-on")
    # Should see both active and consumed items
    await user.should_see("Aktiver Artikel")
    await user.should_see("Entnommener Artikel")


async def test_items_page_toggle_hides_consumed_when_disabled(user: TestUser) -> None:
    """Test that consumed items are hidden when toggle is disabled (default)."""
    await user.open("/test-items-page-with-consumed-toggle")
    # Should see only active item
    await user.should_see("Aktiver Artikel")
    # Consumed item should not be visible (checked via card count)


# Category filter tests (Issue #11)


async def test_items_page_shows_category_filter(user: TestUser) -> None:
    """Test that category filter chips are displayed."""
    await user.open("/test-items-page-with-categories")
    # Should see category filter chips
    await user.should_see("Gemüse")
    await user.should_see("Fleisch")


async def test_items_page_category_filter_shows_all_initially(user: TestUser) -> None:
    """Test that all items are shown when no category is selected."""
    await user.open("/test-items-page-with-categories")
    # Should see all items initially
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")
    await user.should_see("Karotten")


async def test_items_page_category_filter_filters_items(user: TestUser) -> None:
    """Test that selecting a category filters items."""
    await user.open("/test-items-page-with-categories")
    # Click on Gemüse category chip
    user.find("Gemüse").click()
    # Should see items with Gemüse category
    await user.should_see("Tomaten")
    await user.should_see("Karotten")
    # Should not see items without Gemüse category
    await user.should_not_see("Hackfleisch")


async def test_items_page_category_filter_multi_select(user: TestUser) -> None:
    """Test that multiple categories can be selected."""
    await user.open("/test-items-page-with-categories")
    # Click on both categories
    user.find("Gemüse").click()
    user.find("Fleisch").click()
    # Should see items from both categories
    await user.should_see("Tomaten")
    await user.should_see("Hackfleisch")
    await user.should_see("Karotten")


async def test_items_page_category_filter_deselect(user: TestUser) -> None:
    """Test that deselecting a category shows all items again."""
    await user.open("/test-items-page-with-categories")
    # Click to select
    user.find("Gemüse").click()
    await user.should_not_see("Hackfleisch")
    # Click again to deselect
    user.find("Gemüse").click()
    # Should see all items again
    await user.should_see("Hackfleisch")


async def test_items_page_category_filter_combined_with_search(user: TestUser) -> None:
    """Test that category filter works together with search."""
    await user.open("/test-items-page-with-categories")
    # Select Gemüse category
    user.find("Gemüse").click()
    # Should see Tomaten and Karotten
    await user.should_see("Tomaten")
    await user.should_see("Karotten")
    # Search for Tomaten
    user.find("Suchen").type("Tomat")
    # Should only see Tomaten (filtered by both category AND search)
    await user.should_see("Tomaten")
    await user.should_not_see("Karotten")


async def test_items_page_category_filter_no_results(user: TestUser) -> None:
    """Test that appropriate message is shown when filters yield no results."""
    await user.open("/test-items-page-with-categories")
    # Select Gemüse category
    user.find("Gemüse").click()
    # Search for something that doesn't exist in Gemüse
    user.find("Suchen").type("xyz-nicht-vorhanden")
    await user.should_see("Keine Artikel")


# Filter by location and item type tests (Issue #12)


async def test_items_page_has_location_filter(user: TestUser) -> None:
    """Test that items page has a location filter dropdown."""
    await user.open("/test-items-page-with-filters")
    await user.should_see("Lagerort")


async def test_items_page_has_item_type_filter(user: TestUser) -> None:
    """Test that items page has an item type filter dropdown."""
    await user.open("/test-items-page-with-filters")
    await user.should_see("Artikel-Typ")


async def test_items_page_location_filter_shows_all_option(user: TestUser) -> None:
    """Test that location filter has 'Alle' option."""
    await user.open("/test-items-page-with-filters")
    await user.should_see("Alle Lagerorte")


async def test_items_page_item_type_filter_shows_all_option(user: TestUser) -> None:
    """Test that item type filter has 'Alle' option."""
    await user.open("/test-items-page-with-filters")
    await user.should_see("Alle Typen")


async def test_items_page_location_filter_filters_items(user: TestUser) -> None:
    """Test that selecting a location filters items."""
    await user.open("/test-items-page-with-location-filter")
    # Should see item from Tiefkühltruhe
    await user.should_see("Gefrorene Tomaten")
    # Should NOT see item from Kühlschrank
    await user.should_not_see("Frische Milch")


async def test_items_page_item_type_filter_filters_items(user: TestUser) -> None:
    """Test that selecting an item type filters items."""
    await user.open("/test-items-page-with-type-filter")
    # Should see homemade frozen item
    await user.should_see("Selbst Eingefrorenes")
    # Should NOT see purchased fresh item
    await user.should_not_see("Frisch Gekauftes")


# Sorting functionality tests (Issue #13)


async def test_items_page_has_sort_dropdown(user: TestUser) -> None:
    """Test that items page has a sort dropdown with label."""
    await user.open("/test-items-page-with-sorting")
    await user.should_see("Sortierung")


async def test_items_page_sort_default_is_expiry(user: TestUser) -> None:
    """Test that default sort is by best before date (shown as selected value)."""
    await user.open("/test-items-page-with-sorting")
    # Default selected value should be best before date
    await user.should_see("Haltbarkeitsdatum")


async def test_items_page_has_sort_direction_toggle(user: TestUser) -> None:
    """Test that items page has ascending/descending toggle."""
    await user.open("/test-items-page-with-sorting")
    # Should see the direction toggle button
    await user.should_see("arrow_upward")


async def test_items_page_sort_by_expiry_default(user: TestUser) -> None:
    """Test that items are sorted by expiry date by default (ascending)."""
    await user.open("/test-items-page-with-sorting-data")
    # Item expiring soonest should appear first
    # "Bald Ablaufend" expires in 5 days, "Später Ablaufend" in 30 days
    await user.should_see("Bald Ablaufend")


async def test_items_page_sort_by_name(user: TestUser) -> None:
    """Test that items can be sorted by product name."""
    await user.open("/test-items-page-with-sorting-by-name")
    # "Apfel" comes before "Zwiebel" alphabetically
    await user.should_see("Apfel")


async def test_items_page_sort_descending(user: TestUser) -> None:
    """Test that sort direction can be toggled to descending."""
    await user.open("/test-items-page-with-sorting-desc")
    # Item expiring latest should appear first when descending
    await user.should_see("Später Ablaufend")
