"""UI-Test: Edit-View verwirft beim Typwechsel inkompatible Lagerort-/Kategorie-IDs (Issue #385)."""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import item_service
from datetime import date
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="frozen_pizza")
def frozen_pizza_fixture(isolated_test_database) -> dict:
    """TK-Pizza in der Tiefkühltruhe; außerdem ein Kühlschrank für den Typwechsel."""
    with Session(isolated_test_database) as session:
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=1)
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        frozen_cat = Category(name="Fertiggerichte", created_by=1)
        session.add_all([freezer, fridge, frozen_cat])
        session.commit()
        for obj in (freezer, fridge, frozen_cat):
            session.refresh(obj)
        assert freezer.id is not None and frozen_cat.id is not None
        session.add(
            CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=3, months_max=6)
        )
        session.commit()
        item = item_service.create_item(
            session=session,
            product_name="Pizza",
            best_before_date=date(2027, 3, 1),
            quantity=2,
            unit="Stück",
            item_type=ItemType.PURCHASED_FROZEN,
            location_id=freezer.id,
            created_by=1,
            category_id=frozen_cat.id,
        )
        assert item.id is not None
        return {"item_id": item.id, "freezer": freezer.id, "fridge": fridge.id, "frozen_cat": frozen_cat.id}


def _is_disabled(user: User, marker: str) -> bool:
    element = user.find(marker=marker).elements.pop()
    return bool(element._props.get("disabled") or element._props.get("disable")) or not getattr(
        element, "enabled", True
    )


async def test_type_change_drops_incompatible_location_and_disables_save(
    logged_in_user: User, frozen_pizza: dict
) -> None:
    await logged_in_user.open(f"/items/{frozen_pizza['item_id']}/edit")
    await logged_in_user.should_see("Artikel bearbeiten")
    assert not _is_disabled(logged_in_user, "edit-save")

    logged_in_user.find(marker="item-type-chip-purchased_fresh").click()

    await logged_in_user.should_not_see(marker=f"location-chip-{frozen_pizza['freezer']}")
    assert _is_disabled(logged_in_user, "edit-save"), "Speichern muss ohne gültigen Lagerort deaktiviert sein"

    # Für 'frisch eingekauft' sind alle Kategorien wählbar, die bisherige bleibt also gültig
    logged_in_user.find(marker=f"location-chip-{frozen_pizza['fridge']}").click()
    assert not _is_disabled(logged_in_user, "edit-save")
