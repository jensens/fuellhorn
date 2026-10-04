"""Seed functions for populating the database with default data.

These functions can be called via CLI:
    fuellhorn seed shelf-life-defaults
    fuellhorn seed testdata
"""

from app.models.category import Category
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from app.models.item import Item
from app.models.item import ItemType
from app.models.location import Location
from app.models.location import LocationType
from app.models.user import Role
from app.models.user import User
from app.services.auth_service import create_user
from app.services.auth_service import get_user_by_username
from datetime import date
from datetime import timedelta
from sqlmodel import Session
from sqlmodel import select
from typing import Any


# =============================================================================
# Shelf Life Defaults Data
# =============================================================================

SOURCES = {
    "vsz_be": "https://verbraucherschutzzentrale.be/wie-lange-halten-lebensmittel-im-gefrierfach/",
    "t_online": "https://www.t-online.de/leben/essen-und-trinken/id_19481246/auch-tiefkuehlkost-laeuft-ab-so-lange-sind-diese-lebensmittel-haltbar-.html",
    "usda": "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/freezing-and-food-safety",
    "vz_de": "https://www.verbraucherzentrale.de/wissen/lebensmittel/auswaehlen-zubereiten-aufbewahren/konfituere-und-marmelade-haltbarkeit-und-lagerung-58932",
    "food_in_jars": "https://foodinjars.com/blog/canning-101-long-home-canned-foods-really-last/",
    "nchfp": "https://nchfp.uga.edu/how/make-jam-jelly/jams-jellies-general-information/storing-home-canned-jams-and-jellies/",
    "haltbarkeit_net": "https://www.haltbarkeit.net/apfelmus-apfelbrei-konserve-gessst-haltbarkeit/",
    "foodwissen_chutney": "https://foodwissen.de/chutney-haltbarkeit/",
    "tomaten_de": "https://www.tomaten.de/tomatensauce-haltbar-machen/",
    "haus_und_beet": "https://haus-und-beet.de/ketchup-selber-machen/",
    "edeka_pesto": "https://www.edeka.de/wissen/tipps-und-tricks/wie-kann-ich-pesto-haltbar-machen/",
}

