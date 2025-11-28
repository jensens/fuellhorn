"""Tests for location_service."""

from app.models import ItemType
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


# Tests for get_valid_location_types()


def test_get_valid_location_types_purchased_fresh() -> None:
    """Test that purchased_fresh items can only be stored in chilled/ambient."""
    valid_types = location_service.get_valid_location_types(ItemType.PURCHASED_FRESH)

    assert LocationType.CHILLED in valid_types
    assert LocationType.AMBIENT in valid_types
    assert LocationType.FROZEN not in valid_types


def test_get_valid_location_types_purchased_frozen() -> None:
    """Test that purchased_frozen items can only be stored in frozen."""
    valid_types = location_service.get_valid_location_types(ItemType.PURCHASED_FROZEN)

    assert LocationType.FROZEN in valid_types
    assert LocationType.CHILLED not in valid_types
    assert LocationType.AMBIENT not in valid_types


def test_get_valid_location_types_purchased_then_frozen() -> None:
    """Test that purchased_then_frozen items can only be stored in frozen."""
    valid_types = location_service.get_valid_location_types(ItemType.PURCHASED_THEN_FROZEN)

    assert LocationType.FROZEN in valid_types
    assert LocationType.CHILLED not in valid_types
    assert LocationType.AMBIENT not in valid_types


def test_get_valid_location_types_homemade_frozen() -> None:
    """Test that homemade_frozen items can only be stored in frozen."""
    valid_types = location_service.get_valid_location_types(ItemType.HOMEMADE_FROZEN)

    assert LocationType.FROZEN in valid_types
    assert LocationType.CHILLED not in valid_types
    assert LocationType.AMBIENT not in valid_types


def test_get_valid_location_types_homemade_preserved() -> None:
    """Test that homemade_preserved items can only be stored in ambient/chilled."""
    valid_types = location_service.get_valid_location_types(ItemType.HOMEMADE_PRESERVED)

    assert LocationType.AMBIENT in valid_types
    assert LocationType.CHILLED in valid_types
    assert LocationType.FROZEN not in valid_types


# Tests for get_locations_for_item_type()


def test_get_locations_for_item_type_frozen_items(session: Session, test_admin: User) -> None:
    """Test filtering locations for frozen item types."""
    # Create locations of different types
    frozen_loc = location_service.create_location(
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
    location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    # Frozen items should only see frozen locations
    locations = location_service.get_locations_for_item_type(session, ItemType.PURCHASED_FROZEN)

    assert len(locations) == 1
    assert locations[0].id == frozen_loc.id
    assert locations[0].location_type == LocationType.FROZEN


def test_get_locations_for_item_type_fresh_items(session: Session, test_admin: User) -> None:
    """Test filtering locations for fresh item types."""
    # Create locations of different types
    location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    chilled_loc = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    ambient_loc = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    # Fresh items should only see chilled and ambient locations
    locations = location_service.get_locations_for_item_type(session, ItemType.PURCHASED_FRESH)

    assert len(locations) == 2
    location_ids = [loc.id for loc in locations]
    assert chilled_loc.id in location_ids
    assert ambient_loc.id in location_ids


def test_get_locations_for_item_type_preserved_items(session: Session, test_admin: User) -> None:
    """Test filtering locations for preserved item types."""
    # Create locations of different types
    location_service.create_location(
        session=session,
        name="Gefrierschrank",
        location_type=LocationType.FROZEN,
        created_by=test_admin.id,
    )
    chilled_loc = location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )
    ambient_loc = location_service.create_location(
        session=session,
        name="Keller",
        location_type=LocationType.AMBIENT,
        created_by=test_admin.id,
    )

    # Preserved items should only see chilled and ambient locations
    locations = location_service.get_locations_for_item_type(session, ItemType.HOMEMADE_PRESERVED)

    assert len(locations) == 2
    location_ids = [loc.id for loc in locations]
    assert chilled_loc.id in location_ids
    assert ambient_loc.id in location_ids


def test_get_locations_for_item_type_empty_result(session: Session, test_admin: User) -> None:
    """Test that empty list is returned when no matching locations exist."""
    # Create only chilled location
    location_service.create_location(
        session=session,
        name="Kühlschrank",
        location_type=LocationType.CHILLED,
        created_by=test_admin.id,
    )

    # Frozen items should get empty list (no frozen locations)
    locations = location_service.get_locations_for_item_type(session, ItemType.PURCHASED_FROZEN)

    assert len(locations) == 0
