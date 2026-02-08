/**
 * Simple pub/sub EventBus for cross-view communication.
 *
 * Usage:
 *   import { eventBus } from './events.js';
 *   const off = eventBus.on('state:updated', data => { ... });
 *   eventBus.emit('state:updated', { resources: ... });
 *   off(); // unsubscribe
 */

class EventBus {
  constructor() {
    /** @type {Map<string, Set<Function>>} */
    this._handlers = new Map();
  }

  /**
   * Subscribe to an event.
   * @param {string} event
   * @param {Function} handler
   * @returns {Function} unsubscribe function
   */
  on(event, handler) {
    if (!this._handlers.has(event)) {
      this._handlers.set(event, new Set());
    }
    this._handlers.get(event).add(handler);
    return () => this._handlers.get(event)?.delete(handler);
  }

  /**
   * Emit an event to all subscribers.
   * @param {string} event
   * @param {*} data
   */
  emit(event, data) {
    const handlers = this._handlers.get(event);
    if (!handlers) return;
    for (const fn of handlers) {
      try {
        fn(data);
      } catch (err) {
        console.error(`[EventBus] Error in handler for "${event}":`, err);
      }
    }
  }

  /**
   * Remove all handlers for an event, or all handlers if no event given.
   * @param {string} [event]
   */
  clear(event) {
    if (event) {
      this._handlers.delete(event);
    } else {
      this._handlers.clear();
    }
  }
}

export const eventBus = new EventBus();
