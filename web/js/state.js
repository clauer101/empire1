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
 *   'state:spy_reports' – spy report cache refreshed or updated
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

    /** @type {{ attack_id: number, attacker_uid: number }|null} incoming attack to watch in battle view */
    this.pendingIncomingAttack = null;

    /** @type {boolean} */
    this.connected = false;

    /** @type {Map<number, object>|null} Latest spy report per defender_uid */
    this.spyReports = null;
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

  setSpyReports(reportsArray) {
    const map = new Map();
    for (const r of reportsArray || []) map.set(r.defender_uid, r);
    this.spyReports = map;
    eventBus.emit('state:spy_reports', this.spyReports);
  }

  upsertSpyReport(report) {
    if (!this.spyReports) this.spyReports = new Map();
    this.spyReports.set(report.defender_uid, report);
    eventBus.emit('state:spy_reports', this.spyReports);
  }
}

export const state = new StateStore();
