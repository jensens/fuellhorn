"""Anzeigefertige Daten für Artikel-Karten mit konstanter Query-Zahl (Issue #393).

Die Karte (``app/ui/components/item_card.py``) fragte Lagerort, Kategorie,
Haltbarkeit und Entnahmesumme pro Artikel einzeln ab. ``get_item_rows`` lädt alles
für eine ganze Liste in fünf Abfragen: Lagerorte, Kategorien, Entnahmesummen,
Haltbarkeits-Index und Schwellen.
"""

from ..models.category import Category
from ..models.item import Item
from ..models.location import Location
from ..models.withdrawal import Withdrawal
from . import expiry_service
from .expiry_service import ExpiryView
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from sqlalchemy import func
from sqlmodel import Session
from sqlmodel import col
from sqlmodel import select


@dataclass(frozen=True)
class ItemRow:
    """Ein Artikel samt allem, was die Karte anzeigt."""

    item: Item
    location: Location | None
    category: Category | None
    initial_quantity: float
    expiry_view: ExpiryView


def get_item_rows(session: Session, items: Sequence[Item], today: date | None = None) -> list[ItemRow]:
    """Baut ``ItemRow`` für alle Artikel in Eingabereihenfolge; Query-Zahl unabhängig von der Anzahl.

    Artikel ohne ID (nicht gespeichert) werden übersprungen; fehlende Lagerorte oder
    Kategorien ergeben ``None`` statt eines Fehlers.
    """
    saved = [item for item in items if item.id is not None]
    if not saved:
        return []

    location_ids = {item.location_id for item in saved}
    locations = {
        location.id: location
        for location in session.exec(select(Location).where(col(Location.id).in_(location_ids))).all()
    }

    category_ids = {item.category_id for item in saved if item.category_id is not None}
    categories: dict[int | None, Category] = {}
    if category_ids:
        categories = {
            category.id: category
            for category in session.exec(select(Category).where(col(Category.id).in_(category_ids))).all()
        }

    item_ids = [item.id for item in saved if item.id is not None]
    withdrawn_by_item: dict[int, float] = dict(
        session.exec(
            select(Withdrawal.item_id, func.coalesce(func.sum(Withdrawal.quantity), 0.0))
            .where(col(Withdrawal.item_id).in_(item_ids))
            .group_by(col(Withdrawal.item_id))
        ).all()
    )

    views = expiry_service.get_expiry_views(session, saved, today)

    return [
        ItemRow(
            item=item,
            location=locations.get(item.location_id),
            category=categories.get(item.category_id) if item.category_id is not None else None,
            initial_quantity=item.quantity + withdrawn_by_item.get(item.id, 0.0),  # type: ignore[arg-type]
            expiry_view=views[item.id],  # type: ignore[index]
        )
        for item in saved
    ]
