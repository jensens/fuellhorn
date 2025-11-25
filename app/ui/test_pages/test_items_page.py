"""Test pages for Items Page UI testing.

These pages set up test data and allow testing the items page components.
"""

from ...database import get_session
from ...models.category import Category
from ...models.freeze_time_config import ItemType
from ...models.item import Item
from ...models.item import ItemCategory
from ...models.location import Location
from ...models.location import LocationType
from ..components import create_bottom_nav
from ..components import create_item_card
from datetime import date
from datetime import timedelta
from nicegui import app
from nicegui import ui
from sqlmodel import Session
from sqlmodel import select


def _create_test_location(session: Session) -> Location:
    """Create a test location."""
    location = session.get(Location, 1)
    if location:
        return location

    new_location = Location(
        id=1,
        name="Tiefkühltruhe",
        location_type=LocationType.FROZEN,
        created_by=1,
    )
    session.add(new_location)
    session.commit()
    session.refresh(new_location)
    return new_location


def _create_second_location(session: Session) -> Location:
    """Create a second test location (Kühlschrank)."""
    location = session.get(Location, 2)
    if location:
        return location

    new_location = Location(
        id=2,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=1,
    )
    session.add(new_location)
    session.commit()
    session.refresh(new_location)
    return new_location


def _create_test_category(session: Session, name: str = "Gemüse", id: int = 1) -> Category:
    """Create a test category."""
    category = session.get(Category, id)
    if category:
        return category

    new_category = Category(
        id=id,
        name=name,
        color="#00FF00",
        created_by=1,
    )
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category


