/**
 * Internationalization (i18n) — Central translation dictionary
 * Maps identifiers to user-friendly German display strings
 */

export const dict = {
  // Effect descriptions
  gold_offset: 'Increases gold production by a fixed amount',
  gold_modifier: 'Increases gold production by a multiplier',
  culture_offset: 'Increases culture production by a fixed amount',
  culture_modifier: 'Increases culture production by a multiplier',
  life_offset: 'Increases life energy by a fixed amount',
  build_speed_modifier: 'Accelerates building construction by a multiplier',
  build_speed_offset: 'Accelerates building construction by a fixed amount',
  research_speed_modifier: 'Accelerates research by a multiplier',
  research_speed_offset: 'Accelerates research by a fixed amount',
  incoming_siege_time_offset: 'Increases siege time of incoming armies by a fixed amount',
  outgoing_siege_time_offset: 'Decreases siege time of outgoing armies by a fixed amount',
  incoming_travel_time_offset: 'Increases travel time of incoming armies by a fixed amount',
  outgoing_travel_time_offset: 'Decreases travel time of outgoing armies by a fixed amount',
  wave_delay_offset: 'Decreases delay between battle waves by a fixed amount',
  wave_delay_modifier: 'Decreases delay between battle waves by a multiplier',

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

/**
 * Format effect key with its translated description
 */
export function formatEffect(key, value) {
  const description = dict[key] || key;
  const roundedValue = Math.round(value * 100) / 100;  // Round to 2 decimals max
  return `${description}${roundedValue > 0 ? ` (+${roundedValue})` : ` (${roundedValue})`}`;
}

export default { dict, t, formatEffect };
