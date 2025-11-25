"""Tests for location_service."""

from app.models import LocationType
from app.models import User
from app.services import location_service
import pytest
from sqlmodel import Session


def test_create_location(session: Session, test_admin: User) -> None:
    """Test creating a location."""
    location = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )

    assert location.id is not None
    assert location.name == "Gefrierschrank"
    assert location.location_type == LocationType.FROZEN
    assert location.description is None
    assert location.is_active is True
    assert location.created_by == test_admin.id


def test_create_location_with_description(session: Session, test_admin: User) -> None:
    """Test creating a location with description."""
    location = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
        description="Hauptkühlschrank in der Küche",
    )

    assert location.id is not None
    assert location.name == "Kühlschrank"
    assert location.location_type == LocationType.CHILLED
    assert location.description == "Hauptkühlschrank in der Küche"
    assert location.is_active is True


def test_create_location_duplicate_name_fails(session: Session, test_admin: User) -> None:
    """Test that duplicate location names fail."""
    location_service.create_location(
        session=session,
        name="Vorratsraum",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    with pytest.raises(ValueError, match="Location with name 'Vorratsraum' already exists"):
        location_service.create_location(
            session=session,
            name="vorratsraum",  # Case-insensitive check
            location_type=LocationType.AMBIENT,
            created_by=test_admin.id,
        )


def test_get_all_locations(session: Session, test_admin: User) -> None:
    """Test getting all locations."""
    location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )

    locations = location_service.get_all_locations(session)

    assert len(locations) == 2
    assert locations[0].name == "Gefrierschrank"
    assert locations[1].name == "Kühlschrank"


def test_get_location(session: Session, test_admin: User) -> None:
    """Test getting a location by ID."""
    created = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    location = location_service.get_location(session, created.id)

    assert location.id == created.id
    assert location.name == "Keller"


def test_get_location_not_found_fails(session: Session) -> None:
    """Test that getting non-existent location fails."""
    with pytest.raises(ValueError, match="Location with id 999 not found"):
        location_service.get_location(session, 999)


def test_update_location_name(session: Session, test_admin: User) -> None:
    """Test updating a location's name."""
    created = location_service.create_location(
        session=session,
        name="Alter Name",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )

    updated = location_service.update_location(
        session=session,
        id=created.id,
        name="Neuer Name",
    )

    assert updated.name == "Neuer Name"
    assert updated.location_type == LocationType.FROZEN  # Unchanged


def test_update_location_duplicate_name_fails(session: Session, test_admin: User) -> None:
    """Test that updating to duplicate name fails."""
    location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    second = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )

    with pytest.raises(ValueError, match="Location with name 'Gefrierschrank' already exists"):
        location_service.update_location(
            session=session,
            id=second.id,
            name="gefrierschrank",  # Case-insensitive check
        )


def test_update_location_to_inactive(session: Session, test_admin: User) -> None:
    """Test updating a location to inactive."""
    created = location_service.create_location(
        session=session,
        name="Zu deaktivieren",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    updated = location_service.update_location(
        session=session,
        id=created.id,
        is_active=False,
    )

    assert updated.is_active is False


def test_update_location_description(session: Session, test_admin: User) -> None:
    """Test updating a location's description."""
    created = location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )

    updated = location_service.update_location(
        session=session,
        id=created.id,
        description="Neue Beschreibung",
    )

    assert updated.description == "Neue Beschreibung"


def test_delete_location(session: Session, test_admin: User) -> None:
    """Test deleting a location."""
    created = location_service.create_location(
        session=session,
        name="Zu löschen",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )

    location_service.delete_location(session, created.id)

    with pytest.raises(ValueError, match="Location with id .* not found"):
        location_service.get_location(session, created.id)
