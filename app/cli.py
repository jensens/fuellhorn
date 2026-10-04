"""CLI entry point for fuellhorn."""

import os
from pathlib import Path
from sqlmodel import Session
import sys


def run_migrations() -> None:
    """Run alembic migrations from installed package."""
    from alembic import command
    from alembic.config import Config as AlembicConfig
    import app.alembic
    from app.config import Config

    alembic_dir = Path(app.alembic.__file__).parent

    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(alembic_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", Config.get_database_url())

    command.upgrade(alembic_cfg, "head")


def create_admin_user(session: Session, reset_existing: bool = False) -> bool:
    """Create initial admin user from environment variables.

    Supports environment variables for Kubernetes init container usage:
    - ADMIN_USERNAME: Admin username (default: "admin")
    - ADMIN_EMAIL: Admin email (default: "admin@fuellhorn.local")
    - ADMIN_PASSWORD: Admin password (required, no default for security)

    Args:
        session: Database session
        reset_existing: Recovery (Issue #380): bestehenden Benutzer auf Admin, aktiv
            und das Passwort aus ADMIN_PASSWORD zurücksetzen

    Returns:
        True if user was created or reset, False if user already exists

    Raises:
        ValueError: If ADMIN_PASSWORD environment variable is not set
    """
    from app.models.user import Role
    from app.services.auth_service import create_user
    from app.services.auth_service import get_user_by_username

    username = os.environ.get("ADMIN_USERNAME", "admin")
    email = os.environ.get("ADMIN_EMAIL", "admin@fuellhorn.local")
    password = os.environ.get("ADMIN_PASSWORD")

    if not password:
        raise ValueError("ADMIN_PASSWORD environment variable is required")

    # Check if admin already exists
    existing = get_user_by_username(session, username)
    if existing and reset_existing:
        existing.role = Role.ADMIN.value
        existing.is_active = True
        existing.set_password(password)
        session.add(existing)
        session.commit()
        print(f"Admin user reset (role admin, active, new password): {existing.username}")
        return True
    if existing:
        print(f"Admin user already exists: {existing.username}")
        print("Recovery (Passwort, Rolle, Aktiv-Status zurücksetzen): fuellhorn create-admin --reset-password")
        return False

    # Create admin user
    admin = create_user(
        session=session,
        username=username,
        email=email,
        password=password,
        role=Role.ADMIN,
    )

    print(f"Created admin user: {admin.username}")
    print(f"Email: {admin.email}")
    return True


def cli_migrate() -> int:
    """CLI command to run database migrations only.

    Returns:
        0 on success
    """
    print("Running database migrations...")
    run_migrations()
    print("Migrations completed successfully.")
    return 0


def cli_create_admin(options: list[str] | None = None) -> int:
    """CLI command to create admin user.

    Args:
        options: weitere Argumente, z.B. ``--reset-password`` (Recovery, Issue #380)

    Returns:
        0 on success, 1 on error
    """
    from app.database import get_session

    reset_existing = "--reset-password" in (options or [])

    with next(get_session()) as session:
        try:
            created = create_admin_user(session, reset_existing=reset_existing)
            if created:
                print("\nAdmin user created successfully.")
            else:
                print("\nNo changes made.")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1


TESTDATA_DEV_FLAG = "--i-know-this-is-dev"


def cli_seed(subcommand: str | None, options: list[str] | None = None) -> int:
    """CLI command to seed database with default data.

    Args:
        subcommand: 'shelf-life-defaults' or 'testdata'
        options: weitere Argumente, z.B. ``--i-know-this-is-dev``

    Returns:
        0 on success, 1 on error
    """
    from app.config import config
    from app.database import get_engine
    from app.seed import seed_shelf_life_defaults
    from app.seed import seed_testdata

    options = options or []

    if not subcommand:
        print("Usage: fuellhorn seed <subcommand>")
        print("Available subcommands:")
        print("  shelf-life-defaults  Seed categories with shelf life data")
        print(f"  testdata             Seed test data (admin/admin, only with DEBUG=true or {TESTDATA_DEV_FLAG})")
        return 1

    if subcommand not in {"shelf-life-defaults", "testdata"}:
        print(f"Unknown subcommand: {subcommand}")
        print("Available: shelf-life-defaults, testdata")
        return 1

    # Testdaten enthalten den Admin admin/admin: nie unbemerkt in Produktion (#376)
    if subcommand == "testdata" and not (config.DEBUG or TESTDATA_DEV_FLAG in options):
        print("Testdaten (Admin admin/admin) sind nur für die Entwicklung gedacht.")
        print(f"Erlauben mit DEBUG=true oder: fuellhorn seed testdata {TESTDATA_DEV_FLAG}")
        return 1

    # Schema über Alembic anlegen/aktualisieren statt create_all: sonst fehlt
    # alembic_version und ein späteres 'alembic upgrade head' scheitert (#376)
    run_migrations()

    with Session(get_engine()) as session:
        if subcommand == "shelf-life-defaults":
            print("Seeding shelf life defaults...")
            categories, shelf_lives = seed_shelf_life_defaults(session)
            print(f"  Categories: {categories}")
            print(f"  Shelf lives: {shelf_lives}")
            print("Done.")
            return 0

        elif subcommand == "testdata":
            print("Seeding test data...")
            result = seed_testdata(session)
            if result["admin"]:
                print("  Admin created (admin/admin)")
            else:
                print("  Admin already exists")
            print(f"  Categories: {result['categories']}")
            print(f"  Locations: {result['locations']}")
            print(f"  Items: {result['items']}")
            print("Done.")
            return 0

    return 1  # pragma: no cover - alle Subcommands sind oben behandelt


def run_app() -> None:
    """Run the fuellhorn application."""
    import app.api.health  # noqa: F401
    from app.config import config
    from app.config import get_storage_secret
    from app.startup import configure_app
    from app.startup import run_kwargs
    import app.ui.pages  # noqa: F401
    from nicegui import app as nicegui_app
    from nicegui import ui

    if config.SKIP_MIGRATIONS:
        print("Migrationen übersprungen (FUELLHORN_SKIP_MIGRATIONS=true).")
    else:
        run_migrations()

    # Static-Dateien, PWA-Routen und Seitenkopf: dieselbe Funktion wie main.py (#375)
    configure_app(nicegui_app)

    ui.run(
        storage_secret=get_storage_secret(),
        reload=False,
        **run_kwargs(),
    )


def dispatch_command(args: list[str]) -> int:
    """Dispatch CLI command based on arguments.

    Args:
        args: Command line arguments (without program name)

    Returns:
        Exit code (0 for success)
    """
    if not args:
        run_app()
        return 0

    command = args[0]

    if command == "migrate":
        return cli_migrate()
    elif command == "create-admin":
        return cli_create_admin(args[1:])
    elif command == "seed":
        subcommand = args[1] if len(args) > 1 else None
        return cli_seed(subcommand, args[2:])
    else:
        print(f"Unknown command: {command}")
        print("Available commands: migrate, create-admin, seed")
        print("Run without arguments to start the application.")
        return 1


def main() -> None:
    """Main entry point."""
    exit_code = dispatch_command(sys.argv[1:])
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
