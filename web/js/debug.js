/**
 * Debug mode — display API responses as toasts
 */

class DebugMode {
  constructor() {
    this.enabled = localStorage.getItem('debug-mode') === 'true';
    this._toastCallback = null;
  }

  /**
   * Enable/disable debug mode
   */
  toggle(enabled) {
    this.enabled = enabled;
    localStorage.setItem('debug-mode', String(enabled));
  }

  /**
   * Register callback to show toasts
   */
  setToastCallback(callback) {
    this._toastCallback = callback;
  }

  /**
   * Log a response as toast (if debug enabled)
   */
  logResponse(type, data) {
    if (!this.enabled || !this._toastCallback) return;

    // Format: "type: {key1: value1, key2: value2}"
    let text = type;
    if (data && typeof data === 'object') {
      const keys = Object.keys(data).slice(0, 3); // Limit keys shown
      const pairs = keys.map(k => {
        const v = data[k];
        if (typeof v === 'string' && v.length > 20) {
          return `${k}: "${v.substring(0, 20)}..."`;
        } else if (typeof v === 'string') {
          return `${k}: "${v}"`;
        } else if (typeof v === 'number') {
          return `${k}: ${v}`;
        } else {
          return `${k}: [${typeof v}]`;
        }
      });
      text = `${type} { ${pairs.join(', ')} }`;
    }

    this._toastCallback(text, 'debug');
  }
}

export const debug = new DebugMode();
