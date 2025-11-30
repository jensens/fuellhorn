"""Seed test data for development.

Creates:
- Admin user (admin/admin)
- Test categories
- Test locations
- Sample items
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, timedelta  # noqa: E402

from sqlmodel import select  # noqa: E402

from app.database import get_session  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.item import Item, ItemType  # noqa: E402
from app.models.location import Location, LocationType  # noqa: E402
from app.models.user import Role  # noqa: E402
from app.services.auth_service import create_user, get_user_by_username  # noqa: E402


def seed_admin(session) -> int:
    """Create admin user if not exists. Returns admin user ID."""
    try:
        admin = get_user_by_username(session, "admin")
        print("  ✓ Admin existiert bereits")
        return admin.id
    except Exception:
        pass

    admin = create_user(
        session=session,
        username="admin",
        email="admin@fuellhorn.local",
        password="admin",
        role=Role.ADMIN,
    )
    print("  ✓ Admin erstellt (admin/admin)")
    return admin.id


def seed_categories(session, admin_id: int) -> dict[str, int]:
    """Create test categories. Returns name -> id mapping."""
    categories = [
        ("Gemüse", "#4CAF50", 12),  # Grün, 12 Monate Gefrierzeit
        ("Obst", "#FF9800", 12),  # Orange
        ("Fleisch", "#F44336", 6),  # Rot, 6 Monate
        ("Fisch", "#2196F3", 3),  # Blau, 3 Monate
        ("Milchprodukte", "#9C27B0", 3),  # Lila
        ("Fertiggerichte", "#795548", 6),  # Braun
        ("Backwaren", "#FFEB3B", 3),  # Gelb
        ("Suppen & Eintöpfe", "#FF5722", 4),  # Deep Orange
    ]

    result = {}
    for name, color, freeze_months in categories:
        existing = session.exec(select(Category).where(Category.name == name)).first()
        if existing:
            result[name] = existing.id
            continue

        cat = Category(
            name=name,
            color=color,
            freeze_time_months=freeze_months,
            created_by=admin_id,
        )
        session.add(cat)
        session.flush()
        result[name] = cat.id

    session.commit()
    print(f"  ✓ {len(categories)} Kategorien")
    return result


def seed_locations(session, admin_id: int) -> dict[str, int]:
    """Create test locations. Returns name -> id mapping."""
    locations = [
        ("Kühlschrank", LocationType.CHILLED, "Hauptkühlschrank in der Küche"),
        ("Gefriertruhe", LocationType.FROZEN, "Große Truhe im Keller"),
        ("Gefrierfach", LocationType.FROZEN, "Kleines Fach im Kühlschrank"),
        ("Vorratsschrank", LocationType.AMBIENT, "Trockenlager in der Küche"),
        ("Keller", LocationType.AMBIENT, "Kühler Kellerraum"),
    ]

    result = {}
    for name, loc_type, desc in locations:
        existing = session.exec(select(Location).where(Location.name == name)).first()
        if existing:
            result[name] = existing.id
            continue

        loc = Location(
            name=name,
            location_type=loc_type,
            description=desc,
            created_by=admin_id,
        )
        session.add(loc)
        session.flush()
        result[name] = loc.id

    session.commit()
    print(f"  ✓ {len(locations)} Lagerorte")
    return result


def seed_items(session, admin_id: int, categories: dict, locations: dict) -> None:
    """Create sample items for testing."""
    today = date.today()

    items = [
        # Kritisch (rot) - läuft bald ab
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
        # Warnung (gelb)
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
        # OK (grün)
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

    created = 0
    for item_data in items:
        # Check if similar item exists
        existing = session.exec(
            select(Item).where(Item.product_name == item_data["product_name"])
        ).first()
        if existing:
            continue

        item = Item(
            product_name=item_data["product_name"],
            item_type=item_data["item_type"],
            quantity=item_data["quantity"],
            unit=item_data["unit"],
            location_id=locations[item_data["location"]],
            category_id=categories.get(item_data.get("category")),
            best_before_date=item_data["best_before"],
            freeze_date=item_data.get("freeze_date"),
            expiry_date=item_data["expiry"],
            created_by=admin_id,
        )
        session.add(item)
        created += 1

    session.commit()
    print(f"  ✓ {created} Test-Artikel")


def main() -> None:
    """Seed all test data."""
    print("🌱 Testdaten initialisieren...")

    with next(get_session()) as session:
        admin_id = seed_admin(session)
        categories = seed_categories(session, admin_id)
        locations = seed_locations(session, admin_id)
        seed_items(session, admin_id, categories, locations)

    print("✅ Fertig!")


if __name__ == "__main__":
    main()
