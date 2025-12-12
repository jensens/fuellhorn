"""Demo page for Swipe Card component.

This page allows interactive testing of the swipe card component in the browser.
Route: /demo/swipe (only visible in development)

Features:
- Demo card with example content
- Event log with timestamps
- Last event display
- Instructions for testing
"""

from ..components.swipe_card import create_swipe_card
from ..theme import add_theme_css
from datetime import datetime
from nicegui import ui


def _format_time() -> str:
    """Return current time formatted as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


@ui.page("/demo/swipe")
def demo_swipe() -> None:
    """Demo page for swipe card component."""
    add_theme_css()

    # Add swipe card JavaScript
    ui.add_head_html('<script src="/static/js/swipe-card.js"></script>')

    # State for event log
    events: list[str] = []
    last_event_label: ui.label | None = None
    event_log_container: ui.column | None = None

    def add_event(action: str) -> None:
        """Add an event to the log."""
        timestamp = _format_time()
        event_text = f"{timestamp} - {action} triggered"
        events.insert(0, event_text)  # Newest first

        # Update last event display
        if last_event_label:
            last_event_label.set_text(f"Letztes Event: {action}")

        # Update event log
        if event_log_container:
            event_log_container.clear()
            with event_log_container:
                for event in events[:10]:  # Show last 10 events
                    ui.label(event).classes("swipe-demo-event-item")

        # Also show notification
        ui.notify(f"{action} ausgelöst", type="positive", timeout=1500)

    with ui.column().classes("w-full max-w-md mx-auto p-4 gap-4"):
        # Header
        ui.label("Swipe Demo").classes("text-h4 font-bold text-primary")
        ui.label("Interaktive Test-Seite für Swipe-Komponente").classes("text-gray-600")

        ui.separator()

        # Instructions
        with ui.element("div").classes("swipe-demo-instructions"):
            ui.html("<h3>Anleitung</h3>", sanitize=False)
            ui.html(
                """
                <ul>
                    <li><strong>Swipe links</strong> → Teil (500ms) oder Alles</li>
                    <li><strong>Swipe rechts</strong> → Edit</li>
                    <li><strong>Durchswipen</strong> für Edit/Alles</li>
                    <li><strong>Verweilen (500ms)</strong> löst Aktion aus</li>
                </ul>
            """,
                sanitize=False,
            )

        # Demo Card 1
        ui.label("Demo Card 1").classes("text-sm font-semibold text-gray-500 mt-4")

        def card1_content() -> None:
            """Content for demo card 1."""
            with ui.element("div").classes("p-4"):
                ui.label("Beispiel Item").classes("font-bold text-base")
                ui.label("500g • Kühlschrank").classes("text-sm text-gray-600")
                with ui.row().classes("gap-2 mt-2"):
                    ui.badge("Frisch", color="green").props("outline")
                    ui.badge("Milchprodukte", color="primary")

        create_swipe_card(
            content=card1_content,
            on_partial=lambda: add_event("partial_consume (Teil)"),
            on_consume_all=lambda: add_event("consume_all (Alles)"),
            on_edit=lambda: add_event("edit"),
            card_id="demo-card-1",
        )

        # Demo Card 2 (to test "only one card open")
        ui.label("Demo Card 2").classes("text-sm font-semibold text-gray-500 mt-4")

        def card2_content() -> None:
            """Content for demo card 2."""
            with ui.element("div").classes("p-4"):
                ui.label("Zweites Item").classes("font-bold text-base")
                ui.label("3 Stück • Gefriertruhe").classes("text-sm text-gray-600")
                with ui.row().classes("gap-2 mt-2"):
                    ui.badge("TK", color="blue").props("outline")
                    ui.badge("Fleisch", color="red")

        create_swipe_card(
            content=card2_content,
            on_partial=lambda: add_event("partial_consume (Teil) - Card 2"),
            on_consume_all=lambda: add_event("consume_all (Alles) - Card 2"),
            on_edit=lambda: add_event("edit - Card 2"),
            card_id="demo-card-2",
        )

        # Last Event Display
        with (
            ui.element("div")
            .classes("swipe-demo-last-event")
            .bind_visibility_from(globals(), "events", backward=lambda e: len(e) > 0)
        ):
            last_event_label = ui.label("Letztes Event: -")

        # Actually, let's use a simpler approach for visibility
        last_event_label = ui.label("Warte auf Aktion...").classes("swipe-demo-last-event")

        # Event Log
        with ui.element("div").classes("swipe-demo-event-log"):
            ui.html("<h4>Event-Log</h4>", sanitize=False)
            event_log_container = ui.column().classes("gap-0")
            with event_log_container:
                ui.label("Noch keine Events...").classes("swipe-demo-event-item text-gray-400")

        ui.separator()

        # Technical Info
        with ui.expansion("Technische Details", icon="info").classes("w-full"):
            ui.markdown("""
**Interaktions-Matrix:**

| Aktion | Einrasten + 500ms | Durchswipen |
|--------|:-----------------:|:-----------:|
| Teil (links 1) | ✓ | ✗ |
| Alles (links 2) | ✓ | ✓ |
| Edit (rechts) | ✓ | ✓ |

**Swipe-Distanzen (prozentual):**
- Teil: 25% der Kartenbreite
- Alles: 50% der Kartenbreite
- Edit: 25% der Kartenbreite
            """)

        # Back link
        ui.link("← Zurück zum Dashboard", "/").classes("text-primary mt-4")
