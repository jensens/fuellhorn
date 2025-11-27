#!/usr/bin/env python3
"""Seed-Script für Default-Haltbarkeiten.

Dieses Script pflegt die recherchierten Haltbarkeitszeiten für verschiedene
Lebensmittelkategorien in die Datenbank ein.

Ausführung:
    uv run python scripts/seed_shelf_life_defaults.py

Das Script ist idempotent - es kann mehrfach ausgeführt werden ohne
Duplikate zu erzeugen (nutzt create_or_update).
"""

from pathlib import Path
import sys


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import create_db_and_tables
from app.database import get_engine
from app.models.category import Category
from app.models.category_shelf_life import CategoryShelfLife
from app.models.category_shelf_life import StorageType
from sqlmodel import Session
from sqlmodel import select


# Quellen-URLs
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


# Kategorien mit Haltbarkeiten
# Format: (name, color, [(storage_type, min, max, source_key), ...])
CATEGORIES_WITH_SHELF_LIFE: list[tuple[str, str | None, list[tuple[StorageType, int, int, str]]]] = [
    # === FROZEN (Tiefgekühlt) ===
    (
        "Gemüse",
        "#4CAF50",  # Grün
        [(StorageType.FROZEN, 6, 12, "vsz_be")],
    ),
    (
        "Kräuter",
        "#8BC34A",  # Hellgrün
        [(StorageType.FROZEN, 3, 4, "vsz_be")],
    ),
    (
        "Obst",
        "#FF9800",  # Orange
        [(StorageType.FROZEN, 9, 12, "vsz_be")],
    ),
    (
        "Fleisch",
        "#F44336",  # Rot
        [(StorageType.FROZEN, 3, 12, "vsz_be")],
    ),
    (
        "Rindfleisch",
        "#D32F2F",  # Dunkelrot
        [(StorageType.FROZEN, 9, 12, "t_online")],
    ),
    (
        "Schweinefleisch",
        "#E57373",  # Hellrot
        [(StorageType.FROZEN, 4, 7, "t_online")],
    ),
    (
        "Geflügel",
        "#FFEB3B",  # Gelb
        [(StorageType.FROZEN, 3, 12, "t_online")],
    ),
    (
        "Hackfleisch",
        "#C62828",  # Dunkelrot
        [(StorageType.FROZEN, 1, 3, "t_online")],
    ),
    (
        "Fisch",
        "#2196F3",  # Blau
        [(StorageType.FROZEN, 2, 4, "vsz_be")],
    ),
    (
        "Fisch (mager)",
        "#64B5F6",  # Hellblau
        [(StorageType.FROZEN, 4, 6, "t_online")],
    ),
    (
        "Fisch (fett)",
        "#1976D2",  # Dunkelblau
        [(StorageType.FROZEN, 2, 3, "t_online")],
    ),
    (
        "Wurst",
        "#795548",  # Braun
        [(StorageType.FROZEN, 1, 6, "vsz_be")],
    ),
    (
        "Backwaren",
        "#FFC107",  # Amber
        [(StorageType.FROZEN, 1, 3, "vsz_be")],
    ),
    (
        "Brot",
        "#FFE082",  # Helles Amber
        [(StorageType.FROZEN, 1, 3, "t_online")],
    ),
    (
        "Kuchen",
        "#FF80AB",  # Pink
        [(StorageType.FROZEN, 2, 4, "t_online")],
    ),
    (
        "Milchprodukte",
        "#FFFFFF",  # Weiß
        [(StorageType.FROZEN, 2, 6, "vsz_be")],
    ),
    (
        "Butter",
        "#FFF9C4",  # Helles Gelb
        [(StorageType.FROZEN, 6, 8, "t_online")],
    ),
    (
        "Käse",
        "#FFE0B2",  # Helles Orange
        [(StorageType.FROZEN, 2, 4, "t_online")],
    ),
    (
        "Fertiggerichte",
        "#9E9E9E",  # Grau
        [(StorageType.FROZEN, 2, 3, "t_online")],
    ),
    (
        "Suppen",
        "#FFCCBC",  # Helles Koralle
        [(StorageType.FROZEN, 2, 3, "usda")],
    ),
    (
        "Eintöpfe",
        "#BCAAA4",  # Helles Braun
        [(StorageType.FROZEN, 2, 3, "usda")],
    ),
    # === AMBIENT (Eingemachtes) ===
    (
        "Marmelade",
        "#E91E63",  # Pink
        [(StorageType.AMBIENT, 12, 24, "vz_de")],
    ),
    (
        "Konfitüre",
        "#F48FB1",  # Helles Pink
        [(StorageType.AMBIENT, 12, 24, "vz_de")],
    ),
    (
        "Gelee",
        "#CE93D8",  # Helles Lila
        [(StorageType.AMBIENT, 12, 24, "food_in_jars")],
    ),
    (
        "Kompott",
        "#FFAB91",  # Helles Orange
        [(StorageType.AMBIENT, 12, 12, "food_in_jars")],
    ),
    (
        "Obstmus",
        "#FF8A65",  # Koralle
        [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")],
    ),
    (
        "Apfelmus",
        "#A5D6A7",  # Helles Grün
        [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")],
    ),
    (
        "Pflaumenmus",
        "#7E57C2",  # Lila
        [(StorageType.AMBIENT, 12, 18, "haltbarkeit_net")],
    ),
    (
        "Eingelegtes",
        "#AED581",  # Hellgrün
        [(StorageType.AMBIENT, 6, 12, "nchfp")],
    ),
    (
        "Essiggurken",
        "#689F38",  # Dunkelgrün
        [(StorageType.AMBIENT, 6, 12, "nchfp")],
    ),
    (
        "Mixed Pickles",
        "#7CB342",  # Grün
        [(StorageType.AMBIENT, 6, 12, "nchfp")],
    ),
    (
        "Chutney",
        "#FF7043",  # Dunkles Orange
        [(StorageType.AMBIENT, 6, 12, "foodwissen_chutney")],
    ),
    (
        "Relish",
        "#8D6E63",  # Braun
        [(StorageType.AMBIENT, 6, 12, "nchfp")],
    ),
    (
        "Tomatensoße",
        "#EF5350",  # Rot
        [(StorageType.AMBIENT, 12, 12, "tomaten_de")],
    ),
    (
        "Sugo",
        "#E53935",  # Dunkelrot
        [(StorageType.AMBIENT, 12, 12, "tomaten_de")],
    ),
    (
        "Ketchup",
        "#D32F2F",  # Ketchup-Rot
        [(StorageType.AMBIENT, 6, 12, "haus_und_beet")],
    ),
    (
        "Pesto",
        "#558B2F",  # Dunkelgrün
        [(StorageType.AMBIENT, 6, 12, "edeka_pesto")],
    ),
    (
        "Antipasti",
        "#FFA726",  # Orange
        [(StorageType.AMBIENT, 3, 6, "nchfp")],
    ),
    (
        "Senf",
        "#FFCA28",  # Senfgelb
        [(StorageType.AMBIENT, 3, 6, "vz_de")],
    ),
    (
        "Fruchtsirup",
        "#AB47BC",  # Lila
        [(StorageType.AMBIENT, 12, 12, "vz_de")],
    ),
    (
        "Sauerkraut",
        "#C5E1A5",  # Helles Grün
        [(StorageType.AMBIENT, 6, 12, "nchfp")],
    ),
]


def get_or_create_category(session: Session, name: str, color: str | None, admin_id: int) -> Category:
    """Get existing category or create new one."""
    category = session.exec(select(Category).where(Category.name == name)).first()
    if category:
        print(f"  Kategorie '{name}' existiert bereits (ID: {category.id})")
        return category

    category = Category(name=name, color=color, created_by=admin_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    print(f"  Kategorie '{name}' erstellt (ID: {category.id})")
    return category


def create_or_update_shelf_life(
    session: Session,
    category_id: int,
    storage_type: StorageType,
    months_min: int,
    months_max: int,
    source_url: str,
) -> CategoryShelfLife:
    """Create or update shelf life config."""
    existing = session.exec(
        select(CategoryShelfLife).where(
            CategoryShelfLife.category_id == category_id,
            CategoryShelfLife.storage_type == storage_type,
        )
    ).first()

    if existing:
        existing.months_min = months_min
        existing.months_max = months_max
        existing.source_url = source_url
        session.add(existing)
        session.commit()
        session.refresh(existing)
        print(f"    Haltbarkeit aktualisiert: {storage_type.value} = {months_min}-{months_max} Monate")
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
    print(f"    Haltbarkeit erstellt: {storage_type.value} = {months_min}-{months_max} Monate")
    return shelf_life


def get_admin_user_id(session: Session) -> int:
    """Get the first admin user ID or create system user if none exists."""
    from app.models.user import User

    admin = session.exec(select(User).where(User.role == "admin")).first()
    if admin:
        assert admin.id is not None
        return admin.id

    # Fallback: check for existing system user
    system_user = session.exec(select(User).where(User.username == "system")).first()
    if not system_user:
        # Create system user
        system_user = User(
            username="system",
            email="system@localhost",
            role="admin",
        )
        system_user.set_password("system-not-for-login")
        session.add(system_user)
        session.commit()
        session.refresh(system_user)
        print(f"System-User erstellt (ID: {system_user.id})")

    assert system_user.id is not None
    return system_user.id


def seed_shelf_life_defaults() -> None:
    """Seed default shelf life data into the database."""
    print("=" * 60)
    print("Seeding Default-Haltbarkeiten")
    print("=" * 60)

    # Ensure tables exist
    create_db_and_tables()

    with Session(get_engine()) as session:
        # Get admin user ID for created_by
        admin_id = get_admin_user_id(session)
        print(f"\nVerwende Admin-User ID: {admin_id}")

        categories_created = 0
        shelf_lives_created = 0

        print("\nVerarbeite Kategorien und Haltbarkeiten...")
        print("-" * 60)

        for name, color, shelf_lives in CATEGORIES_WITH_SHELF_LIFE:
            category = get_or_create_category(session, name, color, admin_id)
            categories_created += 1

            for storage_type, months_min, months_max, source_key in shelf_lives:
                source_url = SOURCES.get(source_key, "")
                create_or_update_shelf_life(
                    session,
                    category.id,  # type: ignore
                    storage_type,
                    months_min,
                    months_max,
                    source_url,
                )
                shelf_lives_created += 1

        print("-" * 60)
        print("\nZusammenfassung:")
        print(f"  Kategorien verarbeitet: {categories_created}")
        print(f"  Haltbarkeiten verarbeitet: {shelf_lives_created}")
        print("=" * 60)


if __name__ == "__main__":
    seed_shelf_life_defaults()
