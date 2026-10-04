"""Bulk-Daten für Artikel-Karten mit konstanter Query-Zahl (Issue #393).

Vorher holte jede Karte Lagerort, Kategorie, Haltbarkeit und Entnahmesumme einzeln:
~2 echte SQL-Queries pro Artikel, bei 500 Artikeln ~1000 Queries pro Render.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import expiry_service
from app.services import item_service
from app.services.item_rows import ItemRow
from app.services.item_rows import get_item_rows
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from datetime import timedelta
import pytest
from sqlalchemy import event
from sqlmodel import Session


@contextmanager
def count_queries(session: Session) -> Iterator[list[str]]:
    """Zählt SQL-Statements (ohne Transaktionssteuerung), die über die Engine der Session laufen."""
    statements: list[str] = []
    engine = session.get_bind()

    def _record(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _record)


@pytest.fixture(name="fifty_items")
def fifty_items_fixture(session: Session, test_admin: User) -> list[Item]:
    """50 Artikel über 3 Lagerorte und 3 Kategorien (eine mit FROZEN-Haltbarkeit), 10 davon mit Entnahmen."""
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=test_admin.id)
    cellar = Location(name="Keller", location_type=LocationType.AMBIENT, created_by=test_admin.id)
    soups = Category(name="Suppen", created_by=test_admin.id)
    dairy = Category(name="Milchprodukte", created_by=test_admin.id)
    jam = Category(name="Marmelade", created_by=test_admin.id)
    session.add_all([fridge, freezer, cellar, soups, dairy, jam])
    session.commit()
    for obj in (fridge, freezer, cellar, soups, dairy, jam):
        session.refresh(obj)
    assert soups.id is not None and jam.id is not None
    session.add(CategoryShelfLife(category_id=soups.id, storage_type=StorageType.FROZEN, months_min=2, months_max=3))
    session.add(CategoryShelfLife(category_id=jam.id, storage_type=StorageType.AMBIENT, months_min=6, months_max=12))
    session.commit()

    items: list[Item] = []
    for n in range(50):
        if n % 3 == 0:
            item = item_service.create_item(
                session,
                product_name=f"Suppe {n}",
                best_before_date=date.today() - timedelta(days=n),
                quantity=2,
                unit="l",
                item_type=ItemType.HOMEMADE_FROZEN,
                location_id=freezer.id,
                created_by=test_admin.id,
                category_id=soups.id,
                freeze_date=date.today() - timedelta(days=n),
            )
        elif n % 3 == 1:
            item = item_service.create_item(
                session,
                product_name=f"Joghurt {n}",
                best_before_date=date.today() + timedelta(days=n),
                quantity=4,
                unit="Stück",
                item_type=ItemType.PURCHASED_FRESH,
                location_id=fridge.id,
                created_by=test_admin.id,
                category_id=dairy.id,
            )
        else:
            item = item_service.create_item(
                session,
                product_name=f"Marmelade {n}",
                best_before_date=date.today() - timedelta(days=n),
                quantity=3,
                unit="Glas",
                item_type=ItemType.HOMEMADE_PRESERVED,
                location_id=cellar.id,
                created_by=test_admin.id,
                category_id=jam.id,
            )
        items.append(item)
    for item in items[:10]:
        assert item.id is not None
        item_service.withdraw_partial(session, item.id, 1, test_admin.id)
    for item in items:
        session.refresh(item)
    return items


def test_fifty_items_need_at_most_five_queries(session: Session, fifty_items: list[Item]) -> None:
    """Akzeptanzkriterium: Rendern von 50 Artikeln ≤ 5 Queries (hier: die gesamte Datenbeschaffung)."""
    with count_queries(session) as statements:
        rows = get_item_rows(session, fifty_items)

    assert len(rows) == 50
    assert len(statements) <= 5, "\n".join(statements)


def test_rows_carry_location_category_initial_quantity_and_expiry(session: Session, fifty_items: list[Item]) -> None:
    rows = {row.item.id: row for row in get_item_rows(session, fifty_items)}

    withdrawn = rows[fifty_items[0].id]  # Suppe 0, 1 l entnommen
    assert isinstance(withdrawn, ItemRow)
    assert withdrawn.location is not None and withdrawn.location.name == "Truhe"
    assert withdrawn.category is not None and withdrawn.category.name == "Suppen"
    assert (withdrawn.item.quantity, withdrawn.initial_quantity) == (1.0, 2.0)

    untouched = rows[fifty_items[13].id]  # Joghurt 13, keine Entnahme
    assert untouched.initial_quantity == untouched.item.quantity == 4.0
    assert untouched.location is not None and untouched.location.name == "Kühlschrank"

    for item in fifty_items:
        assert item.id is not None
        assert rows[item.id].expiry_view == expiry_service.get_item_expiry_view(session, item)


def test_rows_keep_input_order_and_tolerate_missing_relations(session: Session, test_admin: User) -> None:
    """Reihenfolge wie übergeben; Artikel ohne Kategorie bekommt category=None statt eines Fehlers."""
    assert test_admin.id is not None
    fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=test_admin.id)
    session.add(fridge)
    session.commit()
    session.refresh(fridge)
    assert fridge.id is not None
    second = item_service.create_item(
        session,
        product_name="B",
        best_before_date=date.today(),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=fridge.id,
        created_by=test_admin.id,
    )
    first = item_service.create_item(
        session,
        product_name="A",
        best_before_date=date.today(),
        quantity=1,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=fridge.id,
        created_by=test_admin.id,
    )

    rows = get_item_rows(session, [first, second])

    assert [row.item.product_name for row in rows] == ["A", "B"]
    assert all(row.category is None for row in rows)
    assert get_item_rows(session, []) == []
