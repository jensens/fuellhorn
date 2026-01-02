"""CLI entry point for fuellhorn."""

import os
from pathlib import Path


def run_migrations() -> None:
    """Run alembic migrations from installed package."""
    from alembic import command
    from alembic.config import Config
    import app.alembic

    alembic_dir = Path(app.alembic.__file__).parent

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(alembic_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL", ""))

    command.upgrade(alembic_cfg, "head")


def main() -> None:
    """Main entry point."""
    import app.api.health  # noqa: F401
    from app.config import get_storage_secret
    import app.ui.pages  # noqa: F401
    from nicegui import app as nicegui_app
    from nicegui import ui

    run_migrations()

    # Serve static files (CSS, icons, etc.)
    nicegui_app.add_static_files("/static", "app/static")

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


if __name__ == "__main__":
    main()
