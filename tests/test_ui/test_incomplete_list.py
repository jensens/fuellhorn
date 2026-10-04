"""UI: Liste der unvollständigen Artikel, in der man bleibt (Issue #463).

Oben im Warmen wird ergänzt, was unten im Keller gefehlt hat. Die Liste ist eine eigene
Seite, kein Filter, den man beim Navigieren verliert: Ergänzen führt zurück in die Liste,
die Zeile verschwindet erst, wenn nichts mehr fehlt.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    with Session(isolated_test_database) as session:
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=1)
        vegetables = Category(name="Gemüse", created_by=1)
        session.add_all([freezer, vegetables])
        session.commit()
        session.refresh(freezer)
        session.refresh(vegetables)
        assert freezer.id is not None and vegetables.id is not None
        session.add(
            CategoryShelfLife(category_id=vegetables.id, storage_type=StorageType.FROZEN, months_min=6, months_max=12)
        )
        session.commit()
        return {"freezer": freezer.id, "vegetables": vegetables.id}


def _quick(database, world: dict[str, int], name: str) -> int:
    with Session(database) as session:
        item = item_service.quick_create_item(
            session,
            product_name=name,
            quantity=3,
            unit="Beutel",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
            created_by=1,
        )
        assert item.id is not None
        return item.id


async def test_list_names_the_gaps_and_the_location(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    _quick(isolated_test_database, world, "Erbsen aus Garten")

    await logged_in_user.open("/items/incomplete")

    await logged_in_user.should_see("Erbsen aus Garten")
    await logged_in_user.should_see("Tiefkühltruhe")
    await logged_in_user.should_see("Datum")
    await logged_in_user.should_see("Einfrierdatum")
    await logged_in_user.should_see("Kategorie")


async def test_complete_items_are_not_listed(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    with Session(isolated_test_database) as session:
        item_service.create_item(
            session,
            product_name="Bohnen",
            best_before_date=date(2026, 2, 1),
            quantity=1,
            unit="Beutel",
            item_type=ItemType.HOMEMADE_FROZEN,
            location_id=world["freezer"],
            created_by=1,
            category_id=world["vegetables"],
            freeze_date=date(2026, 3, 1),
        )

    await logged_in_user.open("/items/incomplete")

    await logged_in_user.should_see(marker="incomplete-empty")
    await logged_in_user.should_not_see("Bohnen")


async def test_completing_an_item_returns_to_the_list_and_removes_the_row(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Akzeptanzkriterium: Ergänzen kehrt in die Liste zurück, die Zeile verschwindet."""
    item_id = _quick(isolated_test_database, world, "Kirschen")

    await logged_in_user.open("/items/incomplete")
    logged_in_user.find(marker=f"incomplete-item-{item_id}").click()
    await logged_in_user.should_see("Artikel bearbeiten")

    logged_in_user.find(marker=f"category-chip-{world['vegetables']}").click()
    for marker, value in (("edit-date-input", "01.03.2026"), ("edit-freeze-date-input", "02.03.2026")):
        field = logged_in_user.find(marker=marker)
        field.clear()
        field.type(value)
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    await logged_in_user.should_see(marker="incomplete-empty", retries=50)
    with Session(isolated_test_database) as session:
        item = session.get(Item, item_id)
    assert item is not None
    assert (item.best_before_date, item.freeze_date, item.category_id) == (
        date(2026, 3, 1),
        date(2026, 3, 2),
        world["vegetables"],
    )


async def test_partial_correction_is_allowed_and_keeps_the_row(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Nur die Menge richtigstellen muss gehen, ohne das Datum zu erfinden."""
    item_id = _quick(isolated_test_database, world, "Zwetschken")

    await logged_in_user.open(f"/items/{item_id}/edit?back=/items/incomplete")
    await logged_in_user.should_see("Artikel bearbeiten")
    logged_in_user.find(kind=ui.number).elements.pop().set_value(5)
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    await logged_in_user.should_see("Zwetschken", retries=50)
    with Session(isolated_test_database) as session:
        item = session.get(Item, item_id)
    assert item is not None
    assert (item.quantity, item.best_before_date) == (5, None)


async def test_dashboard_links_to_the_list_with_a_count(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    _quick(isolated_test_database, world, "Erbsen")
    _quick(isolated_test_database, world, "Kirschen")

    await logged_in_user.open("/dashboard")

    await logged_in_user.should_see("Nachpflegen (2)")
    logged_in_user.find(marker="dashboard-incomplete").click()
    await logged_in_user.should_see("Erbsen", retries=50)
