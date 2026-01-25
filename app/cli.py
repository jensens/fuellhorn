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


def create_admin_user(session: Session) -> bool:
    """Create initial admin user from environment variables.

    Supports environment variables for Kubernetes init container usage:
    - ADMIN_USERNAME: Admin username (default: "admin")
    - ADMIN_EMAIL: Admin email (default: "admin@fuellhorn.local")
    - ADMIN_PASSWORD: Admin password (required, no default for security)

    Args:
        session: Database session

    Returns:
        True if user was created, False if user already exists

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
    if existing:
        print(f"Admin user already exists: {existing.username}")
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


def cli_create_admin() -> int:
    """CLI command to create admin user.

    Returns:
        0 on success, 1 on error
    """
    from app.database import get_session

    with next(get_session()) as session:
        try:
            created = create_admin_user(session)
            if created:
                print("\nAdmin user created successfully.")
            else:
                print("\nNo changes made.")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1


def run_app() -> None:
    """Run the fuellhorn application."""
    import app.api.health  # noqa: F401
    from app.config import get_storage_secret
    import app.ui.pages  # noqa: F401
    from nicegui import app as nicegui_app
    from nicegui import ui

    run_migrations()

    # Serve static files (CSS, icons, etc.)
    static_dir = Path(__file__).parent / "static"
    nicegui_app.add_static_files("/static", str(static_dir))

    # Load Solarpunk theme CSS and JavaScript for each client connection
    @nicegui_app.on_connect
    def _load_theme() -> None:
        ui.add_head_html('<link rel="stylesheet" href="/static/css/solarpunk-theme.css">')
        ui.add_head_html('<script src="/static/js/swipe-card.js"></script>')

    port = int(os.environ.get("PORT", "8080"))
    ui.run(
        title="Fuellhorn",
        storage_secret=get_storage_secret(),
        port=port,
        reload=False,
        show=False,
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
        return cli_create_admin()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: migrate, create-admin")
        print("Run without arguments to start the application.")
        return 1


def main() -> None:
    """Main entry point."""
    exit_code = dispatch_command(sys.argv[1:])
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
