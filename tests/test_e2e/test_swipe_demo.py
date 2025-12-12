"""E2E Tests für die Swipe-Demo-Seite mit Playwright.

Diese Tests prüfen die Swipe-Komponente im echten Browser:
- Demo-Seite rendert korrekt
- Swipe-Interaktionen (links/rechts)
- 500ms Dwell-Time Trigger
- Durchswipen-Trigger
- Nur eine Card gleichzeitig offen
"""

from playwright.sync_api import Page
from playwright.sync_api import expect
import time


def _swipe_element(
    page: Page,
    selector: str,
    delta_x: int,
    hold_ms: int = 0,
) -> None:
    """Perform a swipe gesture on an element using mouse events.

    Args:
        page: Playwright page object
        selector: CSS selector for the element to swipe
        delta_x: Horizontal distance to swipe (negative = left, positive = right)
        hold_ms: Time to hold at the end position (for dwell trigger)
    """
    element = page.locator(selector)
    box = element.bounding_box()
    if not box:
        raise ValueError(f"Element not found: {selector}")

    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2

    # Perform swipe with mouse
    page.mouse.move(center_x, center_y)
    page.mouse.down()
    page.mouse.move(center_x + delta_x, center_y, steps=10)

    if hold_ms > 0:
        time.sleep(hold_ms / 1000)

    page.mouse.up()


def _swipe_through(page: Page, selector: str, direction: str) -> None:
    """Perform a quick swipe-through gesture.

    Args:
        page: Playwright page object
        selector: CSS selector for the element
        direction: 'left' or 'right'
    """
    element = page.locator(selector)
    box = element.bounding_box()
    if not box:
        raise ValueError(f"Element not found: {selector}")

    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2

    # Quick swipe through
    delta = -box["width"] * 0.7 if direction == "left" else box["width"] * 0.4
    page.mouse.move(center_x, center_y)
    page.mouse.down()
    page.mouse.move(center_x + delta, center_y, steps=5)
    page.mouse.up()


