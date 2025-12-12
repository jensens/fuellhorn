/**
 * Swipe Card Component
 *
 * Custom swipe-to-reveal actions for touch and mouse.
 * Features:
 * - Bidirectional swipe (left: Teil/Alles, right: Edit)
 * - 300ms dwell-time trigger with radial progress ring
 * - Swipe-through trigger for Alles/Edit
 * - Only one card open at a time
 */

(function () {
  'use strict';

  // Global state: track currently open card
  let currentlyOpenCard = null;

  // Default options
  const DEFAULT_OPTIONS = {
    leftAction1Threshold: 0.25, // Teil position (25%)
    leftAction2Threshold: 0.50, // Alles position (50%)
    rightActionThreshold: 0.25, // Edit position (25%)
    dwellTime: 300, // ms
    swipeThroughMultiplier: 1.2, // 120% of threshold = swipe-through
  };

  /**
   * Initialize a swipe card element.
   * @param {string} cardId - The ID of the card container element
   * @param {object} options - Configuration options
   */
  function initSwipeCard(cardId, options = {}) {
    const container = document.getElementById(cardId);
    if (!container) {
      console.error(`SwipeCard: Element with id "${cardId}" not found`);
      return;
    }

    const content = container.querySelector('.swipe-card-content');
    if (!content) {
      console.error(`SwipeCard: Content element not found in "${cardId}"`);
      return;
    }

    const config = { ...DEFAULT_OPTIONS, ...options };
    const state = {
      isDragging: false,
      startX: 0,
      currentX: 0,
      translateX: 0,
      cardWidth: 0,
      dwellTimer: null,
      dwellStartTime: null,
      activeAction: null,
      progressRing: null,
    };

    // Calculate thresholds in pixels based on card width
    function getThresholds() {
      state.cardWidth = container.offsetWidth;
      return {
        leftAction1: state.cardWidth * config.leftAction1Threshold,
        leftAction2: state.cardWidth * config.leftAction2Threshold,
        rightAction: state.cardWidth * config.rightActionThreshold,
        leftSwipeThrough: state.cardWidth * config.leftAction2Threshold * config.swipeThroughMultiplier,
        rightSwipeThrough: state.cardWidth * config.rightActionThreshold * config.swipeThroughMultiplier,
      };
    }

    // Close other open cards
    function closeOtherCards() {
      if (currentlyOpenCard && currentlyOpenCard !== cardId) {
        const otherCard = document.getElementById(currentlyOpenCard);
        if (otherCard) {
          const otherContent = otherCard.querySelector('.swipe-card-content');
          if (otherContent) {
            otherContent.style.transition = 'transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            otherContent.style.transform = 'translateX(0)';
            otherCard.classList.remove('swiped-left', 'swiped-right', 'swiped-left-full');
          }
        }
        currentlyOpenCard = null;
      }
    }

    // Reset card to initial position
    function resetCard() {
      content.style.transition = 'transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      content.style.transform = 'translateX(0)';
      state.translateX = 0;
      container.classList.remove('swiped-left', 'swiped-right', 'swiped-left-full');
      clearDwellTimer();
      if (currentlyOpenCard === cardId) {
        currentlyOpenCard = null;
      }
    }

    // Clear dwell timer and hide progress ring
    function clearDwellTimer() {
      if (state.dwellTimer) {
        clearTimeout(state.dwellTimer);
        state.dwellTimer = null;
      }
      state.dwellStartTime = null;
      state.activeAction = null;
      hideProgressRing();
    }

    // Show radial progress ring on action button
    function showProgressRing(action) {
      const actionBtn = container.querySelector(`.swipe-action-${action}`);
      if (!actionBtn) return;

      // Create progress ring if not exists
      let ring = actionBtn.querySelector('.dwell-progress-ring');
      if (!ring) {
        ring = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        ring.setAttribute('class', 'dwell-progress-ring');
        ring.setAttribute('viewBox', '0 0 36 36');
        ring.innerHTML = `
          <circle class="ring-bg" cx="18" cy="18" r="16" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="3"/>
          <circle class="ring-progress" cx="18" cy="18" r="16" fill="none" stroke="white" stroke-width="3"
                  stroke-dasharray="100.53" stroke-dashoffset="100.53" stroke-linecap="round"
                  transform="rotate(-90 18 18)"/>
        `;
        actionBtn.appendChild(ring);
      }

      state.progressRing = ring;
      ring.classList.add('active');

      // Animate the progress
      const progressCircle = ring.querySelector('.ring-progress');
      if (progressCircle) {
        progressCircle.style.transition = `stroke-dashoffset ${config.dwellTime}ms linear`;
        // Trigger reflow to restart animation
        progressCircle.style.strokeDashoffset = '100.53';
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            progressCircle.style.strokeDashoffset = '0';
          });
        });
      }
    }

    // Hide progress ring
    function hideProgressRing() {
      if (state.progressRing) {
        state.progressRing.classList.remove('active');
        const progressCircle = state.progressRing.querySelector('.ring-progress');
        if (progressCircle) {
          progressCircle.style.transition = 'none';
          progressCircle.style.strokeDashoffset = '100.53';
        }
        state.progressRing = null;
      }
      // Also hide any other active rings
      container.querySelectorAll('.dwell-progress-ring.active').forEach(ring => {
        ring.classList.remove('active');
      });
    }

    // Start dwell timer for action
    function startDwellTimer(action) {
      clearDwellTimer();
      state.activeAction = action;
      state.dwellStartTime = Date.now();
      showProgressRing(action);

      state.dwellTimer = setTimeout(() => {
        // Dwell time completed - trigger action
        triggerAction(action);
        resetCard();
      }, config.dwellTime);
    }

    // Trigger action callback
    function triggerAction(action) {
      // Dispatch custom event for NiceGUI to catch
      const event = new CustomEvent('swipeaction', {
        detail: { action, cardId },
        bubbles: true,
      });
      container.dispatchEvent(event);

      // Also call global callback if defined
      if (window.swipeCardCallbacks && window.swipeCardCallbacks[cardId]) {
        window.swipeCardCallbacks[cardId](action);
      }
    }

    // Determine which action zone the card is in
    function getActionZone(translateX) {
      const thresholds = getThresholds();

      if (translateX < -thresholds.leftAction2 * 0.75) {
        return 'alles';
      } else if (translateX < -thresholds.leftAction1 * 0.75) {
        return 'teil';
      } else if (translateX > thresholds.rightAction * 0.75) {
        return 'edit';
      }
      return null;
    }

    // Handle drag start
    function onDragStart(e) {
      closeOtherCards();
      state.isDragging = true;
      state.startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
      state.currentX = state.startX;
      content.style.transition = 'none';
      clearDwellTimer();
    }

    // Handle drag move
    function onDragMove(e) {
      if (!state.isDragging) return;

      const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
      const diff = clientX - state.startX;
      state.currentX = clientX;

      const thresholds = getThresholds();

      // Limit drag range
      const maxLeft = -thresholds.leftAction2 * 1.1;
      const maxRight = thresholds.rightAction * 1.1;
      state.translateX = Math.max(maxLeft, Math.min(maxRight, diff));

      content.style.transform = `translateX(${state.translateX}px)`;

      // Update container classes for styling
      container.classList.remove('swiped-left', 'swiped-right', 'swiped-left-full');
      if (state.translateX < -thresholds.leftAction1 * 0.5) {
        container.classList.add('swiped-left');
        if (state.translateX < -thresholds.leftAction2 * 0.75) {
          container.classList.add('swiped-left-full');
        }
      } else if (state.translateX > thresholds.rightAction * 0.5) {
        container.classList.add('swiped-right');
      }

      // Check for dwell zone change
      const currentZone = getActionZone(state.translateX);
      if (currentZone !== state.activeAction) {
        clearDwellTimer();
        if (currentZone) {
          startDwellTimer(currentZone);
        }
      }
    }

    // Handle drag end
    function onDragEnd(e) {
      if (!state.isDragging) return;
      state.isDragging = false;
      clearDwellTimer();

      const thresholds = getThresholds();
      content.style.transition = 'transform 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';

      // Check for swipe-through (quick swipe past threshold)
      const swipeDistance = state.translateX;
      const swipeVelocity = state.currentX - state.startX;

      // Swipe-through left triggers "alles" (not "teil")
      if (swipeDistance < -thresholds.leftSwipeThrough ||
          (swipeDistance < -thresholds.leftAction2 && Math.abs(swipeVelocity) > 50)) {
        triggerAction('alles');
        resetCard();
        return;
      }

      // Swipe-through right triggers "edit"
      if (swipeDistance > thresholds.rightSwipeThrough ||
          (swipeDistance > thresholds.rightAction && swipeVelocity > 50)) {
        triggerAction('edit');
        resetCard();
        return;
      }

      // Snap to position or reset
      if (swipeDistance < -thresholds.leftAction2 * 0.6) {
        // Snap to full left (Alles position)
        content.style.transform = `translateX(${-thresholds.leftAction2}px)`;
        state.translateX = -thresholds.leftAction2;
        container.classList.add('swiped-left', 'swiped-left-full');
        currentlyOpenCard = cardId;
        startDwellTimer('alles');
      } else if (swipeDistance < -thresholds.leftAction1 * 0.6) {
        // Snap to partial left (Teil position)
        content.style.transform = `translateX(${-thresholds.leftAction1}px)`;
        state.translateX = -thresholds.leftAction1;
        container.classList.add('swiped-left');
        currentlyOpenCard = cardId;
        startDwellTimer('teil');
      } else if (swipeDistance > thresholds.rightAction * 0.6) {
        // Snap to right (Edit position)
        content.style.transform = `translateX(${thresholds.rightAction}px)`;
        state.translateX = thresholds.rightAction;
        container.classList.add('swiped-right');
        currentlyOpenCard = cardId;
        startDwellTimer('edit');
      } else {
        // Reset to center
        resetCard();
      }
    }

    // Bind event listeners
    content.addEventListener('mousedown', onDragStart);
    content.addEventListener('touchstart', onDragStart, { passive: true });

    document.addEventListener('mousemove', onDragMove);
    document.addEventListener('touchmove', onDragMove, { passive: true });

    document.addEventListener('mouseup', onDragEnd);
    document.addEventListener('touchend', onDragEnd);

    // Click outside to close
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target) && currentlyOpenCard === cardId) {
        resetCard();
      }
    });

    // Action button clicks (for accessibility / non-swipe interaction)
    container.querySelectorAll('.swipe-action-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const action = btn.dataset.action;
        if (action) {
          triggerAction(action);
          resetCard();
        }
      });
    });

    // Store reference for cleanup
    container._swipeCard = {
      reset: resetCard,
      state,
    };

    return container._swipeCard;
  }

  /**
   * Reset a swipe card to its initial position.
   * @param {string} cardId - The ID of the card container element
   */
  function resetSwipeCard(cardId) {
    const container = document.getElementById(cardId);
    if (container && container._swipeCard) {
      container._swipeCard.reset();
    }
  }

  /**
   * Reset all swipe cards.
   */
  function resetAllSwipeCards() {
    document.querySelectorAll('.swipe-card-container').forEach(container => {
      if (container._swipeCard) {
        container._swipeCard.reset();
      }
    });
    currentlyOpenCard = null;
  }

  // Export to global scope
  window.SwipeCard = {
    init: initSwipeCard,
    reset: resetSwipeCard,
    resetAll: resetAllSwipeCards,
  };

  // Initialize callback storage
  window.swipeCardCallbacks = window.swipeCardCallbacks || {};

})();
