"""E2E Tests for Item Card Swipe functionality with Playwright.

These tests verify the swipe integration in Item Cards:
- Swipe left reveals Teil + Alles buttons
- Swipe right reveals Edit button
- Callbacks are triggered correctly
- Existing click/quick-action functionality preserved
"""

from playwright.sync_api import Page
from playwright.sync_api import expect
import pytest
import time


# Dwell-time triggers don't fire reliably in automated tests
# See: https://github.com/jensens/fuellhorn/issues/231
XFAIL_DWELL_TIME = pytest.mark.xfail(
    reason="Dwell-time triggers unreliable in Playwright (Issue #231)",
    strict=False,
)


def _swipe_element(
    page: Page,
    selector: str,
    delta_x: int,
    hold_ms: int = 0,
) -> None:
    """Perform a swipe gesture on an element using mouse events."""
    element = page.locator(selector)
    box = element.bounding_box()
    if not box:
        raise ValueError(f"Element not found: {selector}")

    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2

    page.mouse.move(center_x, center_y)
    page.mouse.down()
    page.mouse.move(center_x + delta_x, center_y, steps=10)

    if hold_ms > 0:
        time.sleep(hold_ms / 1000)

    page.mouse.up()


def _swipe_through(page: Page, selector: str, direction: str) -> None:
    """Perform a quick swipe-through gesture."""
    element = page.locator(selector)
    box = element.bounding_box()
    if not box:
        raise ValueError(f"Element not found: {selector}")

    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2

    delta = -box["width"] * 0.7 if direction == "left" else box["width"] * 0.4
    page.mouse.move(center_x, center_y)
    page.mouse.down()
    page.mouse.move(center_x + delta, center_y, steps=5)
    page.mouse.up()


class TestItemCardSwipe:
    """E2E Tests for Item Card Swipe integration."""

    def test_item_card_swipe_page_renders(self, page: Page, live_server: str) -> None:
        """Test: Item card swipe test page renders correctly."""
        page.goto(f"{live_server}/test-item-card-swipe")
        expect(page.get_by_text("Erbsen")).to_be_visible()
        expect(page.get_by_text("500 g")).to_be_visible()
        expect(page.locator(".swipe-card-container")).to_be_visible()

    def test_item_card_swipe_left_reveals_buttons(self, page: Page, live_server: str) -> None:
        """Test: Swiping left on item card reveals Teil and Alles buttons."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        card = page.locator(".swipe-card-content").first
        box = card.bounding_box()
        if box:
            _swipe_element(page, ".swipe-card-content", int(-box["width"] * 0.3))
        page.wait_for_timeout(100)
        expect(page.locator(".swipe-action-teil")).to_be_visible()

    def test_item_card_swipe_right_reveals_edit(self, page: Page, live_server: str) -> None:
        """Test: Swiping right on item card reveals Edit button."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        card = page.locator(".swipe-card-content").first
        box = card.bounding_box()
        if box:
            _swipe_element(page, ".swipe-card-content", int(box["width"] * 0.3))
        page.wait_for_timeout(100)
        expect(page.locator(".swipe-action-edit")).to_be_visible()

    @XFAIL_DWELL_TIME
    def test_item_card_swipe_partial_callback(self, page: Page, live_server: str) -> None:
        """Test: Swipe left + dwell triggers partial consume callback."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        card = page.locator(".swipe-card-content").first
        box = card.bounding_box()
        if box:
            _swipe_element(page, ".swipe-card-content", int(-box["width"] * 0.25), 600)
        page.wait_for_timeout(200)
        expect(page.get_by_text("partial_consume")).to_be_visible(timeout=2000)

    @XFAIL_DWELL_TIME
    def test_item_card_swipe_all_callback(self, page: Page, live_server: str) -> None:
        """Test: Swipe left full + dwell triggers consume all callback."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        card = page.locator(".swipe-card-content").first
        box = card.bounding_box()
        if box:
            _swipe_element(page, ".swipe-card-content", int(-box["width"] * 0.5), 600)
        page.wait_for_timeout(200)
        expect(page.get_by_text("consume_all")).to_be_visible(timeout=2000)

    @XFAIL_DWELL_TIME
    def test_item_card_swipe_through_triggers_all(self, page: Page, live_server: str) -> None:
        """Test: Swipe through left triggers consume all callback."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        _swipe_through(page, ".swipe-card-content", "left")
        page.wait_for_timeout(200)
        expect(page.get_by_text("consume_all")).to_be_visible(timeout=2000)

    def test_item_card_swipe_edit_callback(self, page: Page, live_server: str) -> None:
        """Test: Swipe right + dwell triggers edit callback."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        card = page.locator(".swipe-card-content").first
        box = card.bounding_box()
        if box:
            _swipe_element(page, ".swipe-card-content", int(box["width"] * 0.25), 600)
        page.wait_for_timeout(200)
        expect(page.get_by_text("edit", exact=True)).to_be_visible(timeout=2000)

    def test_item_card_swipe_through_right_triggers_edit(self, page: Page, live_server: str) -> None:
        """Test: Swipe through right triggers edit callback."""
        page.goto(f"{live_server}/test-item-card-swipe")
        page.wait_for_timeout(500)
        _swipe_through(page, ".swipe-card-content", "right")
        page.wait_for_timeout(200)
        expect(page.get_by_text("edit", exact=True)).to_be_visible(timeout=2000)

    def test_item_card_quick_action_preserved(self, page: Page, live_server: str) -> None:
        """Test: Quick-action button functionality is preserved."""
        page.goto(f"{live_server}/test-item-card-swipe-with-consume")
        page.wait_for_timeout(500)
        button = page.locator(".sp-quick-action").first
        expect(button).to_be_visible()
        button.click()
        page.wait_for_timeout(200)
        expect(page.get_by_text("quick_consume")).to_be_visible(timeout=2000)