class TestSwipeDemo:
    """E2E Tests für Swipe-Komponente."""

    def test_demo_page_renders(self, page: Page, live_server: str) -> None:
        """Test: Demo-Seite rendert alle UI-Elemente korrekt."""
        page.goto(f"{live_server}/demo/swipe")

        # Titel prüfen
        expect(page.get_by_text("Swipe Demo")).to_be_visible()
        expect(page.get_by_text("Interaktive Test-Seite")).to_be_visible()

        # Anleitung prüfen
        expect(page.get_by_text("Anleitung")).to_be_visible()
        expect(page.get_by_text("Swipe links")).to_be_visible()

        # Demo Cards prüfen
        expect(page.locator("#demo-card-1")).to_be_visible()
        expect(page.locator("#demo-card-2")).to_be_visible()

        # Event-Log prüfen
        expect(page.get_by_text("Event-Log")).to_be_visible()

    def test_swipe_left_partial_with_dwell(self, page: Page, live_server: str) -> None:
        """Test: Swipe links + 500ms Verweilen löst Teil aus."""
        page.goto(f"{live_server}/demo/swipe")

        # Wait for JS to initialize
        page.wait_for_timeout(500)

        # Swipe left to Teil position (25%) and hold
        card = page.locator("#demo-card-1 .swipe-card-content")
        box = card.bounding_box()
        if box:
            delta_x = -box["width"] * 0.25
            _swipe_element(page, "#demo-card-1 .swipe-card-content", int(delta_x), 600)

        # Check that partial action was triggered (notification or event log)
        page.wait_for_timeout(200)
        # Look for "Teil" in the last event or notification
        expect(page.get_by_text("partial_consume").or_(page.get_by_text("Teil"))).to_be_visible(timeout=2000)

    def test_swipe_left_full_with_dwell(self, page: Page, live_server: str) -> None:
        """Test: Swipe links komplett + 500ms Verweilen löst Alles aus."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        # Swipe left to Alles position (50%) and hold
        card = page.locator("#demo-card-1 .swipe-card-content")
        box = card.bounding_box()
        if box:
            delta_x = -box["width"] * 0.5
            _swipe_element(page, "#demo-card-1 .swipe-card-content", int(delta_x), 600)

        page.wait_for_timeout(200)
        expect(page.get_by_text("consume_all").or_(page.get_by_text("Alles"))).to_be_visible(timeout=2000)

    def test_swipe_left_through_triggers_all(self, page: Page, live_server: str) -> None:
        """Test: Durchswipen nach links löst Alles aus."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        # Quick swipe through to the left
        _swipe_through(page, "#demo-card-1 .swipe-card-content", "left")

        page.wait_for_timeout(200)
        expect(page.get_by_text("consume_all").or_(page.get_by_text("Alles"))).to_be_visible(timeout=2000)

    def test_swipe_right_with_dwell(self, page: Page, live_server: str) -> None:
        """Test: Swipe rechts + 500ms Verweilen löst Edit aus."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        # Swipe right to Edit position (25%) and hold
        card = page.locator("#demo-card-1 .swipe-card-content")
        box = card.bounding_box()
        if box:
            delta_x = box["width"] * 0.25
            _swipe_element(page, "#demo-card-1 .swipe-card-content", int(delta_x), 600)

        page.wait_for_timeout(200)
        expect(page.get_by_text("edit")).to_be_visible(timeout=2000)

    def test_swipe_right_through_triggers_edit(self, page: Page, live_server: str) -> None:
        """Test: Durchswipen nach rechts löst Edit aus."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        # Quick swipe through to the right
        _swipe_through(page, "#demo-card-1 .swipe-card-content", "right")

        page.wait_for_timeout(200)
        expect(page.get_by_text("edit")).to_be_visible(timeout=2000)

    def test_swipe_back_cancels(self, page: Page, live_server: str) -> None:
        """Test: Zurückswipen ohne Verweilen bricht ab."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        card = page.locator("#demo-card-1 .swipe-card-content")
        box = card.bounding_box()
        if not box:
            return

        center_x = box["x"] + box["width"] / 2
        center_y = box["y"] + box["height"] / 2

        # Swipe left then back without holding
        page.mouse.move(center_x, center_y)
        page.mouse.down()
        page.mouse.move(center_x - 100, center_y, steps=5)
        page.mouse.move(center_x, center_y, steps=5)  # Swipe back
        page.mouse.up()

        # Card should be back to initial position (no transform)
        page.wait_for_timeout(300)
        transform = card.evaluate("el => getComputedStyle(el).transform")
        # Should be 'none' or 'matrix(1, 0, 0, 1, 0, 0)' (no translation)
        assert transform == "none" or "0, 0)" in transform

    def test_only_one_card_open(self, page: Page, live_server: str) -> None:
        """Test: Nur eine Card kann gleichzeitig offen sein."""
        page.goto(f"{live_server}/demo/swipe")
        page.wait_for_timeout(500)

        # Swipe card 1 left and hold (but don't trigger)
        card1 = page.locator("#demo-card-1 .swipe-card-content")
        box1 = card1.bounding_box()
        if box1:
            center_x = box1["x"] + box1["width"] / 2
            center_y = box1["y"] + box1["height"] / 2
            page.mouse.move(center_x, center_y)
            page.mouse.down()
            page.mouse.move(center_x - 80, center_y, steps=5)
            page.mouse.up()

        page.wait_for_timeout(100)

        # Now swipe card 2 - card 1 should close
        card2 = page.locator("#demo-card-2 .swipe-card-content")
        box2 = card2.bounding_box()
        if box2:
            center_x = box2["x"] + box2["width"] / 2
            center_y = box2["y"] + box2["height"] / 2
            page.mouse.move(center_x, center_y)
            page.mouse.down()
            page.mouse.move(center_x - 80, center_y, steps=5)
            page.mouse.up()

        page.wait_for_timeout(300)

        # Card 1 should be back to initial position
        transform1 = card1.evaluate("el => getComputedStyle(el).transform")
        # Card 1 should not be swiped anymore
        assert transform1 == "none" or "0, 0)" in transform1
