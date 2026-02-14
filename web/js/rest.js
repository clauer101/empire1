/**
 * RestClient — HTTP/REST communication with the game server.
 *
 * Handles all economy / non-realtime requests via REST endpoints,
 * while the WebSocket connection (ApiClient) remains for real-time
 * battle push messages.
 *
 * Token management:
 *   - JWT token stored in localStorage
 *   - Automatically attached as Authorization: Bearer header
 *   - On 401 response, emits 'rest:unauthorized' event
 *
 * Usage:
 *   import { rest } from './rest.js';
 *   rest.init('http://localhost:8080');
 *   const resp = await rest.login('user', 'pass');
 *   const summary = await rest.getSummary();
 */

import { state } from './state.js';
import { eventBus } from './events.js';

const TOKEN_KEY = 'e3_jwt_token';

class RestClient {
  constructor() {
    /** @type {string} */
    this.baseUrl = '';
    /** @type {number} ms before a request times out */
    this.timeout = 15000;
  }

  /**
   * Set the base URL for the REST API.
   * @param {string} baseUrl  e.g. 'http://localhost:8080'
   */
  init(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  // ── Token Management ──────────────────────────────────────

  /** @returns {string|null} */
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  /** @param {string} token */
  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  /** @returns {boolean} */
  get hasToken() {
    return !!this.getToken();
  }

  // ── Low-level HTTP ────────────────────────────────────────

  /**
   * Generic fetch wrapper with auth header and timeout.
   * @param {string} method  HTTP method
   * @param {string} path    e.g. '/api/empire/summary'
   * @param {object} [body]  JSON body (for POST/PUT)
   * @returns {Promise<object>} parsed JSON response
   */
  async _fetch(method, path, body) {
    const url = `${this.baseUrl}${path}`;
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(url, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timer);

      if (resp.status === 401) {
        this.clearToken();
        eventBus.emit('rest:unauthorized');
        throw new Error('Unauthorized — token expired or invalid');
      }

      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail.detail || `HTTP ${resp.status}`);
      }

