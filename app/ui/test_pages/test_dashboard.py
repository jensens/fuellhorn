"""Test pages for Dashboard testing.

These pages test the dashboard's expiry calculation for different item types.
Bug #149: Dashboard was showing all items as expired because it used
best_before_date directly instead of calculating expiry via get_item_expiry_info().
"""

from ...database import get_session
from ...models.category import Category
from ...models.category_shelf_life import CategoryShelfLife
from ...models.category_shelf_life import StorageType
from ...models.item import Item
from ...models.item import ItemType
from ...models.location import Location
from ...models.location import LocationType
from datetime import date
from datetime import timedelta
from nicegui import ui
from sqlmodel import Session


def _create_test_location(
    session: Session,
    location_type: LocationType = LocationType.FROZEN,
) -> Location:
    """Create a test location."""
    location_id = 1 if location_type == LocationType.FROZEN else 2
    location = session.get(Location, location_id)
    if location:
        return location

    name = "Tiefkühltruhe" if location_type == LocationType.FROZEN else "Kühlschrank"
    location = Location(
        id=location_id,
        name=name,
        location_type=location_type,
        created_by=1,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def _create_test_category(session: Session, with_shelf_life: bool = True) -> Category:
    """Create a test category with optional shelf life config."""
    category = session.get(Category, 1)
    if category:
        return category

    category = Category(
        id=1,
        name="Gemüse",
        color="#00FF00",
        created_by=1,
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    # Add shelf life config for frozen storage (6-12 months)
    if with_shelf_life and category.id is not None:
        shelf_life = CategoryShelfLife(
            category_id=category.id,
            storage_type=StorageType.FROZEN,
            months_min=6,
            months_max=12,
        )
        session.add(shelf_life)
        session.commit()

    return category


def _create_shelf_life_item(
    session: Session,
    location: Location,
    category: Category,
    freeze_days_ago: int = 30,
) -> Item:
    """Create a shelf-life item (HOMEMADE_FROZEN) with freeze date."""
    freeze_date = date.today() - timedelta(days=freeze_days_ago)
    item = Item(
        product_name="Erbsen",
        best_before_date=freeze_date,
        freeze_date=freeze_date,
        quantity=500,
        unit="g",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=location.id,
        category_id=category.id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _create_mhd_item(
    session: Session,
    location: Location,
    mhd_days_from_now: int = 10,
) -> Item:
    """Create an MHD item (PURCHASED_FRESH) with best-before date."""
    best_before = date.today() + timedelta(days=mhd_days_from_now)
    item = Item(
        product_name="Joghurt",
        best_before_date=best_before,
        quantity=150,
        unit="g",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# =============================================================================
# Test pages for dashboard expiry calculation
# =============================================================================


@ui.page("/test-dashboard-shelf-life-ok")
def page_dashboard_shelf_life_ok() -> None:
    """Test page: HOMEMADE_FROZEN item frozen 30 days ago should show as fresh.

    With 6-12 months shelf life, this item's optimal date is ~5 months away.
    It should NOT be shown as "Abgelaufen".
    """
    with next(get_session()) as session:
        location = _create_test_location(session)
        category = _create_test_category(session, with_shelf_life=True)
        # Create item frozen 30 days ago - well within shelf life
        _create_shelf_life_item(session, location, category, freeze_days_ago=30)

    # Re-render dashboard (the actual page content)
    _render_dashboard_content()


@ui.page("/test-dashboard-mhd-ok")
def page_dashboard_mhd_ok() -> None:
    """Test page: PURCHASED_FRESH item with MHD 10 days in future."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        # MHD item with best_before 10 days in future - not expiring soon
        _create_mhd_item(session, location, mhd_days_from_now=10)

    _render_dashboard_content()


@ui.page("/test-dashboard-mhd-expired")
def page_dashboard_mhd_expired() -> None:
    """Test page: PURCHASED_FRESH item with MHD in the past (expired)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        # MHD item with best_before 2 days in past - expired
        _create_mhd_item(session, location, mhd_days_from_now=-2)

    _render_dashboard_content()


@ui.page("/test-dashboard-no-expiring")
def page_dashboard_no_expiring() -> None:
    """Test page: No items expiring in next 7 days."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        # MHD item with best_before 30 days in future - not expiring soon
        _create_mhd_item(session, location, mhd_days_from_now=30)

    _render_dashboard_content()


@ui.page("/test-dashboard-with-expiring-items")
def page_dashboard_with_expiring_items() -> None:
    """Test page: Items expiring in next 7 days (Issue #244)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        # Create 3 items expiring soon (within 7 days)
        _create_mhd_item(session, location, mhd_days_from_now=2)
        _create_mhd_item(session, location, mhd_days_from_now=4)
        _create_mhd_item(session, location, mhd_days_from_now=6)

    _render_dashboard_content()


@ui.page("/test-dashboard-at-a-glance")
def page_dashboard_at_a_glance() -> None:
    """Test page: Dashboard 'Auf einen Blick' tiles (Issue #245)."""
    with next(get_session()) as session:
        # Create locations
        location_frozen = _create_test_location(session, LocationType.FROZEN)
        location_chilled = _create_test_location(session, LocationType.CHILLED)

        # Create category
        category = _create_test_category(session, with_shelf_life=True)

        # Create some items
        _create_mhd_item(session, location_chilled, mhd_days_from_now=3)  # expiring
        _create_mhd_item(session, location_chilled, mhd_days_from_now=30)  # not expiring
        _create_shelf_life_item(session, location_frozen, category, freeze_days_ago=30)

    _render_at_a_glance_section()


def _render_at_a_glance_section() -> None:
    """Render 'Auf einen Blick' section for testing (Issue #245)."""
    from ...services import category_service
    from ...services import item_service
    from ...services import location_service

    with next(get_session()) as session:
        # Get counts
        all_items = item_service.get_all_items(session)
        active_items = [i for i in all_items if not i.is_consumed]
        expiring_items = item_service.get_items_expiring_soon(session, days=7)
        locations = location_service.get_all_locations(session)
        categories = category_service.get_all_categories(session)

        # Section title
        ui.label("Auf einen Blick").classes("sp-page-title text-base mb-3")

        # 2x2 Grid
        with ui.element("div").classes("grid grid-cols-2 gap-3"):
            # Tile 1: Artikel
            with ui.card().classes("sp-dashboard-card text-center cursor-pointer"):
                ui.label(str(len(active_items))).classes("sp-stats-number primary")
                ui.label("Artikel").classes("sp-stats-label")

            # Tile 2: Ablauf
            with ui.card().classes("sp-dashboard-card text-center cursor-pointer"):
                ui.label(str(len(expiring_items))).classes("sp-stats-number warning")
                ui.label("Ablauf").classes("sp-stats-label")

            # Tile 3: Lagerorte
            with ui.card().classes("sp-dashboard-card text-center cursor-pointer"):
                ui.label(str(len(locations))).classes("sp-stats-number primary")
                ui.label("Lagerorte").classes("sp-stats-label")

            # Tile 4: Kategorien
            with ui.card().classes("sp-dashboard-card text-center cursor-pointer"):
                ui.label(str(len(categories))).classes("sp-stats-number primary")
                ui.label("Kategorien").classes("sp-stats-label")


def _render_dashboard_content() -> None:
    """Render dashboard content for testing (without auth)."""
    from ...services import item_service

    # Inline rendering of dashboard content (simplified for testing)
    with next(get_session()) as session:
        expiring_items = item_service.get_items_expiring_soon(session, days=7)
        expiring_count = len(expiring_items)

        # Section title with count badge (Issue #244)
        ui.label(f"Bald ablaufend ({expiring_count})").classes("sp-page-title text-base mb-3")

        if expiring_items:
            for item in expiring_items[:5]:
                # Get proper expiry info
                optimal_date, max_date, best_before_date = item_service.get_item_expiry_info(
                    session,
                    item.id,  # type: ignore[arg-type]
                )

                # Determine the effective expiry date for status calculation
                if best_before_date is not None:
                    # MHD items: use best_before_date
                    effective_expiry = best_before_date
                elif optimal_date is not None:
                    # Shelf-life items: use optimal date for warning threshold
                    effective_expiry = optimal_date
                else:
                    # Fallback
                    effective_expiry = item.best_before_date

                days_until_expiry = (effective_expiry - date.today()).days

                # Status calculation
                if days_until_expiry < 0:
                    status_text = "Abgelaufen"
                elif days_until_expiry == 0:
                    status_text = "Heute abgelaufen"
                elif days_until_expiry <= 3:
                    status_text = f"Läuft ab: {'Morgen' if days_until_expiry == 1 else f'in {days_until_expiry} Tagen'}"
                else:
                    status_text = f"Läuft ab: in {days_until_expiry} Tagen"

                ui.label(f"{item.product_name}: {status_text}")

            # "Alle anzeigen" link (Issue #244)
            ui.link("Alle anzeigen", "/items?filter=expiring").classes("text-sm text-leaf hover:text-leaf-dark mt-2")
        else:
            # Improved empty state (Issue #244)
            with ui.card().classes("sp-dashboard-card w-full p-6 text-center"):
                ui.icon("eco").classes("text-4xl text-leaf mb-2")
                ui.label("Alles frisch!").classes("text-lg text-charcoal font-medium")
                ui.label("Keine Artikel laufen in den nächsten 7 Tagen ab.").classes("text-sm text-stone")


# =============================================================================
# Test pages for "Kürzlich hinzugefügt" section (Issue #248)
# =============================================================================


def _create_test_location_with_name(
    session: Session,
    location_type: LocationType,
    name: str,
    location_id: int,
) -> Location:
    """Create a test location with specific name and ID."""
    location = session.get(Location, location_id)
    if location:
        return location

    location = Location(
        id=location_id,
        name=name,
        location_type=location_type,
        created_by=1,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def _create_recently_added_item(
    session: Session,
    location: Location,
    product_name: str,
    days_ago: int = 0,
) -> Item:
    """Create an item with created_at set to specific days ago."""
    from datetime import datetime

    # Create item with best_before_date in the future
    best_before = date.today() + timedelta(days=30)
    item = Item(
        product_name=product_name,
        best_before_date=best_before,
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=location.id,
        created_by=1,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    # Update created_at to simulate item added X days ago
    if days_ago > 0:
        new_created_at = datetime.now() - timedelta(days=days_ago)
        item.created_at = new_created_at
        session.add(item)
        session.commit()
        session.refresh(item)

    return item


@ui.page("/test-dashboard-recently-added")
def page_dashboard_recently_added() -> None:
    """Test page: Recently added items section (Issue #248)."""
    with next(get_session()) as session:
        # Create locations
        location_frozen = _create_test_location_with_name(session, LocationType.FROZEN, "Tiefkühltruhe", 1)
        location_ambient = _create_test_location_with_name(session, LocationType.AMBIENT, "Vorratsraum", 3)

        # Create recently added items
        _create_recently_added_item(session, location_frozen, "Tomatensoße", days_ago=0)
        _create_recently_added_item(session, location_ambient, "Apfelmus", days_ago=1)

    _render_recently_added_section()


@ui.page("/test-dashboard-recently-added-today")
def page_dashboard_recently_added_today() -> None:
    """Test page: Item added today shows 'Heute' (Issue #248)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        _create_recently_added_item(session, location, "Frischer Joghurt", days_ago=0)

    _render_recently_added_section()


@ui.page("/test-dashboard-recently-added-yesterday")
def page_dashboard_recently_added_yesterday() -> None:
    """Test page: Item added yesterday shows 'Gestern' (Issue #248)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        _create_recently_added_item(session, location, "Gestern gekauft", days_ago=1)

    _render_recently_added_section()


@ui.page("/test-dashboard-recently-added-weekday")
def page_dashboard_recently_added_weekday() -> None:
    """Test page: Item added 3 days ago shows weekday (Issue #248)."""
    with next(get_session()) as session:
        location = _create_test_location(session, LocationType.CHILLED)
        _create_recently_added_item(session, location, "Vor 3 Tagen gekauft", days_ago=3)

    _render_recently_added_section()


@ui.page("/test-dashboard-recently-added-empty")
def page_dashboard_recently_added_empty() -> None:
    """Test page: No recently added items (section hidden) (Issue #248)."""
    # Don't create any items - section should be hidden
    _render_recently_added_section()


def _render_recently_added_section() -> None:
    """Render 'Kürzlich hinzugefügt' section for testing (Issue #248)."""
    from ..components.recently_added import create_recently_added_section

    with next(get_session()) as session:
        create_recently_added_section(session)
