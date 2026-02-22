/**
 * Client-side state store.
 *
 * Holds the last known empire snapshot and provides
 * reactive updates via the EventBus.
 *
 * Events emitted:
 *   'state:summary'   – after summary data refreshed
 *   'state:items'     – after item catalog refreshed
 *   'state:military'  – after military data refreshed
 *   'state:connected' – WebSocket connected
 *   'state:disconnected' – WebSocket disconnected
 *   'state:auth'      – auth state changed
 */

import { eventBus } from './events.js';

class StateStore {
  constructor() {
    /** @type {{ uid: number|null, username: string|null, authenticated: boolean }} */
    this.auth = {
      uid: null,
      username: null,
      authenticated: false,
    };

    /** @type {object|null} Last summary_response */
    this.summary = null;

    /** @type {object|null} Last item_response */
    this.items = null;

    /** @type {object|null} Last military_response */
    this.military = null;

    /** @type {{ uid: number, name: string }|null} pending attack target set by dashboard */
    this.pendingAttackTarget = null;

    /** @type {{ uid: number, name: string }|null} pending message target set by dashboard */
    this.pendingMessageTarget = null;

    /** @type {{ attack_id: number, attacker_uid: number }|null} incoming attack to watch in battle view */
    this.pendingIncomingAttack = null;

    /** @type {boolean} */
    this.connected = false;
  }

  setAuth(uid, username) {
    this.auth = { uid, username, authenticated: uid !== null };
    eventBus.emit('state:auth', this.auth);
  }

  clearAuth() {
    this.auth = { uid: null, username: null, authenticated: false };
    eventBus.emit('state:auth', this.auth);
  }

  setSummary(data) {
    this.summary = data;
    eventBus.emit('state:summary', data);
  }

  setItems(data) {
    this.items = data;
    eventBus.emit('state:items', data);
  }

  setMilitary(data) {
    this.military = data;
    eventBus.emit('state:military', data);
  }

  setConnected(value) {
    this.connected = value;
    eventBus.emit(value ? 'state:connected' : 'state:disconnected');
  }
}

export const state = new StateStore();
