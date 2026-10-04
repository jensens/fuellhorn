"""UI: Smart-Default-Zeitfenster aus den Preferences; letzter Eintrag pro Nutzer in der DB (Issue #397).

Vorher hardcodierte der Wizard 30/30/60 Minuten (die Einstellungen in Profil und
Admin waren wirkungslos) und legte den letzten Eintrag in ``app.storage.user`` ab,
obwohl ``preferences_service.save_last_item_entry`` existierte.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Location
from app.models import LocationType
from app.models import StorageType
from app.models import User
from app.services import preferences_service
from datetime import datetime
from datetime import timedelta
from nicegui import ui
from nicegui.testing import User as NiceGUIUser
import pytest
from sqlmodel import Session


ADMIN_ID = 1
WINDOW_KEYS = ("item_type_time_window", "category_time_window", "location_time_window")


def _reset_admin_preferences(engine) -> None:
    with Session(engine) as session:
        admin = session.get(User, ADMIN_ID)
        assert admin is not None
        admin.preferences = {}
        session.add(admin)
        session.commit()


@pytest.fixture(autouse=True)
def _clean_admin_preferences(isolated_test_database):
    """Die Bereinigung löscht alle Zeilen außer dem Admin; seine Preferences würden sonst zwischen Tests leaken."""
    _reset_admin_preferences(isolated_test_database)
    yield
    _reset_admin_preferences(isolated_test_database)


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    """Tiefkühltruhe und eine TK-Kategorie mit Haltbarkeit."""
    with Session(isolated_test_database) as session:
        freezer = Location(name="Tiefkühltruhe", location_type=LocationType.FROZEN, created_by=ADMIN_ID)
        frozen_cat = Category(name="Fertiggerichte", created_by=ADMIN_ID)
        session.add_all([freezer, frozen_cat])
        session.commit()
        session.refresh(freezer)
        session.refresh(frozen_cat)
        assert freezer.id is not None and frozen_cat.id is not None
        session.add(
            CategoryShelfLife(category_id=frozen_cat.id, storage_type=StorageType.FROZEN, months_min=3, months_max=6)
        )
        session.commit()
        return {"freezer": freezer.id, "frozen_cat": frozen_cat.id}


def _set_user_windows(engine, minutes: int) -> None:
    with Session(engine) as session:
        admin = session.get(User, ADMIN_ID)
        assert admin is not None
        for key in WINDOW_KEYS:
            preferences_service.set_user_preference(session, admin, key, minutes)


def _age_last_entry(engine, minutes: int) -> None:
    """Datiert den gespeicherten letzten Eintrag zurück, als wären ``minutes`` vergangen."""
    with Session(engine) as session:
        admin = session.get(User, ADMIN_ID)
        assert admin is not None
        entry = preferences_service.get_last_item_entry(session, admin)
        assert entry is not None, "Der Wizard muss den letzten Eintrag in den Nutzer-Preferences ablegen"
        aged = dict(entry)
        aged["timestamp"] = (datetime.fromisoformat(entry["timestamp"]) - timedelta(minutes=minutes)).isoformat()
        preferences_service.save_last_item_entry(session, admin, aged)


def _is_active(user: NiceGUIUser, marker: str) -> bool:
    element = user.find(marker=marker).elements.pop()
    return "active" in element._classes


async def _capture_frozen_item(user: NiceGUIUser, world: dict[str, int]) -> None:
    """TK-Pizza über 'Speichern & Nächster' erfassen; der Wizard lädt danach Schritt 1 mit Defaults."""
    await user.open("/items/add")
    await user.should_see("Schritt 1 von 3")
    user.find("z.B. Tomaten aus Garten").type("Pizza")
    user.find(marker="item-type-chip-purchased_frozen").click()
    user.find(kind=ui.number).elements.pop().set_value(1)
    user.find(marker="unit-chip-Stück").click()
    user.find("Weiter").click()
    await user.should_see("Schritt 2 von 3")
    user.find(marker=f"category-chip-{world['frozen_cat']}").click()
    user.find("Weiter").click()
    await user.should_see("Schritt 3 von 3")
    user.find(marker=f"location-chip-{world['freezer']}").click()
    user.find(marker="wizard-save-next").click()
    await user.should_see("gespeichert")
    await user.should_see("Schritt 1 von 3")


async def test_last_entry_is_stored_per_user_in_preferences(
    logged_in_user: NiceGUIUser, isolated_test_database, world: dict[str, int]
) -> None:
    """Ein Speicher: der letzte Eintrag liegt in ``user.preferences``, ohne das nie gelesene Datum."""
    await _capture_frozen_item(logged_in_user, world)

    with Session(isolated_test_database) as session:
        admin = session.get(User, ADMIN_ID)
        assert admin is not None
        entry = preferences_service.get_last_item_entry(session, admin)

    assert entry is not None
    assert entry["item_type"] == "purchased_frozen" and entry["unit"] == "Stück"
    assert entry["location_id"] == world["freezer"] and entry["category_id"] == world["frozen_cat"]
    assert "best_before_date" not in entry


async def test_defaults_apply_within_user_window(
    logged_in_user: NiceGUIUser, isolated_test_database, world: dict[str, int]
) -> None:
    _set_user_windows(isolated_test_database, 1)
    await _capture_frozen_item(logged_in_user, world)

    assert _is_active(logged_in_user, "item-type-chip-purchased_frozen")
    assert _is_active(logged_in_user, "unit-chip-Stück")
    logged_in_user.find("z.B. Tomaten aus Garten").type("Lasagne")
    logged_in_user.find(kind=ui.number).elements.pop().set_value(2)
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 2 von 3")
    assert _is_active(logged_in_user, f"category-chip-{world['frozen_cat']}")
    logged_in_user.find("Weiter").click()
    await logged_in_user.should_see("Schritt 3 von 3")
    assert _is_active(logged_in_user, f"location-chip-{world['freezer']}")


async def test_defaults_expire_after_user_window(
    logged_in_user: NiceGUIUser, isolated_test_database, world: dict[str, int]
) -> None:
    """Akzeptanzkriterium: Zeitfenster 1 min, Eintrag 2 min alt → kein Default; die Einheit kennt kein Zeitfenster."""
    _set_user_windows(isolated_test_database, 1)
    await _capture_frozen_item(logged_in_user, world)
    _age_last_entry(isolated_test_database, 2)

    await logged_in_user.open("/items/add")
    await logged_in_user.should_see("Schritt 1 von 3")

    assert not _is_active(logged_in_user, "item-type-chip-purchased_frozen")
    assert _is_active(logged_in_user, "unit-chip-Stück")
