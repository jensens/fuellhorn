"""Echte Seitenflüsse mit der eingeloggten User-Fixture (Issue #389).

Die 680 grünen Tests vor der Sanierung liefen fast nur über Harness-Routen mit
eigenen Callbacks und fanden die Kernfehler aus Stufe 1 nicht. Jeder Test hier
nennt in seinem Docstring den Fehler, den er damals rot gemacht hätte.
"""

from app.models import Category
from app.models import CategoryShelfLife
from app.models import Item
from app.models import ItemType
from app.models import Location
from app.models import LocationType
from app.models import Role
from app.models import StorageType
from app.models import Withdrawal
from app.services import item_service
from app.services.auth_service import get_user_by_username
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from nicegui import ui
from nicegui.testing import User
import pytest
from sqlmodel import Session
from sqlmodel import select


@pytest.fixture(name="world")
def world_fixture(isolated_test_database) -> dict[str, int]:
    """Kühlschrank + Truhe, Kategorie 'Suppen' (FROZEN 2–3 Monate) und 'Milchprodukte' (ohne Haltbarkeit)."""
    with Session(isolated_test_database) as session:
        fridge = Location(name="Kühlschrank", location_type=LocationType.CHILLED, created_by=1)
        freezer = Location(name="Truhe", location_type=LocationType.FROZEN, created_by=1)
        soups = Category(name="Suppen", created_by=1)
        dairy = Category(name="Milchprodukte", created_by=1)
        session.add_all([fridge, freezer, soups, dairy])
        session.commit()
        for obj in (fridge, freezer, soups, dairy):
            session.refresh(obj)
        assert soups.id is not None
        session.add(
            CategoryShelfLife(category_id=soups.id, storage_type=StorageType.FROZEN, months_min=2, months_max=3)
        )
        session.commit()
        return {"fridge": fridge.id, "freezer": freezer.id, "soups": soups.id, "dairy": dairy.id}  # type: ignore[dict-item]


def _mhd_item(session: Session, world: dict[str, int], name: str, days: int, notes: str | None = None) -> int:
    item = item_service.create_item(
        session,
        product_name=name,
        best_before_date=date.today() + timedelta(days=days),
        quantity=2,
        unit="Stück",
        item_type=ItemType.PURCHASED_FRESH,
        location_id=world["fridge"],
        created_by=1,
        category_id=world["dairy"],
        notes=notes,
    )
    assert item.id is not None
    return item.id


def _frozen_soup(session: Session, world: dict[str, int], name: str, frozen_days_ago: int) -> int:
    freeze = date.today() - timedelta(days=frozen_days_ago)
    item = item_service.create_item(
        session,
        product_name=name,
        best_before_date=freeze,
        quantity=1,
        unit="l",
        item_type=ItemType.HOMEMADE_FROZEN,
        location_id=world["freezer"],
        created_by=1,
        category_id=world["soups"],
        freeze_date=freeze,
    )
    assert item.id is not None
    return item.id


def _card_names(user: User) -> list[str]:
    """Produktnamen der gerenderten Artikel-Karten in Anzeigereihenfolge (Marker ``item-name-<id>``)."""
    # ``find(...).elements`` ist eine Menge ohne Reihenfolge; der Elementbaum liefert die Renderreihenfolge
    assert user.client is not None
    return [
        element.text
        for element in user.client.layout.descendants()
        if isinstance(element, ui.label) and any(m.startswith("item-name-") for m in element._markers)
    ]


def _set_number(user: User, value: float) -> None:
    number_input = user.find(kind=ui.number).elements.pop()
    number_input.set_value(value)


def _type_date(user: User, marker: str, value: date) -> None:
    field = user.find(marker=marker)
    field.clear()
    field.type(value.strftime("%d.%m.%Y"))


# --- Wizard ----------------------------------------------------------------------------------