# Format: (name, color, parent_name, [(storage_type, min, max, source_key), ...])
# parent_name = None for top-level/standalone categories.
# Parents MUST appear before their children in this list.
CATEGORIES_WITH_SHELF_LIFE: list[tuple[str, str | None, str | None, list[tuple[StorageType, int, int, str]]]] = [
    # === FROZEN — Standalone ===
    ("Gemüse", "#4CAF50", None, [(StorageType.FROZEN, 6, 12, "vsz_be")]),
    ("Kräuter", "#8BC34A", None, [(StorageType.FROZEN, 3, 4, "vsz_be")]),
    ("Obst", "#FF9800", None, [(StorageType.FROZEN, 9, 12, "vsz_be")]),
    # === FROZEN — Fleisch (Gruppe) ===
    ("Fleisch", "#F44336", None, [(StorageType.FROZEN, 3, 12, "vsz_be")]),
    ("Rindfleisch", "#D32F2F", "Fleisch", [(StorageType.FROZEN, 9, 12, "t_online")]),
    ("Schweinefleisch", "#E57373", "Fleisch", [(StorageType.FROZEN, 4, 7, "t_online")]),
    ("Geflügel", "#FFEB3B", "Fleisch", [(StorageType.FROZEN, 3, 12, "t_online")]),
    ("Hackfleisch", "#C62828", "Fleisch", [(StorageType.FROZEN, 1, 3, "t_online")]),
    ("Wurst", "#795548", "Fleisch", [(StorageType.FROZEN, 1, 6, "vsz_be")]),
    # === FROZEN — Fisch (Gruppe) ===
    ("Fisch", "#2196F3", None, [(StorageType.FROZEN, 2, 4, "vsz_be")]),
    ("Fisch (mager)", "#64B5F6", "Fisch", [(StorageType.FROZEN, 4, 6, "t_online")]),
    ("Fisch (fett)", "#1976D2", "Fisch", [(StorageType.FROZEN, 2, 3, "t_online")]),
    ("Meeresfrüchte", "#0097A7", "Fisch", [(StorageType.FROZEN, 2, 4, "vsz_be")]),
    # === FROZEN — Backwaren (Gruppe) ===
    ("Backwaren", "#FFC107", None, [(StorageType.FROZEN, 1, 3, "vsz_be")]),
    ("Brot", "#FFE082", "Backwaren", [(StorageType.FROZEN, 1, 3, "t_online")]),
    ("Kuchen", "#FF80AB", "Backwaren", [(StorageType.FROZEN, 2, 4, "t_online")]),
    # === FROZEN — Milchprodukte (Gruppe) ===
    ("Milchprodukte", "#FFFFFF", None, [(StorageType.FROZEN, 2, 6, "vsz_be")]),
    ("Butter", "#FFF9C4", "Milchprodukte", [(StorageType.FROZEN, 6, 8, "t_online")]),
    ("Käse", "#FFE0B2", "Milchprodukte", [(StorageType.FROZEN, 2, 4, "t_online")]),
    # === FROZEN — Gekochtes (Gruppe) ===
    ("Gekochtes", "#8D6E63", None, [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Suppen", "#FFCCBC", "Gekochtes", [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Eintöpfe", "#BCAAA4", "Gekochtes", [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Fertiggerichte", "#9E9E9E", "Gekochtes", [(StorageType.FROZEN, 2, 3, "t_online")]),
    # === AMBIENT — Fruchtaufstriche (Gruppe) ===
    ("Fruchtaufstriche", "#E91E63", None, [(StorageType.AMBIENT, 12, 24, "vz_de")]),
    ("Marmelade", "#C2185B", "Fruchtaufstriche", [(StorageType.AMBIENT, 12, 24, "vz_de")]),
    ("Gelee", "#CE93D8", "Fruchtaufstriche", [(StorageType.AMBIENT, 12, 24, "food_in_jars")]),
    # === AMBIENT — Obstmus (Gruppe) ===
    ("Obstmus", "#FF8A65", None, [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")]),
    ("Apfelmus", "#A5D6A7", "Obstmus", [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")]),
    ("Pflaumenmus", "#7E57C2", "Obstmus", [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")]),
    ("Kompott", "#FFAB91", "Obstmus", [(StorageType.AMBIENT, 12, 12, "food_in_jars")]),
    # === AMBIENT — Eingelegtes (Gruppe) ===
    ("Eingelegtes", "#AED581", None, [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Essiggurken", "#689F38", "Eingelegtes", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Mixed Pickles", "#7CB342", "Eingelegtes", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    # === AMBIENT — Soßen (Gruppe) ===
    ("Soßen", "#EF5350", None, [(StorageType.AMBIENT, 6, 12, "tomaten_de")]),
    ("Tomatensoße", "#E53935", "Soßen", [(StorageType.AMBIENT, 12, 12, "tomaten_de")]),
    ("Sugo", "#D32F2F", "Soßen", [(StorageType.AMBIENT, 12, 12, "tomaten_de")]),
    ("Ketchup", "#C62828", "Soßen", [(StorageType.AMBIENT, 6, 12, "haus_und_beet")]),
    ("Pesto", "#558B2F", "Soßen", [(StorageType.AMBIENT, 6, 12, "edeka_pesto")]),
    # === AMBIENT — Würziges (Gruppe) ===
    ("Würziges", "#FF7043", None, [(StorageType.AMBIENT, 3, 12, "foodwissen_chutney")]),
    ("Chutney", "#E64A19", "Würziges", [(StorageType.AMBIENT, 6, 12, "foodwissen_chutney")]),
    ("Relish", "#8D6E63", "Würziges", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Senf", "#FFCA28", "Würziges", [(StorageType.AMBIENT, 3, 6, "vz_de")]),
    # === AMBIENT — Standalone ===
    ("Antipasti", "#FFA726", None, [(StorageType.AMBIENT, 3, 6, "nchfp")]),
    ("Fruchtsirup", "#AB47BC", None, [(StorageType.AMBIENT, 12, 12, "vz_de")]),
    ("Sauerkraut", "#C5E1A5", None, [(StorageType.AMBIENT, 6, 12, "nchfp")]),
]

# Categories without shelf-life, for general item classification (PURCHASED_FRESH etc.)
# Format: (name, color)
CATEGORIES_FRESH_ONLY: list[tuple[str, str]] = [
    ("Nudeln & Pasta", "#FFCC80"),
    ("Reis & Getreide", "#D7CCC8"),
    ("Backzutaten", "#FFECB3"),
    ("Konserven", "#90A4AE"),
    ("Gewürze", "#A1887F"),
    ("Öle & Essig", "#C8E6C9"),
    ("Getränke", "#81D4FA"),
    ("Snacks", "#FFE082"),
    ("Eier", "#FFF3E0"),
    ("Aufschnitt", "#FFAB91"),
    ("Milchprodukte (frisch)", "#E1BEE7"),
]


# =============================================================================
# Testdata
# =============================================================================

TEST_CATEGORIES = [
    ("Gemüse", "#4CAF50", 12),
    ("Obst", "#FF9800", 12),
    ("Fleisch", "#F44336", 6),
    ("Fisch", "#2196F3", 3),
    ("Milchprodukte", "#9C27B0", 3),
    ("Fertiggerichte", "#795548", 6),
    ("Backwaren", "#FFEB3B", 3),
    ("Suppen & Eintöpfe", "#FF5722", 4),
]

TEST_LOCATIONS = [
    ("Kühlschrank", LocationType.CHILLED, "Hauptkühlschrank in der Küche", "#00BCD4"),
    ("Gefriertruhe", LocationType.FROZEN, "Große Truhe im Keller", "#1565C0"),
    ("Gefrierfach", LocationType.FROZEN, "Kleines Fach im Kühlschrank", "#42A5F5"),
    ("Vorratsschrank", LocationType.AMBIENT, "Trockenlager in der Küche", "#FF8F00"),
    ("Keller", LocationType.AMBIENT, "Kühler Kellerraum", "#6D4C41"),
]


# =============================================================================
# Helper Functions
# =============================================================================


def get_or_create_system_user(session: Session) -> int:
    """Get admin user ID or create system user if none exists."""
    admin = session.exec(select(User).where(User.role == "admin")).first()
    if admin:
        assert admin.id is not None
        return admin.id

    system_user = session.exec(select(User).where(User.username == "system")).first()
    if not system_user:
        system_user = User(
            username="system",
            email="system@localhost",
            role="admin",
        )
        system_user.set_password("system-not-for-login")
        session.add(system_user)
        session.commit()
        session.refresh(system_user)
        print(f"  System-User erstellt (ID: {system_user.id})")

    assert system_user.id is not None
    return system_user.id


def get_or_create_category(
    session: Session,
    name: str,
    color: str | None,
    admin_id: int,
    parent_id: int | None = None,
    *,
    assign_parent: bool = False,
) -> Category:
    """Get existing category or create new one.

    Eine bestehende Kategorie bleibt unverändert (#460). Einzige Ausnahme:
    ``assign_parent`` ordnet eine Kategorie ohne Gruppe ``parent_id`` zu; der Seed
    setzt das nur für Gruppen, die er im selben Lauf neu angelegt hat.
    """
    category = session.exec(select(Category).where(Category.name == name)).first()
    if category:
        if assign_parent and parent_id is not None and category.parent_id is None and category.id != parent_id:
            category.parent_id = parent_id
            session.add(category)
            session.commit()
            session.refresh(category)
        return category

    category = Category(name=name, color=color, parent_id=parent_id, created_by=admin_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def create_shelf_life_if_missing(
    session: Session,
    category_id: int,
    storage_type: StorageType,
    months_min: int,
    months_max: int,
    source_url: str,
) -> CategoryShelfLife:
    """Create shelf life config unless one exists; existing values stay untouched (#460)."""
    existing = session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category_id,
            CategoryShelfLife.storage_type == storage_type,
        )
    ).first()

    if existing:
        return existing

    shelf_life = CategoryShelfLife(
        category_id=category_id,
        storage_type=storage_type,
        months_min=months_min,
        months_max=months_max,
        source_url=source_url,
    )
    session.add(shelf_life)
    session.commit()
    session.refresh(shelf_life)
    return shelf_life


# =============================================================================
# Main Seed Functions
# =============================================================================


def seed_shelf_life_defaults(session: Session) -> tuple[int, int]:
    """Seed default shelf life data.

    Legt nur Fehlendes an: Kategorien und Haltbarkeiten, die es noch nicht gibt.
    Bestehende Werte bleiben unverändert, auch wenn sie vom Standard abweichen (#460);
    Korrekturen an Standardwerten gehören in eine Migration.

    Returns:
        Tuple of (categories_count, shelf_lives_count)
    """
    admin_id = get_or_create_system_user(session)

    categories_created = 0
    shelf_lives_created = 0

    # Track created categories by name for parent lookup
    category_by_name: dict[str, Category] = {}
    # Gruppen, die dieser Lauf neu anlegt: nur ihnen werden bestehende Kategorien
    # ohne Gruppe zugeordnet (Datenbanken vor #351). Bestehende Gruppen hat der
    # Nutzer womöglich selbst geordnet (#460).
    new_groups: set[str] = set()

    for name, color, parent_name, shelf_lives in CATEGORIES_WITH_SHELF_LIFE:
        parent_id = category_by_name[parent_name].id if parent_name else None
        existed = session.exec(select(Category.id).where(Category.name == name)).first() is not None
        category = get_or_create_category(
            session, name, color, admin_id, parent_id, assign_parent=parent_name in new_groups
        )
        if not existed and parent_name is None:
            new_groups.add(name)
        category_by_name[name] = category
        categories_created += 1

        for storage_type, months_min, months_max, source_key in shelf_lives:
            source_url = SOURCES.get(source_key, "")
            create_shelf_life_if_missing(
                session,
                category.id,  # type: ignore[arg-type]
                storage_type,
                months_min,
                months_max,
                source_url,
            )
            shelf_lives_created += 1

    # Fresh-only categories (no shelf-life)
    for name, color in CATEGORIES_FRESH_ONLY:
        get_or_create_category(session, name, color, admin_id)
        categories_created += 1

    return categories_created, shelf_lives_created


def seed_testdata(session: Session) -> dict[str, int]:
    """Seed test data for development.

    Creates:
    - Admin user (admin/admin)
    - Test categories
    - Test locations
    - Sample items

    Returns:
        Dict with counts: {"admin": 0|1, "categories": n, "locations": n, "items": n}
    """
    result = {"admin": 0, "categories": 0, "locations": 0, "items": 0}

    # Admin user
    admin = get_user_by_username(session, "admin")
    if admin is None:
        admin = create_user(
            session=session,
            username="admin",
            email="admin@fuellhorn.local",
            password="admin",
            role=Role.ADMIN,
        )
        result["admin"] = 1

    assert admin.id is not None
    admin_id = admin.id

    # Categories
    category_ids: dict[str, int] = {}
    for name, color, freeze_months in TEST_CATEGORIES:
        existing = session.exec(select(Category).where(Category.name == name)).first()
        if existing:
            category_ids[name] = existing.id  # type: ignore[assignment]
            continue

        cat = Category(
            name=name,
            color=color,
            freeze_time_months=freeze_months,
            created_by=admin_id,
        )
        session.add(cat)
        session.flush()
        category_ids[name] = cat.id  # type: ignore[assignment]
        result["categories"] += 1

    session.commit()

    # Locations
    location_ids: dict[str, int] = {}
    for name, loc_type, desc, color in TEST_LOCATIONS:
        existing = session.exec(select(Location).where(Location.name == name)).first()
        if existing:
            if not existing.color:
                existing.color = color
                session.add(existing)
            location_ids[name] = existing.id  # type: ignore[assignment]
            continue

        loc = Location(
            name=name,
            location_type=loc_type,
            description=desc,
            color=color,
            created_by=admin_id,
        )
        session.add(loc)
        session.flush()
        location_ids[name] = loc.id  # type: ignore[assignment]
        result["locations"] += 1

    session.commit()

    # Sample items
    today = date.today()
    items: list[dict[str, Any]] = [
        {
            "product_name": "Milch",
            "item_type": ItemType.PURCHASED_FRESH,
            "quantity": 1,
            "unit": "L",
            "location": "Kühlschrank",
            "category": "Milchprodukte",
            "best_before": today + timedelta(days=2),
            "expiry": today + timedelta(days=2),
        },
        {
            "product_name": "Joghurt",
            "item_type": ItemType.PURCHASED_FRESH,
            "quantity": 4,
            "unit": "Stk",
            "location": "Kühlschrank",
            "category": "Milchprodukte",
            "best_before": today + timedelta(days=1),
            "expiry": today + timedelta(days=1),
        },
        {
            "product_name": "Hackfleisch (TK)",
            "item_type": ItemType.PURCHASED_THEN_FROZEN,
            "quantity": 500,
            "unit": "g",
            "location": "Gefriertruhe",
            "category": "Fleisch",
            "best_before": today - timedelta(days=30),
            "freeze_date": today - timedelta(days=30),
            "expiry": today + timedelta(days=5),
        },
        {
            "product_name": "Erbsen (TK)",
            "item_type": ItemType.PURCHASED_FROZEN,
            "quantity": 450,
            "unit": "g",
            "location": "Gefrierfach",
            "category": "Gemüse",
            "best_before": today + timedelta(days=180),
            "expiry": today + timedelta(days=180),
        },
        {
            "product_name": "Tomatensuppe",
            "item_type": ItemType.HOMEMADE_FROZEN,
            "quantity": 1,
            "unit": "L",
            "location": "Gefriertruhe",
            "category": "Suppen & Eintöpfe",
            "best_before": today - timedelta(days=14),
            "freeze_date": today - timedelta(days=14),
            "expiry": today + timedelta(days=100),
        },
        {
            "product_name": "Apfelmus",
            "item_type": ItemType.HOMEMADE_PRESERVED,
            "quantity": 3,
            "unit": "Gläser",
            "location": "Keller",
            "category": "Obst",
            "best_before": today - timedelta(days=60),
            "expiry": today + timedelta(days=300),
        },
        {
            "product_name": "Lachs",
            "item_type": ItemType.PURCHASED_FROZEN,
            "quantity": 400,
            "unit": "g",
            "location": "Gefriertruhe",
            "category": "Fisch",
            "best_before": today + timedelta(days=60),
            "expiry": today + timedelta(days=60),
        },
        {
            "product_name": "Brot",
            "item_type": ItemType.PURCHASED_THEN_FROZEN,
            "quantity": 1,
            "unit": "Stk",
            "location": "Gefrierfach",
            "category": "Backwaren",
            "best_before": today - timedelta(days=3),
            "freeze_date": today - timedelta(days=3),
            "expiry": today + timedelta(days=87),
        },
    ]

    for item_data in items:
        existing = session.exec(select(Item).where(Item.product_name == item_data["product_name"])).first()
        if existing:
            continue

        location_name = str(item_data["location"])
        category_name = str(item_data.get("category", ""))
        item = Item(
            product_name=str(item_data["product_name"]),
            item_type=item_data["item_type"],
            quantity=int(item_data["quantity"]),
            unit=str(item_data["unit"]),
            location_id=location_ids[location_name],
            category_id=category_ids.get(category_name),
            best_before_date=item_data["best_before"],
            freeze_date=item_data.get("freeze_date"),
            expiry_date=item_data["expiry"],
            created_by=admin_id,
        )
        session.add(item)
        result["items"] += 1

    session.commit()
    return result
