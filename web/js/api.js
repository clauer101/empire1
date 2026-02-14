/**
 * ApiClient — WebSocket-based communication with the game server.
 *
 * All server interaction goes through this class.
 * Methods return Promises that resolve when the server responds,
 * or resolve immediately for fire-and-forget commands.
 *
 * Usage:
 *   const api = new ApiClient('ws://localhost:8765');
 *   await api.connect();
 *   const summary = await api.getSummary();
 */

import { state } from './state.js';
import { eventBus } from './events.js';
import { debug } from './debug.js';
import ReconnectingWebSocket from './lib/reconnecting-websocket.mjs';

let _requestId = 0;
function nextRequestId() {
  return `req_${++_requestId}_${Date.now()}`;
}

class ApiClient {
  /**
   * @param {string} wsUrl  WebSocket URL, e.g. 'ws://localhost:8765'
   */
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    /** @type {ReconnectingWebSocket|null} */
    this._ws = null;
    /** @type {Promise<void>|null} */
    this._connectPromise = null;
    /** @type {Map<string, {resolve: Function, reject: Function, timer: number}>} */
    this._pending = new Map();
    /** @type {number} ms before a request times out */
    this.timeout = 10000;
    /** @type {boolean} */
    this._intentionalClose = false;
    /** @type {boolean} */
    this._hasConnectedOnce = false;
    /** @type {number|null} polling interval id */
    this._pollTimer = null;
    /** @type {number} ms between polling cycles */
    this.pollInterval = 5000;
  }

  // ── Connection Management ──────────────────────────────────

  /**
   * Open the WebSocket connection.
   * @returns {Promise<void>} resolves once connected
   */
  connect() {
    if (this._connectPromise) {
      return this._connectPromise;
    }
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this._ws && this._ws.readyState === WebSocket.CONNECTING) {
      this._connectPromise = new Promise((resolve, reject) => {
        const ws = this._ws;
        let settled = false;

        const cleanup = () => {
          ws.removeEventListener('open', onOpen);
          ws.removeEventListener('close', onClose);
          ws.removeEventListener('error', onError);
          this._connectPromise = null;
        };

        const onOpen = () => {
          if (settled) return;
          settled = true;
          cleanup();
          resolve();
        };

        const onClose = (ev) => {
          if (settled) return;
          settled = true;
          cleanup();
          reject(new Error(`WebSocket closed while connecting (code ${ev.code})`));
        };

        const onError = () => {
          if (settled) return;
          settled = true;
          cleanup();
          reject(new Error('WebSocket error while connecting'));
        };

        ws.addEventListener('open', onOpen);
        ws.addEventListener('close', onClose);
        ws.addEventListener('error', onError);
      });

      return this._connectPromise;
    }

    this._connectPromise = new Promise((resolve, reject) => {
      this._intentionalClose = false;

      // Close any existing socket before reinitializing
      if (this._ws) {
        this._ws.removeEventListener('open', this._onSocketOpen);
        this._ws.removeEventListener('close', this._onSocketClose);
        this._ws.removeEventListener('error', this._onSocketError);
        this._ws.removeEventListener('message', this._onSocketMessage);
        try { this._ws.close(1000, 'reinitialize'); } catch (_) {}
        this._ws = null;
      }

      const ws = new ReconnectingWebSocket(this.wsUrl, [], {
        WebSocket,
        minReconnectionDelay: 1000,
        maxReconnectionDelay: 10000,
        reconnectionDelayGrowFactor: 1.5,
        connectionTimeout: 4000,
        maxRetries: Infinity,
      });
      this._ws = ws;

      let settled = false;

      this._onSocketOpen = async () => {
        const isReconnect = this._hasConnectedOnce;
        this._hasConnectedOnce = true;
        console.log(isReconnect ? '[ApiClient] reconnected to' : '[ApiClient] connected to', this.wsUrl);
        state.setConnected(true);

        if (!settled) {
          settled = true;
          this._connectPromise = null;
          resolve();
          return;
        }

        if (this._intentionalClose) return;

        const creds = this._loadCredentials();
        if (creds) {
          try {
            await this.login(creds.username, creds.password);
          } catch (err) {
            console.warn('[ApiClient] re-auth on reconnect failed:', err?.message || err);
          }
        }
      };

      this._onSocketClose = (ev) => {
        console.log('[ApiClient] disconnected', ev.code, ev.reason);
        state.setConnected(false);
        this._rejectAllPending('Connection closed');
        if (!settled) {
          settled = true;
          this._connectPromise = null;
          reject(new Error(`WebSocket closed before open (code ${ev.code})`));
        }
      };

      this._onSocketError = () => {
        if (!settled) {
          settled = true;
          this._connectPromise = null;
          reject(new Error('WebSocket connection failed'));
        }
      };

      this._onSocketMessage = (ev) => {
        this._handleMessage(ev.data);
      };

      ws.addEventListener('open', this._onSocketOpen);
      ws.addEventListener('close', this._onSocketClose);
      ws.addEventListener('error', this._onSocketError);
      ws.addEventListener('message', this._onSocketMessage);
    });

    return this._connectPromise;
  }

  /**
   * Close the connection intentionally (no auto-reconnect).
   */
  disconnect(reason = 'intentional-disconnect') {
    this._intentionalClose = true;
    this._connectPromise = null;
    this.stopPolling();
    this._rejectAllPending(`Connection closed: ${reason}`);
    if (this._ws) {
      this._ws.removeEventListener('open', this._onSocketOpen);
      this._ws.removeEventListener('close', this._onSocketClose);
      this._ws.removeEventListener('error', this._onSocketError);
      this._ws.removeEventListener('message', this._onSocketMessage);
      this._ws.close(1000, reason);
      this._ws = null;
    }
    state.setConnected(false);
  }

  // ── Low-level Send / Receive ───────────────────────────────

  /**
   * Send a message and wait for a typed response.
   * @param {object} msg        Message object (must have 'type')
   * @param {string} expectType Expected response type (null = fire-and-forget)
   * @returns {Promise<object|null>}
   */
  _request(msg, expectType) {
    return new Promise((resolve, reject) => {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
        return reject(new Error('Not connected'));
      }

      // Inject authenticated sender UID so the server knows who we are
      if (state.auth.authenticated && state.auth.uid) {
        msg.sender = state.auth.uid;
      }

      if (!expectType) {
        // fire-and-forget
        this._ws.send(JSON.stringify(msg));
        return resolve(null);
      }

      const requestId = nextRequestId();
      msg.request_id = requestId;

      const timer = setTimeout(() => {
        this._pending.delete(requestId);
        reject(new Error(`Timeout waiting for ${expectType}`));
      }, this.timeout);

      this._pending.set(requestId, { resolve, reject, timer });
      this._ws.send(JSON.stringify(msg));
    });
  }

  /**
   * Handle incoming WebSocket message.
   * @param {string} raw
   */
  _handleMessage(raw) {
    let msg;
    try {
      msg = JSON.parse(raw);
    } catch (err) {
      console.error('[ApiClient] invalid JSON from server:', raw);
      return;
    }

    if (msg.type === 'debug') {
      debug.logResponse(msg.type, msg);
    }

    // If this is a response to a pending request, resolve it
    if (msg.request_id && this._pending.has(msg.request_id)) {
      const { resolve, reject, timer } = this._pending.get(msg.request_id);
      clearTimeout(timer);
      this._pending.delete(msg.request_id);

      if (msg.type === 'error') {
        reject(new Error(msg.message || 'Server error'));
      } else {
        if (msg._debug) {
          console.debug('[ApiClient] Debug info:', msg._debug);
        }
        resolve(msg);
      }
      return;
    }

    // Server-push message — dispatch via EventBus
    if (msg._debug) {
      console.debug('[ApiClient] Server debug (push):', msg._debug);
    }
    this._handlePush(msg);
  }

  /**
   * Handle unsolicited server-push messages.
   * @param {object} msg
   */
  _handlePush(msg) {
    switch (msg.type) {
      case 'welcome':
        console.log('[ApiClient] guest uid:', msg.temp_uid);
        break;
      case 'quick_message':
        eventBus.emit('server:quick_message', msg);
        break;
      case 'notification':
        eventBus.emit('server:notification', msg);
        break;
      case 'citizen_upgrade_response':
        eventBus.emit('server:citizen_upgrade_response', msg);
        break;
      case 'change_citizen_response':
        eventBus.emit('server:change_citizen_response', msg);
        break;
      case 'build_response':
        eventBus.emit('server:build_response', msg);
        break;
      case 'battle_setup':
        eventBus.emit('server:battle_setup', msg);
        break;
      case 'battle_update':
        eventBus.emit('server:battle_update', msg);
        break;
      case 'battle_summary':
        eventBus.emit('server:battle_summary', msg);
        break;
      case 'battle_status':
        eventBus.emit('server:battle_status', msg);
        break;
      case 'attack_phase_changed':
        console.log('[PUSH] Attack phase changed: id=%d phase=%s', msg.attack_id, msg.new_phase);
        eventBus.emit('server:attack_phase_changed', msg);
        break;
      case 'attack_response':
        console.warn('[ApiClient] ⚠️  attack_response received as PUSH (request_id missing!):', msg);
        console.warn('[ApiClient] This means the request_id was not preserved. Check server.py or message handler.');
        eventBus.emit('server:message', msg);
        break;
      default:
        if (msg.type && msg.type.includes('response')) {
          console.warn('[ApiClient] ⚠️  Response received as PUSH:', msg.type, msg);
        } else {
          console.log('[ApiClient] unhandled push:', msg.type, msg);
        }
        eventBus.emit('server:message', msg);
    }
  }

  _rejectAllPending(reason) {
    for (const [id, { reject, timer }] of this._pending) {
      clearTimeout(timer);
      reject(new Error(reason));
    }
    this._pending.clear();
  }

  // ── Credential Storage ─────────────────────────────────────

  _saveCredentials(username, password) {
    sessionStorage.setItem('e3_credentials', JSON.stringify({ username, password }));
  }

  _loadCredentials() {
    const raw = sessionStorage.getItem('e3_credentials');
    return raw ? JSON.parse(raw) : null;
  }

  _clearCredentials() {
    sessionStorage.removeItem('e3_credentials');
  }

  // ── Polling ────────────────────────────────────────────────

  /**
   * Start periodic polling of summary data.
   * @param {number} [interval] ms between polls
   */
  startPolling(interval) {
    this.stopPolling();
    this.pollInterval = interval || this.pollInterval;
    this._poll(); // immediate first poll
    this._pollTimer = setInterval(() => this._poll(), this.pollInterval);
  }

  stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }

  async _poll() {
    try {
      const summary = await this.getSummary();
      state.setSummary(summary);
    } catch (err) {
      // Silently ignore poll errors (reconnect handles it)
    }
  }

  // ── Auth ───────────────────────────────────────────────────

  /**
   * Authenticate with the server.
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{success: boolean, uid: number, reason?: string}>}
   */
  async login(username, password) {
    const resp = await this._request(
      { type: 'auth_request', username, password },
      'auth_response'
    );
    if (resp.success) {
      this._saveCredentials(username, password);
      state.setAuth(resp.uid, username);
      // If server sends fresh summary data after login, apply it immediately
      if (resp.summary) {
        state.setSummary(resp.summary);
      }
    }
    return resp;
  }

  /**
   * Register a new account.
   * @param {string} username
   * @param {string} password
   * @param {string} [email]
   * @returns {Promise<object>}
   */
  async signup(username, password, email, empire_name) {
    return this._request(
      { type: 'signup', username, password, email, empire_name },
      'signup_response'
    );
  }

  /**
   * Logout: clear credentials and navigate to login.
   */
  logout() {
    this._clearCredentials();
    state.clearAuth();
    this.stopPolling();
  }

  /**
   * Try to auto-login from saved credentials or URL params.
   * @returns {Promise<boolean>} true if auto-login succeeded
   */
  async tryAutoLogin() {
    // Check URL params first
    const params = new URLSearchParams(window.location.search);
    let username = params.get('user');
    let password = params.get('pwd');

    // Fall back to session storage
    if (!username || !password) {
      const saved = this._loadCredentials();
      if (saved) {
        username = saved.username;
        password = saved.password;
      }
    }

    if (!username || !password) return false;

    try {
      const resp = await this.login(username, password);
      // Clean URL params after successful login
      if (params.has('user')) {
        window.history.replaceState({}, '', window.location.pathname + window.location.hash);
      }
      return resp.success;
    } catch (err) {
      console.warn('[ApiClient] auto-login failed:', err.message);
      return false;
    }
  }

  // ── Queries (return response) ──────────────────────────────

  /**
   * Get empire summary.
   * @param {number} [uid] target UID (omit for own empire)
   * @returns {Promise<object>} summary_response
   */
  async getSummary(uid) {
    const msg = { type: 'summary_request' };
    if (uid !== undefined) msg.uid = uid;
    return this._request(msg, 'summary_response');
  }

  /**
   * Get item catalog (buildings & knowledge definitions).
   * @returns {Promise<object>} item_response
   */
  async getItems() {
    const resp = await this._request(
      { type: 'item_request' },
      'item_response'
    );
    state.setItems(resp);
    return resp;
  }

  /**
   * Get military overview (armies, attacks).
   * @param {number} [uid]
   * @returns {Promise<object>} military_response
   */
  async getMilitary(uid) {
    const msg = { type: 'military_request' };
    if (uid !== undefined) msg.uid = uid;
    const resp = await this._request(msg, 'military_response');
    state.setMilitary(resp);
    return resp;
  }

  /**
   * Load the hex map from the server.
   * @returns {Promise<object>} map_load_response with tiles
   */
  async loadMap() {
    const resp = await this._request(
      { type: 'map_load_request' },
      'map_load_response'
    );
    return resp;
  }

  /**
   * Save the hex map to the server.
   * @param {object} tiles Hex tiles {hexKey: {type, ...}}
   * @returns {Promise<object>} map_save_response
   */
  async saveMap(tiles) {
    const resp = await this._request(
      { type: 'map_save_request', tiles },
      'map_save_response'
    );
    return resp;
  }

  async startBattle() {
    const resp = await this._request(
      { type: 'battle_request' },
      'battle_response'
    );
    return resp;
  }

  /**
   * Get timeline / messages.
   * @param {number} targetUid
   * @param {string[]} [markRead]
   * @param {string[]} [markUnread]
   * @returns {Promise<object>} timeline_response
   */
  async getTimeline(targetUid, markRead, markUnread) {
    const msg = { type: 'timeline_request', target_uid: targetUid };
    if (markRead) msg.mark_read = markRead;
    if (markUnread) msg.mark_unread = markUnread;
    return this._request(msg, 'timeline_response');
  }

  /**
   * Get user info for UIDs.
   * @param {number[]} uids
   * @returns {Promise<object>} userinfo_response
   */
  async getUserInfo(uids) {
    return this._request(
      { type: 'userinfo_request', uids },
      'userinfo_response'
    );
  }

  /**
   * Get hall of fame / rankings.
   * @returns {Promise<object>} hall_of_fame_response
   */
  async getHallOfFame() {
    return this._request(
      { type: 'hall_of_fame_request' },
      'hall_of_fame_response'
    );
  }

  /**
   * Get user preferences.
   * @returns {Promise<object>} preferences_response
   */
  async getPreferences() {
    return this._request(
      { type: 'preferences_request' },
      'preferences_response'
    );
  }

  /**
   * Get next wave preview in a battle.
   * @param {string} bid battle id
   * @returns {Promise<object>} battle_next_wave_response
   */
  async getBattleNextWave(bid) {
    return this._request(
      { type: 'battle_next_wave_request', bid },
      'battle_next_wave_response'
    );
  }

  /**
   * Get notifications.
   * @returns {Promise<object>} notification_response
   */
  async getNotifications() {
    return this._request(
      { type: 'notification_request' },
      'notification_response'
    );
  }

  // ── Commands (fire-and-forget) ─────────────────────────────

  /**
   * Queue a building or research item.
   * @param {string} iid Item IID
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async buildItem(iid) {
    return new Promise((resolve, reject) => {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
        return reject(new Error('Not connected'));
      }

      // Send request WITHOUT request_id so server sends as push notification
      const msg = { type: 'new_item', iid };
      if (state.auth.authenticated && state.auth.uid) {
        msg.sender = state.auth.uid;
      }
      console.log('[ApiClient] → new_item:', iid);
      this._ws.send(JSON.stringify(msg));

      // Wait for push response (with timeout)
      const timer = setTimeout(() => {
        unsub();
        console.warn('[ApiClient] ⚠️ build_response timeout after', this.timeout, 'ms');
        reject(new Error('build_response timeout'));
      }, this.timeout);

      const unsub = eventBus.on('server:build_response', (response) => {
        clearTimeout(timer);
        unsub();
        console.log('[ApiClient] ← build_response received:', response);
        resolve(response);
      });
    });
  }

  /**
   * Place a structure on the hex map.
   * @param {string} iid Structure IID
   * @param {number} hexQ hex column
   * @param {number} hexR hex row
   */
  async placeStructure(iid, hexQ, hexR) {
    return this._request(
      { type: 'new_structure', iid, hex_q: hexQ, hex_r: hexR },
      null
    );
  }

  /**
   * Remove a structure.
   * @param {string} sid Structure ID
   */
  async deleteStructure(sid) {
    return this._request({ type: 'delete_structure', sid }, null);
  }

  /**
   * Upgrade a structure.
   * @param {string} sid Structure ID
   */
  async upgradeStructure(sid) {
    return this._request({ type: 'upgrade_structure', sid }, null);
  }

  /**
   * Upgrade citizen count.
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async upgradeCitizen() {
    return new Promise((resolve, reject) => {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
        return reject(new Error('Not connected'));
      }

      // Send request
      const msg = { type: 'citizen_upgrade' };
      if (state.auth.authenticated && state.auth.uid) {
        msg.sender = state.auth.uid;
      }
      this._ws.send(JSON.stringify(msg));

      // Wait for response (with timeout)
      const timer = setTimeout(() => {
        unsub();
        reject(new Error('citizen_upgrade response timeout'));
      }, this.timeout);

      const unsub = eventBus.on('server:citizen_upgrade_response', (response) => {
        clearTimeout(timer);
        unsub();
        resolve(response);
      });
    });
  }

  /**
   * Reassign citizen roles.
   * @param {object} citizens e.g. { merchant: 2, scientist: 1, artist: 0 }
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async changeCitizen(citizens) {
    return new Promise((resolve, reject) => {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
        return reject(new Error('Not connected'));
      }

      // Send request
      const msg = { type: 'change_citizen', citizens };
      if (state.auth.authenticated && state.auth.uid) {
        msg.sender = state.auth.uid;
      }
      this._ws.send(JSON.stringify(msg));

      // Wait for response (with timeout)
      const timer = setTimeout(() => {
        unsub();
        reject(new Error('change_citizen response timeout'));
      }, this.timeout);

      const unsub = eventBus.on('server:change_citizen_response', (response) => {
        clearTimeout(timer);
        unsub();
        resolve(response);
      });
    });
  }

  /**
   * Buy more max_life.
   */
  async increaseLife() {
    return this._request({ type: 'increase_life' }, null);
  }

  /**
   * Create a new army.
   * @param {string} name
   */
  async createArmy(name) {
    return this._request({ type: 'new_army', name }, null);
  }

  /**
   * Modify an existing army.
   * @param {int} aid Army ID
   * @param {string} name
   */
  async changeArmy(aid, name) {
    return this._request({ type: 'change_army', aid, name }, null);
  }

  /**
   * Add a new wave to an army.
   * The server decides the critter type (defaults to SLAVE).
   * @param {int} aid Army ID
   */
  async addWave(aid) {
    return this._request(
      { type: 'new_wave', aid },
      null
    );
  }

  /**
   * Change critter type and/or critter count in existing wave.
   * @param {int} aid Army ID
   * @param {int} waveNumber Wave index (0-based)
   * @param {string} critterIid Critter type (optional)
   * @param {int} slots Wave capacity (optional)
   */
  async changeWave(aid, waveNumber, critterIid, slots) {
    const payload = { type: 'change_wave', aid, wave_number: waveNumber };
    if (critterIid) payload.critter_iid = critterIid;
    if (slots !== undefined) payload.slots = slots;
    return this._request(payload, null);
  }

  /**
   * Launch an attack.
   * @param {number} targetUid
   * @param {string} armyAid
   * @param {string[]} [spyOptions]
   */
  async attack(targetUid, armyAid, spyOptions) {
    const msg = { type: 'new_attack_request', target_uid: targetUid, army_aid: armyAid };
    if (spyOptions) msg.spy_options = spyOptions;
    return this._request(msg, null);
  }

  /**
   * Launch an attack by target Empire UID.
   * @param {number} targetUid Target Empire UID
   * @param {number} armyAid
   */
  async attackOpponent(targetUid, armyAid) {
    const msg = { type: 'new_attack_request', target_uid: targetUid, army_aid: armyAid };
    return this._request(msg, 'attack_response');
  }

  /** End an active siege. */
  async endSiege() {
    return this._request({ type: 'end_siege' }, null);
  }

  /**
   * Register to watch a battle.
   * @param {string} bid Battle ID
   */
  async battleRegister(bid) {
    return this._request({ type: 'battle_register', bid }, null);
  }

  /**
   * Unregister from watching a battle.
   * @param {string} bid Battle ID
   */
  async battleUnregister(bid) {
    return this._request({ type: 'battle_unregister', bid }, null);
  }

  /**
   * Send a message to another player.
   * @param {number} targetUid
   * @param {string} body
   */
  async sendMessage(targetUid, body) {
    return this._request(
      { type: 'user_message', target_uid: targetUid, body },
      null
    );
  }

  /**
   * Update account preferences.
   * @param {string} statement
   * @param {string} email
   */
  async changePreferences(statement, email) {
    return this._request(
      { type: 'change_preferences', statement, email },
      null
    );
  }

  /**
   * Create a new empire.
   */
  async createEmpire() {
    return this._request({ type: 'create_empire' }, null);
  }
}

export { ApiClient };
