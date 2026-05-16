/**
 * Internationalization (i18n) — UI label dictionary and helpers.
 *
 * Effect formatting has moved to web/js/lib/format.js (formatEffect, fmtEffectRow, etc.)
 */

export const dict = {
  // Common UI labels
  effort: 'Effort',
  effects: 'Effects',
  requires: 'Requires',
  status: 'Status',
  available: 'Available',
  completed: 'Completed',
  'in-progress': 'In Progress',
  building: 'Building',
};

/**
 * Format a number as integer (round, no decimals)
 */
export function fmtNumber(n) {
  if (n == null) return '—';
  if (typeof n !== 'number') return String(n);
  return Math.round(n).toLocaleString('de-DE');
}

/**
 * Get a translated string, fallback to original if not found
 */
export function t(key) {
  return dict[key] ?? key;
}

// Re-export formatEffect from format.js so existing imports from i18n.js keep working
export { formatEffect } from './lib/format.js';

export default { dict, t };
