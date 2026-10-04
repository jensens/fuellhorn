"""Tests: stabile Kategorie-Reihenfolge bei gleicher sort_order (Issue #467).

PostgreSQL garantiert bei gleichem Sortierwert keine Reihenfolge. SQLite liefert
Gleichstände in Einfügereihenfolge (auch mit ``PRAGMA reverse_unordered_selects``),
der Fehler ist dort also nicht als falsche Reihenfolge sichtbar. Geprüft wird
deshalb, dass die Abfragen ``id`` als zweites Sortierkriterium tragen.
"""

from app.models.category import Category
from app.models.item import ItemType
from app.models.user import User
from app.services import category_service
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
import re
from sqlalchemy import event
from sqlmodel import Session


@contextmanager
def _category_queries(session: Session) -> Iterator[list[str]]:
    """Alle SELECTs auf die Kategorie-Tabelle mitschreiben."""
    statements: list[str] = []
    engine = session.get_bind()

    def record(conn, cursor, statement: str, parameters, context, executemany) -> None:  # noqa: ANN001
        if re.search(r"FROM category\b", statement):
            statements.append(" ".join(statement.split()))

    event.listen(engine, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", record)


def _assert_ordered_by_sort_order_then_id(session: Session, call: Callable[[], object]) -> None:
    with _category_queries(session) as statements:
        call()
    ordered = [s for s in statements if "ORDER BY" in s]
    assert ordered, statements
    for statement in ordered:
        assert "ORDER BY category.sort_order, category.id" in statement, statement


def _seed_categories(session: Session, admin: User) -> None:
    group = Category(name="Gruppe", created_by=admin.id)  # type: ignore[arg-type]
    session.add(group)
    session.commit()
    session.add_all(
        [
            Category(name=name, parent_id=group.id, created_by=admin.id)  # type: ignore[arg-type]
            for name in ("Erste", "Zweite")
        ]
    )
    session.commit()


def test_get_all_categories_breaks_ties_by_id(session: Session, test_admin: User) -> None:
    _seed_categories(session, test_admin)

    _assert_ordered_by_sort_order_then_id(session, lambda: category_service.get_all_categories(session))


def test_categories_for_fresh_items_break_ties_by_id(session: Session, test_admin: User) -> None:
    _seed_categories(session, test_admin)

    _assert_ordered_by_sort_order_then_id(
        session, lambda: category_service.get_categories_for_item_type(session, ItemType.PURCHASED_FRESH)
    )


def test_categories_for_frozen_items_break_ties_by_id(session: Session, test_admin: User) -> None:
    _seed_categories(session, test_admin)

    _assert_ordered_by_sort_order_then_id(
        session, lambda: category_service.get_categories_for_item_type(session, ItemType.HOMEMADE_FROZEN)
    )
