"""Touch-Targets auf /items und im Dashboard sind mindestens 44 px hoch (Issue #399)."""

from app.models import Category
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        veg = Category(name="Gemüse", created_by=1)
        session.add_all([fridge, veg])
        session.commit()
        session.refresh(fridge)
        session.refresh(veg)
        assert fridge.id is not None and veg.id is not None
        item = item_service.create_item(
            session,
            product_name="Karotten",
            best_before_date=date(2027, 1, 1),
            quantity=1,
            unit="kg",
            item_type=ItemType.PURCHASED_FRESH,
            location_id=fridge.id,
            created_by=1,
            category_id=veg.id,
        )
        assert item.id is not None
        return {"fridge": fridge.id, "veg": veg.id, "item": item.id}


async def test_category_filter_chips_are_44px_tall(logged_in_user: User, world: dict[str, int]) -> None:
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Karotten")

    chip = logged_in_user.find(marker=f"filter-category-{world['veg']}").elements.pop()

    assert "min-h-[44px]" in chip._classes
    assert "py-1" not in chip._classes


async def test_sort_direction_button_is_not_dense(logged_in_user: User, world: dict[str, int]) -> None:
    await logged_in_user.open("/items")
    await logged_in_user.should_see("Karotten")

    (button,) = logged_in_user.find(kind=ui.button, marker="sort-direction").elements

    assert "dense" not in button._props
    assert button._style.get("min-height") == "44px"
    assert button._style.get("min-width") == "44px"


async def test_recently_added_rows_are_44px_tall(logged_in_user: User, world: dict[str, int]) -> None:
    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Karotten")

    rows = [
        element
        for element in logged_in_user.client.layout.descendants()  # type: ignore[union-attr]
        if "min-h-[44px]" in getattr(element, "_classes", []) and "cursor-pointer" in element._classes
    ]

    assert rows, "Die Zeile des zuletzt erfassten Artikels muss ein 44-px-Touch-Target sein"
