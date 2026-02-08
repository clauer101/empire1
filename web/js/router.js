/**
 * Hash-based router for single-page navigation.
 *
 * Each view module must export:
 *   {
 *     id:    string,            // route name (used in hash)
 *     title: string,            // page title
 *     init:  (container, api, state) => void,  // build DOM (called once)
 *     enter: () => void,        // called on every navigation to this view
 *     leave: () => void,        // called when navigating away
 *   }
 *
 * Usage:
 *   const router = new Router(containerEl, api, state);
 *   router.register(dashboardView);
 *   router.register(loginView);
 *   router.start();                // reads current hash, activates view
 *   router.navigate('dashboard');  // programmatic navigation
 */

class Router {
  /**
   * @param {HTMLElement} container  DOM element where views are rendered
   * @param {import('./api.js').ApiClient} api
   * @param {import('./state.js').StateStore} state
   */
  constructor(container, api, state) {
    this._container = container;
    this._api = api;
    this._state = state;
    /** @type {Map<string, object>} route id → view module */
    this._views = new Map();
    /** @type {Map<string, HTMLElement>} route id → view DOM element */
    this._viewElements = new Map();
    /** @type {string|null} */
    this._activeViewId = null;
    /** @type {string} default route when hash is empty */
    this.defaultRoute = 'login';
    /** @type {string[]} routes that don't require auth */
    this.publicRoutes = ['login', 'signup'];

    this._onHashChange = this._onHashChange.bind(this);
  }

  /**
   * Register a view module.
   * @param {object} view
   */
  register(view) {
    this._views.set(view.id, view);

    // Create a wrapper div for this view (hidden by default)
    const el = document.createElement('div');
    el.id = `view-${view.id}`;
    el.className = 'view';
    el.style.display = 'none';
    this._container.appendChild(el);
    this._viewElements.set(view.id, el);

    // Let the view build its DOM structure
    view.init(el, this._api, this._state);
  }

  /**
   * Start listening to hash changes and activate current route.
   */
  start() {
    window.addEventListener('hashchange', this._onHashChange);
    this._onHashChange();
  }

  /**
   * Stop listening.
   */
  stop() {
    window.removeEventListener('hashchange', this._onHashChange);
  }

  /**
   * Navigate to a route programmatically.
   * @param {string} viewId
   */
  navigate(viewId) {
    window.location.hash = `#${viewId}`;
  }

  /**
   * Get the current route id from the hash.
   * @returns {string}
   */
  currentRoute() {
    const hash = window.location.hash.replace('#', '');
    return hash || this.defaultRoute;
  }

  _onHashChange() {
    const routeId = this.currentRoute();

    // Auth guard: redirect to login if not authenticated
    if (!this.publicRoutes.includes(routeId) && !this._state.auth.authenticated) {
      this.navigate('login');
      return;
    }

    // If already on login and authenticated, go to dashboard
    if (routeId === 'login' && this._state.auth.authenticated) {
      this.navigate('dashboard');
      return;
    }

    this._activateView(routeId);
  }

  /**
   * @param {string} viewId
   */
  _activateView(viewId) {
    if (!this._views.has(viewId)) {
      console.warn(`[Router] unknown route: ${viewId}`);
      this.navigate(this.defaultRoute);
      return;
    }

    // Leave current view
    if (this._activeViewId && this._activeViewId !== viewId) {
      const prev = this._views.get(this._activeViewId);
      const prevEl = this._viewElements.get(this._activeViewId);
      if (prev && prevEl) {
        prevEl.style.display = 'none';
        prev.leave();
      }
    }

    // Enter new view
    const view = this._views.get(viewId);
    const el = this._viewElements.get(viewId);
    el.style.display = '';
    this._activeViewId = viewId;
    document.title = `E3 — ${view.title}`;
    view.enter();

    // Update nav active state
    document.querySelectorAll('[data-route]').forEach((navEl) => {
      navEl.classList.toggle('active', navEl.dataset.route === viewId);
    });
  }
}

export { Router };