      return await resp.json();
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        throw new Error(`Request timeout: ${method} ${path}`);
      }
      throw err;
    }
  }

  /** @returns {Promise<object>} */
  _get(path) { return this._fetch('GET', path); }

  /** @returns {Promise<object>} */
  _post(path, body) { return this._fetch('POST', path, body); }

  /** @returns {Promise<object>} */
  _put(path, body) { return this._fetch('PUT', path, body); }

  // ── Auth ──────────────────────────────────────────────────

  /**
   * Login via REST. Stores JWT token on success.
   * @param {string} username
   * @param {string} password
   * @returns {Promise<object>} { success, uid, token, summary?, reason? }
   */
  async login(username, password) {
    const resp = await this._post('/api/auth/login', { username, password });
    if (resp.success && resp.token) {
      this.setToken(resp.token);
      state.setAuth(resp.uid, username);
      if (resp.summary) {
        state.setSummary(resp.summary);
      }
    }
    return resp;
  }

  /**
   * Signup via REST.
   * @param {string} username
   * @param {string} password
   * @param {string} [email]
   * @param {string} [empire_name]
   * @returns {Promise<object>}
   */
  async signup(username, password, email, empire_name) {
    return this._post('/api/auth/signup', { username, password, email, empire_name });
  }

  /**
   * Logout — clear token and auth state.
   */
  logout() {
    this.clearToken();
    state.clearAuth();
  }

  /**
   * Try auto-login from URL params or stored token.
   * If a token exists, validates by fetching summary.
   * Falls back to credential-based login.
   * @returns {Promise<boolean>}
   */
  async tryAutoLogin() {
    // Check URL params first
    const params = new URLSearchParams(window.location.search);
    const username = params.get('user');
    const password = params.get('pwd');

    if (username && password) {
      try {
        const resp = await this.login(username, password);
        window.history.replaceState({}, '', window.location.pathname + window.location.hash);
        return resp.success;
      } catch (err) {
        console.warn('[RestClient] auto-login via URL params failed:', err.message);
        return false;
      }
    }

    // If we have a stored token, validate it
    if (this.hasToken) {
      try {
        const summary = await this.getSummary();
        if (summary) {
          state.setAuth(summary.uid, summary.name);
          state.setSummary(summary);
          return true;
        }
      } catch (err) {
        console.warn('[RestClient] stored token invalid:', err.message);
        this.clearToken();
      }
    }

    // Fall back to stored credentials (for migration from old WS-only flow)
    const savedRaw = sessionStorage.getItem('e3_credentials');
    if (savedRaw) {
      try {
        const saved = JSON.parse(savedRaw);
        if (saved.username && saved.password) {
          const resp = await this.login(saved.username, saved.password);
          return resp.success;
        }
      } catch (err) {
        console.warn('[RestClient] credential-based auto-login failed:', err.message);
      }
    }

    return false;
  }

  // ── Empire Queries ────────────────────────────────────────

  /** @returns {Promise<object>} */
  async getSummary() {
    const resp = await this._get('/api/empire/summary');
    state.setSummary(resp);
    return resp;
  }

  /** @returns {Promise<object>} */
  async getItems() {
    const resp = await this._get('/api/empire/items');
    state.setItems(resp);
    return resp;
  }

  /** @returns {Promise<object>} */
  async getMilitary() {
    const resp = await this._get('/api/empire/military');
    state.setMilitary(resp);
    return resp;
  }

  // ── Building / Research ───────────────────────────────────

  /**
   * Queue a building or research item.
   * @param {string} iid Item IID
   * @returns {Promise<object>}
   */
  async buildItem(iid) {
    return this._post('/api/empire/build', { iid });
  }

  // ── Citizens ──────────────────────────────────────────────

  /**
   * Upgrade citizen count.
   * @returns {Promise<object>}
   */
  async upgradeCitizen() {
    return this._post('/api/empire/citizen/upgrade', {});
  }

  /**
   * Reassign citizen roles.
   * @param {object} citizens e.g. { merchant: 2, scientist: 1, artist: 0 }
   * @returns {Promise<object>}
   */
  async changeCitizen(citizens) {
    return this._put('/api/empire/citizen', citizens);
  }

  // ── Map ───────────────────────────────────────────────────

  /** @returns {Promise<object>} */
  async loadMap() {
    return this._get('/api/map');
  }

  /**
   * @param {object} tiles
   * @returns {Promise<object>}
   */
  async saveMap(tiles) {
    return this._put('/api/map', { tiles });
  }

  // ── Army ──────────────────────────────────────────────────

  /**
   * Create a new army.
   * @param {string} name
   * @returns {Promise<object>}
   */
  async createArmy(name) {
    return this._post('/api/army', { name });
  }

  /**
   * Rename an army.
   * @param {number} aid
   * @param {string} name
   * @returns {Promise<object>}
   */
  async changeArmy(aid, name) {
    return this._put(`/api/army/${aid}`, { name });
  }

  /**
   * Add a wave to an army.
   * @param {number} aid
   * @returns {Promise<object>}
   */
  async addWave(aid) {
    return this._post(`/api/army/${aid}/wave`, {});
  }

  /**
   * Change critter type / slots in a wave.
   * @param {number} aid
   * @param {number} waveNumber
   * @param {string} [critterIid]
   * @param {number} [slots]
   * @returns {Promise<object>}
   */
  async changeWave(aid, waveNumber, critterIid, slots) {
    const body = {};
    if (critterIid) body.critter_iid = critterIid;
    if (slots !== undefined) body.slots = slots;
    return this._put(`/api/army/${aid}/wave/${waveNumber}`, body);
  }

  // ── Attack ────────────────────────────────────────────────

  /**
   * Launch an attack.
   * @param {number} targetUid
   * @param {number} armyAid
   * @returns {Promise<object>}
   */
  async attackOpponent(targetUid, armyAid) {
    return this._post('/api/attack', { target_uid: targetUid, army_aid: armyAid });
  }

  // ── WebSocket URL helper ──────────────────────────────────

  /**
   * Returns the WebSocket URL with JWT token as query param
   * for authenticated WS connections.
   * @param {string} wsBaseUrl  e.g. 'ws://localhost:8765'
   * @returns {string}
   */
  getAuthenticatedWsUrl(wsBaseUrl) {
    const token = this.getToken();
    if (token) {
      return `${wsBaseUrl}?token=${encodeURIComponent(token)}`;
    }
    return wsBaseUrl;
  }
}

/** Singleton instance */
const rest = new RestClient();
export { rest, RestClient };
