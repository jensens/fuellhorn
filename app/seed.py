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
from app.services import item_service
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
    "oekotest_milch": "https://www.oekotest.de/essen-trinken/Milch-einfrieren-So-bleibt-Milch-lange-haltbar_11630_1.html",
    "utopia_sahne": "https://utopia.de/ratgeber/sahne-einfrieren-so-klappt-es/",
    "vz_nrw_einfrieren": "https://www.verbraucherzentrale.nrw/9-lebensmittel-die-man-einfrieren-kann-butter-eier-rohen-teig-mehr-99308",
    "csu_drying_fruits": "https://extension.colostate.edu/resource/drying-fruits/",
    "csu_drying_vegetables": "https://extension.colostate.edu/resource/drying-vegetables/",
    "osu_drying_herbs": "https://extension.oregonstate.edu/food/preservation/drying-herbs",
}

# Format: (name, color, parent_name, [(storage_type, min, max, source_key), ...])
# parent_name = None for top-level/standalone categories.
# Leere Haltbarkeitsliste = nur für frisch Gekauftes (z. B. Nudeln, Getränke).
# Parents MUST appear before their children in this list.
CATEGORIES: list[tuple[str, str | None, str | None, list[tuple[StorageType, int, int, str]]]] = [
    # Eine Gruppe hat nur dann eine eigene Haltbarkeit, wenn alle ihre Kategorien sie
    # brauchen: Kategorien ohne eigenen Wert erben ihn (#395), und eine geerbte
    # Gefrierzeit würde z. B. Joghurt beim Einfrieren anbieten (#456).
    # === Obst & Gemüse ===
    ("Obst & Gemüse", "#66BB6A", None, []),
    ("Gemüse", "#4CAF50", "Obst & Gemüse", [(StorageType.FROZEN, 6, 12, "vsz_be")]),
    ("Obst", "#FF9800", "Obst & Gemüse", [(StorageType.FROZEN, 9, 12, "vsz_be")]),
    ("Kräuter", "#8BC34A", "Obst & Gemüse", [(StorageType.FROZEN, 3, 4, "vsz_be")]),
    # === Fleisch & Wurst ===
    ("Fleisch & Wurst", "#F44336", None, [(StorageType.FROZEN, 3, 12, "vsz_be")]),
    ("Rindfleisch", "#D32F2F", "Fleisch & Wurst", [(StorageType.FROZEN, 9, 12, "t_online")]),
    ("Schweinefleisch", "#E57373", "Fleisch & Wurst", [(StorageType.FROZEN, 4, 7, "t_online")]),
    ("Geflügel", "#FFEB3B", "Fleisch & Wurst", [(StorageType.FROZEN, 3, 12, "t_online")]),
    ("Hackfleisch", "#C62828", "Fleisch & Wurst", [(StorageType.FROZEN, 1, 3, "t_online")]),
    ("Wurst", "#795548", "Fleisch & Wurst", [(StorageType.FROZEN, 1, 6, "vsz_be")]),
    # === Fisch ===
    ("Fisch", "#2196F3", None, [(StorageType.FROZEN, 2, 4, "vsz_be")]),
    ("Fisch (mager)", "#64B5F6", "Fisch", [(StorageType.FROZEN, 4, 6, "t_online")]),
    ("Fisch (fett)", "#1976D2", "Fisch", [(StorageType.FROZEN, 2, 3, "t_online")]),
    ("Meeresfrüchte", "#0097A7", "Fisch", [(StorageType.FROZEN, 2, 4, "vsz_be")]),
    # === Milchprodukte & Eier: Frischkäse, Joghurt, Sauerrahm werden gefroren grießig ===
    ("Milchprodukte & Eier", "#78909C", None, []),
    ("Butter", "#F9A825", "Milchprodukte & Eier", [(StorageType.FROZEN, 6, 8, "t_online")]),
    ("Käse", "#FFB74D", "Milchprodukte & Eier", [(StorageType.FROZEN, 2, 4, "t_online")]),
    ("Milch", "#5C9BD5", "Milchprodukte & Eier", [(StorageType.FROZEN, 2, 3, "oekotest_milch")]),
    ("Sahne", "#D4B483", "Milchprodukte & Eier", [(StorageType.FROZEN, 2, 3, "utopia_sahne")]),
    ("Topfen", "#C9A66B", "Milchprodukte & Eier", [(StorageType.FROZEN, 10, 12, "vz_nrw_einfrieren")]),
    ("Frischkäse", "#9FA8DA", "Milchprodukte & Eier", []),
    ("Joghurt", "#BA68C8", "Milchprodukte & Eier", []),
    ("Sauerrahm & Schmand", "#7986CB", "Milchprodukte & Eier", []),
    ("Eier", "#D4A373", "Milchprodukte & Eier", []),
    # === Backwaren ===
    ("Backwaren", "#FFC107", None, [(StorageType.FROZEN, 1, 3, "vsz_be")]),
    ("Brot", "#FFE082", "Backwaren", [(StorageType.FROZEN, 1, 3, "t_online")]),
    ("Kuchen", "#FF80AB", "Backwaren", [(StorageType.FROZEN, 2, 4, "t_online")]),
    # === Gekochtes ===
    ("Gekochtes", "#8D6E63", None, [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Suppen", "#FFCCBC", "Gekochtes", [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Eintöpfe", "#BCAAA4", "Gekochtes", [(StorageType.FROZEN, 2, 3, "usda")]),
    ("Fertiggerichte", "#9E9E9E", "Gekochtes", [(StorageType.FROZEN, 2, 3, "t_online")]),
    # === Süßes Eingemachtes ===
    ("Süßes Eingemachtes", "#E91E63", None, [(StorageType.AMBIENT, 12, 24, "vz_de")]),
    ("Marmelade", "#C2185B", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 24, "vz_de")]),
    ("Gelee", "#CE93D8", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 24, "food_in_jars")]),
    ("Apfelmus", "#A5D6A7", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")]),
    ("Pflaumenmus", "#7E57C2", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")]),
    ("Kompott", "#FFAB91", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 12, "food_in_jars")]),
    ("Fruchtsirup", "#AB47BC", "Süßes Eingemachtes", [(StorageType.AMBIENT, 12, 12, "vz_de")]),
    # === Eingelegtes ===
    ("Eingelegtes", "#AED581", None, [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Essiggurken", "#689F38", "Eingelegtes", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Mixed Pickles", "#7CB342", "Eingelegtes", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Sauerkraut", "#C5E1A5", "Eingelegtes", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    ("Antipasti", "#FFA726", "Eingelegtes", [(StorageType.AMBIENT, 3, 6, "nchfp")]),
    # === Soßen ===
    ("Soßen", "#EF5350", None, [(StorageType.AMBIENT, 6, 12, "tomaten_de")]),
    ("Tomatensoße", "#E53935", "Soßen", [(StorageType.AMBIENT, 12, 12, "tomaten_de")]),
    ("Sugo", "#D32F2F", "Soßen", [(StorageType.AMBIENT, 12, 12, "tomaten_de")]),
    ("Pesto", "#558B2F", "Soßen", [(StorageType.AMBIENT, 6, 12, "edeka_pesto")]),
    # === Würzsaucen ===
    ("Würzsaucen", "#FF7043", None, [(StorageType.AMBIENT, 3, 12, "foodwissen_chutney")]),
    ("Ketchup", "#C62828", "Würzsaucen", [(StorageType.AMBIENT, 6, 12, "haus_und_beet")]),
    ("Senf", "#FFCA28", "Würzsaucen", [(StorageType.AMBIENT, 3, 6, "vz_de")]),
    ("Chutney", "#E64A19", "Würzsaucen", [(StorageType.AMBIENT, 6, 12, "foodwissen_chutney")]),
    ("Relish", "#8D6E63", "Würzsaucen", [(StorageType.AMBIENT, 6, 12, "nchfp")]),
    # === Getrocknetes: selbst gedörrt, Raumtemperatur, luftdicht (#476); Werte = Qualität, nicht Sicherheit ===
    ("Getrocknetes", "#BF8F5B", None, []),
    ("Trockenobst", "#C0763A", "Getrocknetes", [(StorageType.AMBIENT, 6, 12, "csu_drying_fruits")]),
    ("Trockengemüse", "#8A9A5B", "Getrocknetes", [(StorageType.AMBIENT, 6, 12, "csu_drying_vegetables")]),
    ("Getrocknete Pilze", "#7B5E4A", "Getrocknetes", [(StorageType.AMBIENT, 6, 12, "csu_drying_vegetables")]),
    ("Getrocknete Kräuter & Tee", "#6B8E23", "Getrocknetes", [(StorageType.AMBIENT, 6, 12, "osu_drying_herbs")]),
    # === Vorrat (nur frisch gekauft, ohne Haltbarkeit) ===
    ("Vorrat", "#6D4C41", None, []),
    ("Nudeln & Pasta", "#FFCC80", "Vorrat", []),
    ("Reis & Getreide", "#D7CCC8", "Vorrat", []),
    ("Backzutaten", "#FFECB3", "Vorrat", []),
    ("Konserven", "#90A4AE", "Vorrat", []),
    ("Gewürze", "#A1887F", "Vorrat", []),
    ("Öle & Essig", "#C8E6C9", "Vorrat", []),
    ("Getränke", "#81D4FA", "Vorrat", []),
    ("Snacks", "#FFE082", "Vorrat", []),
]


# =============================================================================
# Testdata
# =============================================================================

# Passwort des Testdaten-Admins: erfüllt die Passwortregel (mindestens 8 Zeichen, #383).
# Nur für die Entwicklung; Doku und Skripte nennen genau diesen Wert (#468).
TESTDATA_ADMIN_PASSWORD = "admin123"

# (Name, Farbe, Haltbarkeiten als (Lagerart, Monate von, Monate bis)). Die Beispielartikel
# entstehen über den Dienst und brauchen bei berechneter Haltbarkeit eine passende
# Kategorie (#385); ohne sie zeigten sie "Keine Haltbarkeitsdaten" (#468).
TEST_CATEGORIES: list[tuple[str, str, tuple[tuple[StorageType, int, int], ...]]] = [
    ("Gemüse", "#4CAF50", ((StorageType.FROZEN, 8, 12),)),
    ("Obst", "#FF9800", ((StorageType.FROZEN, 8, 12), (StorageType.AMBIENT, 12, 24))),
    ("Fleisch", "#F44336", ((StorageType.FROZEN, 3, 6),)),
    ("Fisch", "#2196F3", ((StorageType.FROZEN, 2, 3),)),
    ("Milchprodukte", "#9C27B0", ((StorageType.FROZEN, 2, 3),)),
    ("Fertiggerichte", "#795548", ((StorageType.FROZEN, 3, 6),)),
    ("Backwaren", "#FFEB3B", ((StorageType.FROZEN, 1, 3),)),
    ("Suppen & Eintöpfe", "#FF5722", ((StorageType.FROZEN, 3, 4),)),
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

    Legt nur fehlende Kategorien an, samt ihrer Standard-Haltbarkeiten. Bestehende
    Kategorien bleiben unverändert, auch wenn sie vom Standard abweichen (#460) oder
    eine Haltbarkeit fehlt, etwa weil der Nutzer sie gelöscht hat (#462);
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

    for name, color, parent_name, shelf_lives in CATEGORIES:
        parent_id = category_by_name[parent_name].id if parent_name else None
        existed = session.exec(select(Category.id).where(Category.name == name)).first() is not None
        category = get_or_create_category(
            session, name, color, admin_id, parent_id, assign_parent=parent_name in new_groups
        )
        if not existed and parent_name is None:
            new_groups.add(name)
        category_by_name[name] = category
        categories_created += 1

        if existed:
            continue  # fehlende Haltbarkeit nicht nachtragen: verschöbe Ablaufdaten (#462)

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

    return categories_created, shelf_lives_created


def seed_testdata(session: Session) -> dict[str, int]:
    """Seed test data for development.

    Creates:
    - Admin user ``admin`` mit ``TESTDATA_ADMIN_PASSWORD``
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
            password=TESTDATA_ADMIN_PASSWORD,
            role=Role.ADMIN,
        )
        result["admin"] = 1

    assert admin.id is not None
    admin_id = admin.id

    # Categories
    category_ids: dict[str, int] = {}
    for name, color, shelf_lives in TEST_CATEGORIES:
        existing = session.exec(select(Category).where(Category.name == name)).first()
        if existing:
            category_ids[name] = existing.id  # type: ignore[assignment]
        else:
            cat = Category(
                name=name,
                color=color,
                created_by=admin_id,
            )
            session.add(cat)
            session.flush()
            category_ids[name] = cat.id  # type: ignore[assignment]
            result["categories"] += 1

        # Nur fehlende Haltbarkeiten ergänzen; angepasste bleiben (#460)
        for storage_type, months_min, months_max in shelf_lives:
            create_shelf_life_if_missing(
                session,
                category_id=category_ids[name],
                storage_type=storage_type,
                months_min=months_min,
                months_max=months_max,
                source_url="",
            )

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
        },
        {
            "product_name": "Joghurt",
            "item_type": ItemType.PURCHASED_FRESH,
            "quantity": 4,
            "unit": "Stk",
            "location": "Kühlschrank",
            "category": "Milchprodukte",
            "best_before": today + timedelta(days=1),
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
        },
        {
            "product_name": "Erbsen (TK)",
            "item_type": ItemType.PURCHASED_FROZEN,
            "quantity": 450,
            "unit": "g",
            "location": "Gefrierfach",
            "category": "Gemüse",
            "best_before": today + timedelta(days=180),
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
        },
        {
            "product_name": "Apfelmus",
            "item_type": ItemType.HOMEMADE_PRESERVED,
            "quantity": 3,
            "unit": "Gläser",
            "location": "Keller",
            "category": "Obst",
            "best_before": today - timedelta(days=60),
        },
        {
            "product_name": "Lachs",
            "item_type": ItemType.PURCHASED_FROZEN,
            "quantity": 400,
            "unit": "g",
            "location": "Gefriertruhe",
            "category": "Fisch",
            "best_before": today + timedelta(days=60),
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
        },
    ]

    for item_data in items:
        existing = session.exec(select(Item).where(Item.product_name == item_data["product_name"])).first()
        if existing:
            continue

        # Über den Dienst, damit die Beispiele dieselben Regeln erfüllen wie erfasste Artikel (#468)
        item_service.create_item(
            session,
            product_name=str(item_data["product_name"]),
            best_before_date=item_data["best_before"],
            quantity=item_data["quantity"],
            unit=str(item_data["unit"]),
            item_type=item_data["item_type"],
            location_id=location_ids[str(item_data["location"])],
            created_by=admin_id,
            category_id=category_ids[str(item_data["category"])],
            freeze_date=item_data.get("freeze_date"),
        )
        result["items"] += 1

    session.commit()
    return result
