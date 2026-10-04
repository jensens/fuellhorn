"""Performance-Eigenschaften der Vorratsliste (Issue #393): konstante Query-Zahl, Debounce, ein Refresh."""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import item_service
from datetime import date
from datetime import timedelta
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlalchemy import event
from sqlmodel import Session


@pytest.fixture(name="fifty_items")
def fifty_items_fixture(isolated_test_database) -> list[int]:
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=1)
        soups = Category(name="Suppen", created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, freezer, soups, dairy])
        session.commit()
        for obj in (fridge, freezer, soups, dairy):
            session.refresh(obj)
        assert soups.id is not None and fridge.id is not None and freezer.id is not None
        session.add(
            CategoryShelfLife(category_id=soups.id, storage_type=StorageType.FROZEN, months_min=2, months_max=3)
        )
        session.commit()
        ids: list[int] = []
        for n in range(50):
            if n % 2:
                item = item_service.create_item(
                    session,
                    product_name=f"Suppe {n}",
                    best_before_date=date.today() - timedelta(days=n),
                    quantity=2,
                    unit="l",
                    item_type=ItemType.HOMEMADE_FROZEN,
                    location_id=freezer.id,
                    created_by=1,
                    category_id=soups.id,
                    freeze_date=date.today() - timedelta(days=n),
                )
            else:
                item = item_service.create_item(
                    session,
                    product_name=f"Joghurt {n}",
                    best_before_date=date.today() + timedelta(days=n),
                    quantity=4,
                    unit="Stück",
                    item_type=ItemType.PURCHASED_FRESH,
                    location_id=fridge.id,
                    created_by=1,
                    category_id=dairy.id,
                )
            assert item.id is not None
            ids.append(item.id)
        for item_id in ids[:5]:
            item_service.withdraw_partial(session, item_id, 1, 1)
        return ids


async def test_items_page_renders_fifty_items_with_constant_query_count(
    logged_in_user: User, isolated_test_database, fifty_items: list[int]
) -> None:
    """Seitenaufbau mit 50 Karten braucht höchstens 12 Queries (vorher ~2 pro Karte)."""
    statements: list[str] = []

    def _record(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        statements.append(statement)

    event.listen(isolated_test_database, "before_cursor_execute", _record)
    try:
        await logged_in_user.open("/items")
        await logged_in_user.should_see("Suppe 1")
    finally:
        event.remove(isolated_test_database, "before_cursor_execute", _record)

    page_statements = [s for s in statements if "users" not in s.lower() or "item" in s.lower()]
    assert len(page_statements) <= 12, "\n".join(statements)


async def test_search_input_is_debounced(logged_in_user: User) -> None:
    """Die Suche rendert nicht bei jedem Tastendruck: Quasar-Debounce 300 ms am Eingabefeld."""
    await logged_in_user.open("/items")

    (search,) = [e for e in logged_in_user.find(kind=ui.input).elements if e._props.get("label") == "Suchen"]

    assert str(search._props.get("debounce")) == "300"


async def test_withdrawal_from_sheet_refreshes_list_once(
    logged_in_user: User, isolated_test_database, fifty_items: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """on_withdraw und on_close riefen beide refresh_items → doppelter Render; jetzt genau einer."""
    calls: list[int] = []
    original = item_service.get_active_items

    def _counting(session: Session) -> list[Item]:
        calls.append(1)
        return original(session)

    monkeypatch.setattr(item_service, "get_active_items", _counting)

    await logged_in_user.open("/items")
    await logged_in_user.should_see("Joghurt 0")
    calls.clear()

    logged_in_user.find(marker=f"item-consume-{fifty_items[0]}").click()
    await logged_in_user.should_see("Teilentnahme")
    logged_in_user.find("Teilentnahme").click()
    await logged_in_user.should_see("Menge entnehmen")
    logged_in_user.find(kind=ui.number).elements.pop().set_value(1)
    logged_in_user.find("Bestätigen").click()
    await logged_in_user.should_see("entnommen")

    assert len(calls) == 1