def _create_test_item(
    session: Session,
    location: Location,
    product_name: str = "Tomaten",
    expiry_days_from_now: int = 30,
    quantity: float = 500,
    unit: str = "g",
    is_consumed: bool = False,
) -> Item:
    """Create a test item."""
    expiry_date = date.today() + timedelta(days=expiry_days_from_now)
    item = Item(
        product_name=product_name,
        best_before_date=date.today(),
        expiry_date=expiry_date,
        quantity=quantity,
        unit=unit,
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        created_by=1,
        is_consumed=is_consumed,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _create_test_item_with_type(
    session: Session,
    location: Location,
    product_name: str,
    item_type: ItemType,
    expiry_days_from_now: int = 30,
) -> Item:
    """Create a test item with specific item type."""
    expiry_date = date.today() + timedelta(days=expiry_days_from_now)
    item = Item(
        product_name=product_name,
        best_before_date=date.today(),
        expiry_date=expiry_date,
        quantity=500,
        unit="g",
        item_type=item_type,
        location_id=location.id,
        created_by=1,
        is_consumed=False,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _set_test_session() -> None:
    """Set test user session."""
    app.storage.user["authenticated"] = True
    app.storage.user["user_id"] = 1
    app.storage.user["username"] = "admin"


def _add_item_category(session: Session, item_id: int, category_id: int) -> None:
    """Add a category to an item."""
    item_category = ItemCategory(item_id=item_id, category_id=category_id)
    session.add(item_category)
    session.commit()


@ui.page("/test-login-admin")
def page_test_login_admin(next: str = "") -> None:
    """Test page to simulate admin login.

    Args:
        next: Optional URL to redirect to after login.
              If not provided, shows a confirmation page.
    """
    _set_test_session()
    if next:
        ui.navigate.to(next)
    else:
        ui.label("Angemeldet als admin")
        ui.label("Willkommen")


@ui.page("/test-items-page-with-items")
def page_items_with_items() -> None:
    """Test page with items displayed as cards."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create multiple test items
        item1 = _create_test_item(
            session,
            location,
            product_name="Tomaten",
            expiry_days_from_now=30,
            quantity=500,
            unit="g",
        )
        _create_test_item(
            session,
            location,
            product_name="Hackfleisch",
            expiry_days_from_now=10,
            quantity=750,
            unit="g",
        )

        # Add category to first item
        category = _create_test_category(session)
        item_category = ItemCategory(item_id=item1.id, category_id=category.id)
        session.add(item_category)
        session.commit()

        # Create page layout
        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get non-consumed items
            items = list(
                session.exec(
                    select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                ).all()
            )

            if items:
                for item in items:
                    create_item_card(item, session)
            else:
                ui.label("Keine Artikel vorhanden")

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-consumed")
def page_items_with_consumed() -> None:
    """Test page to verify consumed items are excluded."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create active item
        _create_test_item(
            session,
            location,
            product_name="Aktiver Artikel",
            expiry_days_from_now=30,
            is_consumed=False,
        )

        # Create consumed item (should not be shown)
        _create_test_item(
            session,
            location,
            product_name="Entnommener Artikel",
            expiry_days_from_now=30,
            is_consumed=True,
        )

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get non-consumed items only
            items = list(
                session.exec(
                    select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                ).all()
            )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-empty")
def page_items_empty() -> None:
    """Test page with no items (empty state)."""
    _set_test_session()

    with ui.column().classes("w-full"):
        ui.label("Vorrat").classes("text-h5")
        ui.label("Keine Artikel vorhanden")

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-search")
def page_items_with_search() -> None:
    """Test page with search functionality for items."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create multiple test items for search testing
        _create_test_item(
            session,
            location,
            product_name="Tomaten",
            expiry_days_from_now=30,
            quantity=500,
            unit="g",
        )
        _create_test_item(
            session,
            location,
            product_name="Hackfleisch",
            expiry_days_from_now=10,
            quantity=750,
            unit="g",
        )

        # Get all items for search
        all_items = list(
            session.exec(
                select(Item).where(Item.is_consumed.is_(False))  # type: ignore
            ).all()
        )

        # Create page layout with search
        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Container for items
            items_container = ui.column().classes("w-full")

            def update_items(query: str) -> None:
                """Update displayed items based on search query."""
                items_container.clear()
                search_term = query.lower() if query else ""

                filtered_items = [item for item in all_items if search_term in item.product_name.lower()]

                with items_container:
                    if filtered_items:
                        for item in filtered_items:
                            create_item_card(item, session)
                    else:
                        ui.label("Keine Artikel gefunden").classes("text-gray-500")

            # Search input with on_change callback for live filtering
            ui.input(
                label="Suchen",
                placeholder="Produktname...",
                on_change=lambda e: update_items(e.value),
            ).classes("w-full")

            # Initial render with empty query
            update_items("")

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-consumed-toggle")
def page_items_with_consumed_toggle() -> None:
    """Test page with consumed toggle (default: OFF)."""
    _set_test_session()
    # Set browser storage to default (show_consumed = False)
    app.storage.browser["show_consumed_items"] = False

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create active item
        _create_test_item(
            session,
            location,
            product_name="Aktiver Artikel",
            expiry_days_from_now=30,
            is_consumed=False,
        )

        # Create consumed item (should not be shown by default)
        _create_test_item(
            session,
            location,
            product_name="Entnommener Artikel",
            expiry_days_from_now=30,
            is_consumed=True,
        )

        show_consumed = app.storage.browser.get("show_consumed_items", False)

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Toggle for showing consumed items
            ui.switch("Entnommene anzeigen", value=show_consumed)

            # Get items based on filter
            if show_consumed:
                items = list(session.exec(select(Item)).all())
            else:
                items = list(
                    session.exec(
                        select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                    ).all()
                )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-consumed-toggle-on")
def page_items_with_consumed_toggle_on() -> None:
    """Test page with consumed toggle enabled (show all items)."""
    _set_test_session()
    # Set browser storage to show consumed items
    app.storage.browser["show_consumed_items"] = True

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create active item
        _create_test_item(
            session,
            location,
            product_name="Aktiver Artikel",
            expiry_days_from_now=30,
            is_consumed=False,
        )

        # Create consumed item (should be shown when toggle is ON)
        _create_test_item(
            session,
            location,
            product_name="Entnommener Artikel",
            expiry_days_from_now=30,
            is_consumed=True,
        )

        show_consumed = app.storage.browser.get("show_consumed_items", False)

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Toggle for showing consumed items
            ui.switch("Entnommene anzeigen", value=show_consumed)

            # Get items based on filter (show_consumed = True means show all)
            if show_consumed:
                items = list(session.exec(select(Item)).all())
            else:
                items = list(
                    session.exec(
                        select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                    ).all()
                )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


# Category filter test page (Issue #11)


@ui.page("/test-items-page-with-categories")
def page_items_with_categories() -> None:
    """Test page with category filter functionality for items."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create categories
        cat_gemuese = _create_test_category(session, name="Gemüse", id=1)
        cat_fleisch = _create_test_category(session, name="Fleisch", id=2)

        # Create test items with different categories
        item_tomaten = _create_test_item(
            session,
            location,
            product_name="Tomaten",
            expiry_days_from_now=30,
            quantity=500,
            unit="g",
        )
        _add_item_category(session, item_tomaten.id, cat_gemuese.id)  # type: ignore

        item_hackfleisch = _create_test_item(
            session,
            location,
            product_name="Hackfleisch",
            expiry_days_from_now=10,
            quantity=750,
            unit="g",
        )
        _add_item_category(session, item_hackfleisch.id, cat_fleisch.id)  # type: ignore

        item_karotten = _create_test_item(
            session,
            location,
            product_name="Karotten",
            expiry_days_from_now=20,
            quantity=300,
            unit="g",
        )
        _add_item_category(session, item_karotten.id, cat_gemuese.id)  # type: ignore

        # Get all items and categories
        all_items = list(
            session.exec(
                select(Item).where(Item.is_consumed.is_(False))  # type: ignore
            ).all()
        )
        all_categories = list(session.exec(select(Category)).all())

        # Build item-to-categories mapping
        item_category_map: dict[int, set[int]] = {}
        for item in all_items:
            item_cats = session.exec(select(ItemCategory).where(ItemCategory.item_id == item.id)).all()
            item_category_map[item.id] = {ic.category_id for ic in item_cats}  # type: ignore

        # State for filters
        selected_categories: set[int] = set()
        chip_elements: dict[int, ui.button] = {}

        # Create page layout
        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Search input (created first, connected later)
            search_input = ui.input(
                label="Suchen",
                placeholder="Produktname...",
            ).classes("w-full")

            # Category filter chips
            with ui.row().classes("w-full gap-2 flex-wrap my-2"):

                def update_chip_style(cat_id: int) -> None:
                    """Update chip appearance based on selection state."""
                    chip = chip_elements.get(cat_id)
                    if chip:
                        if cat_id in selected_categories:
                            chip.classes(remove="bg-gray-200", add="bg-primary text-white")
                        else:
                            chip.classes(remove="bg-primary text-white", add="bg-gray-200")

                def toggle_category(cat_id: int) -> None:
                    """Toggle category selection."""
                    if cat_id in selected_categories:
                        selected_categories.remove(cat_id)
                    else:
                        selected_categories.add(cat_id)
                    update_chip_style(cat_id)
                    update_items_display()

                for cat in all_categories:
                    chip = ui.button(
                        cat.name,
                        on_click=lambda _, cid=cat.id: toggle_category(cid),
                    ).classes("bg-gray-200 text-gray-800 rounded-full px-4 py-1 text-sm")
                    chip_elements[cat.id] = chip  # type: ignore

            # Container for items
            items_container = ui.column().classes("w-full")

            def update_items_display() -> None:
                """Update displayed items based on search and category filters."""
                items_container.clear()
                search_term = search_input.value.lower() if search_input.value else ""

                filtered_items = list(all_items)

                # Filter by search term
                if search_term:
                    filtered_items = [item for item in filtered_items if search_term in item.product_name.lower()]

                # Filter by selected categories (OR logic: show if item has ANY selected category)
                if selected_categories:
                    filtered_items = [
                        item
                        for item in filtered_items
                        if item_category_map.get(item.id, set()) & selected_categories  # type: ignore
                    ]

                with items_container:
                    if filtered_items:
                        for item in filtered_items:
                            create_item_card(item, session)
                    else:
                        ui.label("Keine Artikel gefunden").classes("text-gray-500")

            # Connect search input to update function (after update_items_display is defined)
            search_input.on_value_change(lambda _: update_items_display())

            # Initial render
            update_items_display()

    create_bottom_nav(current_page="items")


# Location and item type filter test pages (Issue #12)


@ui.page("/test-items-page-with-filters")
def page_items_with_filters() -> None:
    """Test page with location and item type filter dropdowns."""
    _set_test_session()

    with next(get_session()) as session:
        location1 = _create_test_location(session)
        location2 = _create_second_location(session)

        # Create items in different locations
        _create_test_item(
            session,
            location1,
            product_name="Gefrorene Tomaten",
            expiry_days_from_now=30,
        )
        _create_test_item(
            session,
            location2,
            product_name="Frische Milch",
            expiry_days_from_now=7,
        )

        locations = [location1, location2]

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Filter row
            with ui.row().classes("w-full gap-2"):
                # Location filter
                ui.select(
                    label="Lagerort",
                    options={0: "Alle Lagerorte"} | {loc.id: loc.name for loc in locations},
                    value=0,
                ).classes("flex-1")

                # Item type filter
                ui.select(
                    label="Artikel-Typ",
                    options={
                        "": "Alle Typen",
                        ItemType.PURCHASED_FRESH.value: "Frisch gekauft",
                        ItemType.PURCHASED_FROZEN.value: "TK-Ware gekauft",
                        ItemType.PURCHASED_THEN_FROZEN.value: "Gekauft → eingefroren",
                        ItemType.HOMEMADE_FROZEN.value: "Selbst eingefroren",
                        ItemType.HOMEMADE_PRESERVED.value: "Eingemacht",
                    },
                    value="",
                ).classes("flex-1")

            # Get all items
            items = list(
                session.exec(
                    select(Item).where(Item.is_consumed.is_(False))  # type: ignore
                ).all()
            )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-location-filter")
def page_items_with_location_filter() -> None:
    """Test page with location filter pre-selected to Tiefkühltruhe."""
    _set_test_session()

    with next(get_session()) as session:
        location1 = _create_test_location(session)  # Tiefkühltruhe
        location2 = _create_second_location(session)  # Kühlschrank

        # Create items in different locations
        _create_test_item(
            session,
            location1,
            product_name="Gefrorene Tomaten",
            expiry_days_from_now=30,
        )
        _create_test_item(
            session,
            location2,
            product_name="Frische Milch",
            expiry_days_from_now=7,
        )

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get items filtered by location (Tiefkühltruhe only)
            items = list(
                session.exec(
                    select(Item).where(
                        Item.is_consumed.is_(False),  # type: ignore
                        Item.location_id == location1.id,
                    )
                ).all()
            )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")


@ui.page("/test-items-page-with-type-filter")
def page_items_with_type_filter() -> None:
    """Test page with item type filter pre-selected to HOMEMADE_FROZEN."""
    _set_test_session()

    with next(get_session()) as session:
        location = _create_test_location(session)

        # Create items with different types
        _create_test_item_with_type(
            session,
            location,
            product_name="Selbst Eingefrorenes",
            item_type=ItemType.HOMEMADE_FROZEN,
        )
        _create_test_item_with_type(
            session,
            location,
            product_name="Frisch Gekauftes",
            item_type=ItemType.PURCHASED_FRESH,
        )

        with ui.column().classes("w-full"):
            ui.label("Vorrat").classes("text-h5")

            # Get items filtered by type (HOMEMADE_FROZEN only)
            items = list(
                session.exec(
                    select(Item).where(
                        Item.is_consumed.is_(False),  # type: ignore
                        Item.item_type == ItemType.HOMEMADE_FROZEN,
                    )
                ).all()
            )

            for item in items:
                create_item_card(item, session)

    create_bottom_nav(current_page="items")
