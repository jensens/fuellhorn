"""Swipe Card Component - Touch/Mouse swipe-to-reveal actions.

Provides a reusable swipe card with bidirectional actions:
- Swipe left: Teil (partial) + Alles (consume all)
- Swipe right: Edit

Features:
- 500ms dwell-time trigger with radial progress ring
- Swipe-through trigger for Alles/Edit (not Teil)
- Only one card open at a time
- Touch + Mouse support
"""

from nicegui import ui
from typing import Any
from typing import Callable
import uuid


# SVG icons for action buttons
ICON_TEIL = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 8v8M8 12h8"/>
</svg>"""

ICON_ALLES = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M20 6L9 17l-5-5"/>
</svg>"""

ICON_EDIT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
</svg>"""


def create_swipe_card(
    content: Callable[[], None],
    on_partial: Callable[[], None] | None = None,
    on_consume_all: Callable[[], None] | None = None,
    on_edit: Callable[[], None] | None = None,
    card_id: str | None = None,
    teil_label: str = "Teil",
    alles_label: str = "Alles",
    edit_label: str = "Edit",
) -> ui.element:
    """Create a swipe card with bidirectional actions.

    Args:
        content: Callable that creates the card content (called within slot)
        on_partial: Callback when "Teil" (partial consume) action is triggered
        on_consume_all: Callback when "Alles" (consume all) action is triggered
        on_edit: Callback when "Edit" action is triggered
        card_id: Optional unique ID for the card (auto-generated if not provided)
        teil_label: Label for the partial action button
        alles_label: Label for the consume all action button
        edit_label: Label for the edit action button

    Returns:
        The container element for the swipe card

    Example:
        def my_content():
            ui.label("Item Name").classes("font-bold")
            ui.label("Details...")

        create_swipe_card(
            content=my_content,
            on_partial=lambda: print("Teil"),
            on_consume_all=lambda: print("Alles"),
            on_edit=lambda: print("Edit"),
        )
    """
    # Generate unique ID if not provided
    unique_id = card_id or f"swipe-card-{uuid.uuid4().hex[:8]}"

    # Create container with swipe structure
    container = ui.element("div").classes("swipe-card-container")
    container._props["id"] = unique_id

    with container:
        # Left actions (behind content, revealed on left swipe)
        # Order: Alles first (left, revealed at 50%), Teil second (right, revealed at 25%)
        with ui.element("div").classes("swipe-card-actions-left"):
            # Alles button (left side, revealed when swiping further)
            with ui.element("button").classes("swipe-action-btn swipe-action-alles").props('data-action="alles"'):
                ui.html(ICON_ALLES, sanitize=False)
                ui.label(alles_label)

            # Teil button (right side, revealed first when starting to swipe)
            with ui.element("button").classes("swipe-action-btn swipe-action-teil").props('data-action="teil"'):
                ui.html(ICON_TEIL, sanitize=False)
                ui.label(teil_label)

        # Right action (behind content, revealed on right swipe)
        with ui.element("div").classes("swipe-card-actions-right"):
            with ui.element("button").classes("swipe-action-btn swipe-action-edit").props('data-action="edit"'):
                ui.html(ICON_EDIT, sanitize=False)
                ui.label(edit_label)

        # Slideable content layer
        with ui.element("div").classes("swipe-card-content"):
            content()

    # Register callbacks in JavaScript
    callback_js = f"""
        window.swipeCardCallbacks = window.swipeCardCallbacks || {{}};
        window.swipeCardCallbacks['{unique_id}'] = function(action) {{
            if (action === 'teil') {{
                emitEvent('{unique_id}', 'partial');
            }} else if (action === 'alles') {{
                emitEvent('{unique_id}', 'consume_all');
            }} else if (action === 'edit') {{
                emitEvent('{unique_id}', 'edit');
            }}
        }};
    """

    # Initialize swipe functionality after DOM is ready
    init_js = f"""
        setTimeout(function() {{
            if (window.SwipeCard) {{
                window.SwipeCard.init('{unique_id}');
            }}
        }}, 100);
    """

    ui.run_javascript(callback_js)
    ui.run_javascript(init_js)

    # Set up event handlers using NiceGUI's event system
    def handle_swipe_event(e: Any) -> None:
        """Handle swipe events from JavaScript."""
        action = e.args.get("action") if hasattr(e, "args") else None
        if action == "partial" and on_partial:
            on_partial()
        elif action == "consume_all" and on_consume_all:
            on_consume_all()
        elif action == "edit" and on_edit:
            on_edit()

    # Listen for custom events from JavaScript
    # We use a hidden element to receive events
    event_receiver = ui.element("div").style("display: none;")
    event_receiver._props["id"] = f"{unique_id}-receiver"

    # JavaScript function to emit events to NiceGUI
    emit_js = f"""
        function emitEvent(cardId, action) {{
            const event = new CustomEvent('swipe-action-' + cardId, {{
                detail: {{ action: action }},
                bubbles: true
            }});
            document.dispatchEvent(event);
        }}

        document.addEventListener('swipe-action-{unique_id}', function(e) {{
            const action = e.detail.action;
            // Call NiceGUI callback via fetch
            fetch('/_nicegui/api/swipe/' + encodeURIComponent('{unique_id}') + '/' + action, {{
                method: 'POST'
            }}).catch(function() {{}});
        }});
    """
    ui.run_javascript(emit_js)

    # Alternative: Use element's on() method for events
    # This approach uses a more direct callback mechanism
    container.on(
        "swipeaction",
        lambda e: _dispatch_action(e, on_partial, on_consume_all, on_edit),
    )

    return container


def _dispatch_action(
    event: Any,
    on_partial: Callable[[], None] | None,
    on_consume_all: Callable[[], None] | None,
    on_edit: Callable[[], None] | None,
) -> None:
    """Dispatch swipe action to appropriate callback."""
    try:
        detail = event.args.get("detail", {})
        action = detail.get("action")
    except (AttributeError, TypeError):
        return

    if action == "teil" and on_partial:
        on_partial()
    elif action == "alles" and on_consume_all:
        on_consume_all()
    elif action == "edit" and on_edit:
        on_edit()


def reset_swipe_card(card_id: str) -> None:
    """Reset a swipe card to its initial position.

    Args:
        card_id: The ID of the card to reset
    """
    ui.run_javascript(f"window.SwipeCard && window.SwipeCard.reset('{card_id}');")


def reset_all_swipe_cards() -> None:
    """Reset all swipe cards to their initial positions."""
    ui.run_javascript("window.SwipeCard && window.SwipeCard.resetAll();")
