"""Location service - Business logic for location management."""

from ..models.location import Location
from ..models.location import LocationType
from sqlmodel import Session
from sqlmodel import select


def create_location(
    session: Session,
    name: str,
    location_type: LocationType,
    created_by: int,
    description: str | None = None,
) -> Location:
    """Create a new location.

    Args:
        session: Database session
        name: Location name (case-insensitive unique)
        location_type: Type of storage location (frozen/chilled/ambient)
        created_by: User ID who created the location
        description: Optional description of the location

    Returns:
        Created location

    Raises:
        ValueError: If location with same name already exists
    """
    # Check for duplicate name (case-insensitive)
    existing = session.exec(
        select(Location).where(Location.name.ilike(name))  # type: ignore
    ).first()

    if existing:
        raise ValueError(f"Location with name '{existing.name}' already exists")

    location = Location(
        name=name,
        location_type=location_type,
        created_by=created_by,
        description=description,
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
) -> Location:
    """Update location.

    Args:
        session: Database session
        id: Location ID
        name: New name (case-insensitive unique)
        location_type: New location type
        description: New description
        is_active: New active status

    Returns:
        Updated location

    Raises:
        ValueError: If location not found or duplicate name
    """
    location = get_location(session, id)

    # Check for duplicate name if changing name
    if name and name.lower() != location.name.lower():
        existing = session.exec(
            select(Location).where(Location.name.ilike(name))  # type: ignore
        ).first()

        if existing:
            raise ValueError(f"Location with name '{existing.name}' already exists")

        location.name = name

    if location_type is not None:
        location.location_type = location_type

    if description is not None:
        location.description = description

    if is_active is not None:
        location.is_active = is_active

    session.add(location)
    session.commit()
    session.refresh(location)

    return location


def delete_location(session: Session, id: int) -> None:
    """Delete location.

    Args:
        session: Database session
        id: Location ID

    Raises:
        ValueError: If location not found
    """
    location = get_location(session, id)

    session.delete(location)
    session.commit()