async def test_wizard_persists_every_field(logged_in_user: User, isolated_test_database, world: dict[str, int]) -> None:
    """Hätte gefangen: #362 (jeder Artikel bekam date.today()), #385 (Lagerort/Kategorie nicht geprüft)."""
    mhd = date.today() + timedelta(days=12)
    await logged_in_user.open("/items/add")
    logged_in_user.find("z.B. Tomaten aus Garten").type("Bergkäse")
    logged_in_user.find(marker="item-type-chip-purchased_fresh").click()
    _set_number(logged_in_user, 250)
    logged_in_user.find(marker="unit-chip-g").click()
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 2 von 3")
    logged_in_user.find(marker=f"category-chip-{world['dairy']}").click()
    _type_date(logged_in_user, "wizard-date-input", mhd)
    logged_in_user.find("z.B. je 12 Stück, 300g pro Packung").type("vom Markt")
    logged_in_user.find("Weiter").click()

    await logged_in_user.should_see("Schritt 3 von 3")
    await logged_in_user.should_see(f"MHD: {mhd.strftime('%d.%m.%Y')}")
    logged_in_user.find(marker=f"location-chip-{world['fridge']}").click()
    logged_in_user.find(marker="wizard-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = session.exec(select(Item)).one()
    assert (item.product_name, item.quantity, item.unit) == ("Bergkäse", 250, "g")
    assert (item.item_type, item.category_id, item.location_id) == (
        ItemType.PURCHASED_FRESH,
        world["dairy"],
        world["fridge"],
    )
    assert (item.best_before_date, item.freeze_date, item.notes) == (mhd, None, "vom Markt")
    assert item.created_by == 1


# --- Edit ------------------------------------------------------------------------------------


async def test_edit_changes_date_and_notes_in_db(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Hätte gefangen: #362 (Edit-Datum erreichte form_data nicht), #386 (Notiz nie geändert/geleert)."""
    with Session(isolated_test_database) as session:
        item_id = _mhd_item(session, world, "Joghurt", days=3, notes="alt")
    new_date = date.today() + timedelta(days=20)

    await logged_in_user.open(f"/items/{item_id}/edit")
    _type_date(logged_in_user, "edit-date-input", new_date)
    notes = logged_in_user.find("z.B. je 12 Stück, 300g pro Packung")
    notes.clear()
    notes.type("neu")
    logged_in_user.find(marker="edit-save").click()
    await logged_in_user.should_see("gespeichert")

    with Session(isolated_test_database) as session:
        item = item_service.get_item(session, item_id)
    assert (item.best_before_date, item.notes) == (new_date, "neu")


# --- /items ------------------------------------------------------------------------------------


async def test_items_expiring_filter_uses_status_not_best_before_date(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Hätte gefangen: #363 (Expiring-Soon verglich best_before_date; frische Suppe galt als abgelaufen)."""
    with Session(isolated_test_database) as session:
        _frozen_soup(session, world, "Kürbissuppe", frozen_days_ago=0)  # ok, Idealdatum in 2 Monaten
        _mhd_item(session, world, "Joghurt", days=2)  # critical
        _mhd_item(session, world, "Butter", days=30)  # ok

    await logged_in_user.open("/items?filter=expiring")
    await logged_in_user.should_see("Joghurt")
    assert _card_names(logged_in_user) == ["Joghurt"]


async def test_items_search_filters_cards(logged_in_user: User, isolated_test_database, world: dict[str, int]) -> None:
    """Echte Suche auf /items (vorher nur die reine Funktion _filter_items getestet)."""
    with Session(isolated_test_database) as session:
        _mhd_item(session, world, "Joghurt", days=5)
        _mhd_item(session, world, "Butter", days=5)

    await logged_in_user.open("/items")
    assert sorted(_card_names(logged_in_user)) == ["Butter", "Joghurt"]

    logged_in_user.find("Produktname...").type("jog")
    await logged_in_user.should_see("Joghurt")
    assert _card_names(logged_in_user) == ["Joghurt"]

    logged_in_user.find("Produktname...").clear()
    logged_in_user.find("Produktname...").type("xyz")
    await logged_in_user.should_see("Keine Artikel gefunden")


async def test_items_location_filter_and_sort_direction(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Lagerort-Filter und Sortierrichtung auf der echten Seite."""
    with Session(isolated_test_database) as session:
        _mhd_item(session, world, "Joghurt", days=2)
        _mhd_item(session, world, "Butter", days=10)
        _frozen_soup(session, world, "Kürbissuppe", frozen_days_ago=0)

    await logged_in_user.open("/items")
    # Standard: nach wirksamem Ablaufdatum aufsteigend (Suppe: Idealdatum in 2 Monaten)
    assert _card_names(logged_in_user) == ["Joghurt", "Butter", "Kürbissuppe"]

    logged_in_user.find(marker="sort-direction").click()
    await logged_in_user.should_see("Kürbissuppe")
    assert _card_names(logged_in_user) == ["Kürbissuppe", "Butter", "Joghurt"]

    (location_select,) = [
        s for s in logged_in_user.find(kind=ui.select).elements if s._props.get("label") == "Lagerort"
    ]
    location_select.set_value(world["freezer"])
    await logged_in_user.should_see("Kürbissuppe")
    assert _card_names(logged_in_user) == ["Kürbissuppe"]


async def test_items_partial_withdrawal_from_real_card_records_user(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Hätte gefangen: #367 (Entnahme ohne withdrawn_by; Artikel verschwand aus beiden Listen)."""
    with Session(isolated_test_database) as session:
        item_id = _mhd_item(session, world, "Joghurt", days=5)
        admin = get_user_by_username(session, "admin")
        assert admin is not None

    await logged_in_user.open("/items")
    logged_in_user.find(marker=f"item-consume-{item_id}").click()
    await logged_in_user.should_see("Teilentnahme")
    logged_in_user.find("Teilentnahme").click()
    await logged_in_user.should_see("Menge entnehmen")
    _set_number(logged_in_user, 0.5)
    logged_in_user.find("Bestätigen").click()
    await logged_in_user.should_see("entnommen")

    with Session(isolated_test_database) as session:
        item = item_service.get_item(session, item_id)
        (withdrawal,) = session.exec(select(Withdrawal)).all()
    assert item.quantity == 1.5
    assert (withdrawal.quantity, withdrawal.withdrawn_by) == (0.5, admin.id)


# --- Dashboard ---------------------------------------------------------------------------------


async def test_dashboard_expiring_count_with_mixed_types(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Hätte gefangen: #363 (Zähler 'Bald ablaufend' zählte frisch eingefrorene Suppe mit)."""
    with Session(isolated_test_database) as session:
        _frozen_soup(session, world, "Kürbissuppe", frozen_days_ago=0)
        _frozen_soup(session, world, "Alte Suppe", frozen_days_ago=75)  # Idealdatum (2 Monate) überschritten
        _mhd_item(session, world, "Joghurt", days=2)
        _mhd_item(session, world, "Butter", days=30)

    await logged_in_user.open("/dashboard")
    await logged_in_user.should_see("Bald ablaufend (2)")
    await logged_in_user.should_see("Joghurt")
    await logged_in_user.should_see("Alte Suppe")
    await logged_in_user.should_see((date.today() - timedelta(days=75) + relativedelta(months=2)).strftime("%d.%m."))


# --- Berechtigungen ------------------------------------------------------------------------------


async def test_non_admin_is_redirected_from_admin_page_with_message(
    logged_in_user: User, isolated_test_database
) -> None:
    """Hätte gefangen: fehlende Rückmeldung bei verweigertem Zugriff (Redirect ohne Hinweis)."""

    def _set_role(role: Role) -> None:
        with Session(isolated_test_database) as session:
            admin = get_user_by_username(session, "admin")
            assert admin is not None
            admin.role = role.value
            session.add(admin)
            session.commit()

    _set_role(Role.USER)
    try:
        await logged_in_user.open("/admin/users")
        await logged_in_user.should_see("Auf einen Blick")  # Dashboard = Redirect-Ziel
        await logged_in_user.should_see("Keine Berechtigung")
        await logged_in_user.should_not_see("Neuen Benutzer")
    finally:
        _set_role(Role.ADMIN)


async def test_items_type_filter_category_chip_and_reset(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """Artikel-Typ-Filter, Kategorie-Chip und 'Filter zurücksetzen' auf der echten Seite."""
    with Session(isolated_test_database) as session:
        _mhd_item(session, world, "Joghurt", days=5)
        _frozen_soup(session, world, "Kürbissuppe", frozen_days_ago=0)

    await logged_in_user.open("/items")
    assert sorted(_card_names(logged_in_user)) == ["Joghurt", "Kürbissuppe"]

    (type_select,) = [s for s in logged_in_user.find(kind=ui.select).elements if s._props.get("label") == "Artikel-Typ"]
    type_select.set_value(ItemType.HOMEMADE_FROZEN.value)
    await logged_in_user.should_see("Kürbissuppe")
    assert _card_names(logged_in_user) == ["Kürbissuppe"]

    logged_in_user.find("Filter zurücksetzen").click()
    await logged_in_user.should_see("Joghurt")
    assert sorted(_card_names(logged_in_user)) == ["Joghurt", "Kürbissuppe"]

    logged_in_user.find("● Milchprodukte").click()
    await logged_in_user.should_see("Joghurt")
    assert _card_names(logged_in_user) == ["Joghurt"]
    logged_in_user.find("● Milchprodukte").click()
    assert sorted(_card_names(logged_in_user)) == ["Joghurt", "Kürbissuppe"]


async def test_items_consumed_toggle_shows_withdrawn_items(
    logged_in_user: User, isolated_test_database, world: dict[str, int]
) -> None:
    """'Entnommene anzeigen' listet verbrauchte Artikel; ohne Entnahmen erscheint der Hinweis."""
    with Session(isolated_test_database) as session:
        _mhd_item(session, world, "Joghurt", days=5)
        consumed_id = _mhd_item(session, world, "Alte Butter", days=5)
        item_service.mark_item_consumed(session, consumed_id, user_id=1)

    await logged_in_user.open("/items")
    assert _card_names(logged_in_user) == ["Joghurt"]

    (toggle,) = logged_in_user.find(kind=ui.switch).elements
    toggle.set_value(True)
    await logged_in_user.should_see("Alte Butter")
    assert _card_names(logged_in_user) == ["Alte Butter"]

    toggle.set_value(False)
    await logged_in_user.should_see("Joghurt")
    assert _card_names(logged_in_user) == ["Joghurt"]
