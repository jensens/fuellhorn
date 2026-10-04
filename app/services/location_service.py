"""Location service - Business logic for location management."""

from ..models.item import Item
from ..models.item import ItemType
from ..models.location import Location
from ..models.location import LocationType
from ..services.errors import DuplicateNameError
from ..services.validation import require_non_empty
from ..services.validation import validate_hex_color
from sqlmodel import Session
from sqlmodel import col
from sqlmodel import func
from sqlmodel import or_
from sqlmodel import select


def get_valid_location_types(item_type: ItemType) -> list[LocationType]:
    """Get valid location types for a given item type.

    Args:
        item_type: The type of item

    Returns:
        List of valid LocationTypes for this item type
    """
    if item_type in {
        ItemType.PURCHASED_FROZEN,
        ItemType.PURCHASED_THEN_FROZEN,
        ItemType.HOMEMADE_FROZEN,
    }:
        return [LocationType.FROZEN]
    elif item_type in {ItemType.PURCHASED_FRESH, ItemType.HOMEMADE_PRESERVED}:
        return [LocationType.AMBIENT, LocationType.CHILLED]
    else:
        # Fallback (should not happen with current ItemType enum)
        return [LocationType.FROZEN, LocationType.CHILLED, LocationType.AMBIENT]


def get_locations_for_item_type(
    session: Session, item_type: ItemType, *, include_location_id: int | None = None
) -> list[Location]:
    """Get active locations filtered by valid types for the given item type.

    Deaktivierte Lagerorte werden ausgeblendet (Issue #379). ``include_location_id``
    hält den aktuellen Lagerort eines bestehenden Artikels wählbar, auch wenn er
    inzwischen deaktiviert wurde (Edit-View).

    Args:
        session: Database session
        item_type: The type of item to filter locations for
        include_location_id: Lagerort, der unabhängig von is_active enthalten sein soll

    Returns:
        List of locations that are valid for this item type
    """
    valid_types = get_valid_location_types(item_type)
    active_or_current = col(Location.is_active) == True  # noqa: E712 - SQL-Ausdruck, kein Python-Vergleich
    if include_location_id is not None:
        active_or_current = or_(active_or_current, col(Location.id) == include_location_id)
    return list(
        session.exec(
            select(Location).where(col(Location.location_type).in_(valid_types)).where(active_or_current)
        ).all()
    )


def create_location(
    session: Session,
    name: str,
    location_type: LocationType,
    created_by: int,
    description: str | None = None,
    color: str | None = None,
) -> Location:
    """Create a new location.

    Args:
        session: Database session
        name: Location name (case-insensitive unique)
        location_type: Type of storage location (frozen/chilled/ambient)
        created_by: User ID who created the location
        description: Optional description of the location
        color: Optional hex color code (e.g., "#FF5733")

    Returns:
        Created location

    Raises:
        ServiceValidationError: leerer Name oder ungültige Farbe (Issue #383)
        DuplicateNameError: If location with same name already exists
    """
    name = require_non_empty(name, "Lagerortname")
    color = validate_hex_color(color)

    # Check for duplicate name (case-insensitive)
    existing = session.exec(
        select(Location).where(Location.name.ilike(name))  # type: ignore
    ).first()

    if existing:
        raise DuplicateNameError("name", existing.name, "Lagerort")

    location = Location(
        name=name,
        location_type=location_type,
        created_by=created_by,
        description=description,
        color=color,
    )

    session.add(location)
    session.commit()
    session.refresh(location)

    return location


def get_all_locations(session: Session) -> list[Location]:
    """Get all locations.

    Args:
        session: Database session

    Returns:
        List of all locations
    """
    return list(session.exec(select(Location)).all())


def get_location(session: Session, id: int) -> Location:
    """Get location by ID.

    Args:
        session: Database session
        id: Location ID

    Returns:
        Location

    Raises:
        ValueError: If location not found
    """
    location = session.get(Location, id)

    if not location:
        raise ValueError(f"Location with id {id} not found")

    return location


def update_location(
    session: Session,
    id: int,
    name: str | None = None,
    location_type: LocationType | None = None,
    description: str | None = None,
    is_active: bool | None = None,
    color: str | None = None,
) -> Location:
    """Update location.

    Args:
        session: Database session
        id: Location ID
        name: New name (case-insensitive unique)
        location_type: New location type
        description: New description
        is_active: New active status
        color: New hex color code (e.g., "#FF5733")

    Returns:
        Updated location

    Raises:
        ValueError: If location not found or duplicate name
    """
    location = get_location(session, id)

    if name is not None:
        name = require_non_empty(name, "Lagerortname")
    if color is not None:
        color = validate_hex_color(color)

    # Check for duplicate name if changing name
    if name and name.lower() != location.name.lower():
        existing = session.exec(
            select(Location).where(Location.name.ilike(name))  # type: ignore
        ).first()

        if existing:
            raise DuplicateNameError("name", existing.name, "Lagerort")

        location.name = name

    if location_type is not None:
        location.location_type = location_type

    if description is not None:
        location.description = description

    if is_active is not None:
        location.is_active = is_active

    if color is not None:
        location.color = color

    session.add(location)
    session.commit()
    session.refresh(location)

    return location


def delete_location(session: Session, id: int) -> None:
    """Löscht einen Lagerort, der von keinem Artikel referenziert wird.

    Entnommene Artikel zählen mit, weil sie den Lagerort weiterhin referenzieren;
    der dokumentierte Weg für belegte Lagerorte ist das Deaktivieren (Issue #379).

    Raises:
        ValueError: Lagerort nicht gefunden oder noch in Verwendung.
    """
    location = get_location(session, id)

    item_count = session.exec(select(func.count()).select_from(Item).where(Item.location_id == id)).one()
    if item_count:
        raise ValueError(
            f"Lagerort '{location.name}' ist in Verwendung ({item_count} Artikel, inklusive entnommener). "
            "Lagerort stattdessen deaktivieren."
        )

    session.delete(location)
    session.commit()
