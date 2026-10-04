"""Login Page and Index Redirect."""

from ..auth import show_login_page
from nicegui import app
from nicegui import ui


@ui.page("/")
def index() -> None:
    """Root - Redirect zu Login oder Dashboard."""
    if app.storage.user.get("authenticated"):
        ui.navigate.to("/dashboard")
    else:
        ui.navigate.to("/login")


@ui.page("/login")
def login(next: str = "/dashboard") -> None:
    """Login-Seite; ``next`` ist die Seite, die den Login verlangt hat (nur relative Pfade)."""
    show_login_page(next_url=next)
