"""UI: Kategorie-Hierarchie im Admin verwalten und im Vorratsfilter nutzen (Issue #395)."""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.services import category_service
from app.services import item_service
from datetime import date
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session


@pytest.fixture(name="meat_world")
def meat_world_fixture(isolated_test_database) -> dict[str, int]:
    """Gruppe 'Fleisch' mit Kind 'Rindfleisch', eigenständige 'Wurst' und 'Gemüse'; Truhe mit je einem Artikel."""
    with Session(isolated_test_database) as session:
        meat = Category(name="Fleisch", created_by=1)
        session.add(meat)
        session.commit()
        session.refresh(meat)
        beef = Category(name="Rindfleisch", created_by=1, parent_id=meat.id)
        sausage = Category(name="Wurst", created_by=1)
        veg = Category(name="Gemüse", created_by=1)
        freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=1)
        session.add_all([beef, sausage, veg, freezer])
        session.commit()
        for obj in (beef, sausage, veg, freezer):
            session.refresh(obj)
        assert meat.id and beef.id and sausage.id and veg.id and freezer.id
        for category_id in (meat.id, beef.id, sausage.id, veg.id):
            session.add(
                CategoryShelfLife(category_id=category_id, storage_type=StorageType.FROZEN, months_min=2, months_max=6)
            )
        session.commit()
        for name, category_id in (("Steak", beef.id), ("Bratwurst", sausage.id), ("Erbsen", veg.id)):
            item_service.create_item(
                session,
                product_name=name,
                best_before_date=date(2027, 3, 1),
                quantity=1,
                unit="Stück",
                item_type=ItemType.PURCHASED_FROZEN,
                location_id=freezer.id,
                created_by=1,
                category_id=category_id,
            )
        return {"meat": meat.id, "beef": beef.id, "sausage": sausage.id, "veg": veg.id}


def _card_names(user: User) -> list[str]:
    assert user.client is not None
    return [
        element.text
        for element in user.client.layout.descendants()
        if isinstance(element, ui.label) and any(m.startswith("item-name-") for m in element._markers)
    ]


async def test_admin_assigns_child_to_parent(logged_in_user: User, isolated_test_database, meat_world: dict) -> None:
    """Akzeptanzkriterium: Kind einem Parent zuordnen → in der DB und in der Liste eingerückt unter der Gruppe."""
    await logged_in_user.open("/admin/categories")
    await logged_in_user.should_see("Gruppe")  # Badge an 'Fleisch'

    logged_in_user.find(marker="edit-Wurst").click()
    (parent_select,) = logged_in_user.find(kind=ui.select, marker="edit-parent").elements
    parent_select.set_value(meat_world["meat"])
    logged_in_user.find("Speichern").click()
    await logged_in_user.should_see("aktualisiert")

    with Session(isolated_test_database) as session:
        assert category_service.get_category(session, meat_world["sausage"]).parent_id == meat_world["meat"]
    await logged_in_user.should_see(marker="child-of-Fleisch-Wurst")


async def test_admin_parent_select_offers_only_top_level_groups(logged_in_user: User, meat_world: dict) -> None:
    """Als Parent wählbar sind nur Kategorien ohne eigenen Parent, nicht die Kategorie selbst."""
    await logged_in_user.open("/admin/categories")
    logged_in_user.find(marker="edit-Gemüse").click()
    (parent_select,) = logged_in_user.find(kind=ui.select, marker="edit-parent").elements

    labels = set(parent_select.options.values())

    assert "Fleisch" in labels and "Wurst" in labels
    assert "Rindfleisch" not in labels and "Gemüse" not in labels


async def test_admin_move_within_group_only_reorders_siblings(
    logged_in_user: User, isolated_test_database, meat_world: dict
) -> None:
    """Hoch/Runter bewegt innerhalb der Geschwister; ein Kind rutscht nicht aus seiner Gruppe heraus."""
    with Session(isolated_test_database) as session:
        pork = Category(name="Schwein", created_by=1, parent_id=meat_world["meat"], sort_order=99)
        session.add(pork)
        session.commit()

    await logged_in_user.open("/admin/categories")
    logged_in_user.find(marker="move-up-Schwein").click()
    await logged_in_user.should_see("Schwein")

    with Session(isolated_test_database) as session:
        ordered = [c.name for c in category_service.get_all_categories(session) if c.parent_id == meat_world["meat"]]
    assert ordered == ["Schwein", "Rindfleisch"]


async def test_items_parent_chip_filters_to_children(logged_in_user: User, meat_world: dict) -> None:
    """Akzeptanzkriterium: Parent-Chip zeigt die Artikel der Kinder."""
    await logged_in_user.open("/items")
    assert sorted(_card_names(logged_in_user)) == ["Bratwurst", "Erbsen", "Steak"]

    logged_in_user.find(marker="category-filter-open").click()  # Auswahl im Panel (#471)
    logged_in_user.find(marker=f"filter-category-{meat_world['meat']}").click()
    await logged_in_user.should_see("Steak")
    assert _card_names(logged_in_user) == ["Steak"]

    logged_in_user.find(marker=f"filter-category-{meat_world['veg']}").click()
    await logged_in_user.should_see("Erbsen")
    assert sorted(_card_names(logged_in_user)) == ["Erbsen", "Steak"]
