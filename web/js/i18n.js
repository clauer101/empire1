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
  life_regen_modifier: 'Increases life energy by a fixed amount',
  build_speed_modifier: 'Accelerates building construction by a multiplier',
  build_speed_offset: 'Accelerates building construction by a fixed amount',
  research_speed_offset: 'Accelerates research by a fixed amount',
  research_speed_modifier: 'Accelerates research by a multiplier',
  siege_offset: 'Modifies siege time of armies',
  travel_offset: 'Modifies travel time of armies',
  wave_delay_offset: 'Increases delay between incoming waves',
  max_life_modifier: 'Increases maximum life',
  restore_life_after_loss_offset: 'Restores life after a lost battle',
  tower_sell_refund_modifier: 'Increases tower sell refund',
  artifact_steal_victory_modifier: 'Increases artifact steal chance on victory',
  artifact_steal_defeat_modifier: 'Increases artifact steal chance on defeat',
  spy_workshop: 'Unlocks workshop intelligence in spy reports',

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
 * Per-effect formatting metadata.
 *
 * scale:    multiply the raw value before display  (e.g. 100 for % modifiers)
 * unit:     string appended after the number
 * decimals: fixed decimal places (null = auto, trims trailing zeros)
 *
 * Modifiers (0.5 → "50%"):  scale:100, unit:'%', decimals:0
 * Time offsets (seconds):   unit:'s',  decimals:0
 * Production offsets (/s):  unit:'/s', decimals:2
 */
export const effectMeta = {
  gold_offset: { unit: '/s', decimals: 2 },
  gold_modifier: { scale: 100, unit: '%', decimals: 0 },
  culture_offset: { unit: '/s', decimals: 2 },
  culture_modifier: { scale: 100, unit: '%', decimals: 0 },
  life_regen_modifier: { unit: '/s', decimals: 3 },
  build_speed_offset: { unit: '/s', decimals: 2 },
  build_speed_modifier: { scale: 100, unit: '%', decimals: 0 },
  research_speed_offset: { unit: '/s', decimals: 2 },
  research_speed_modifier: { scale: 100, unit: '%', decimals: 0 },
  siege_offset: { fmt: 'duration' },
  travel_offset: { fmt: 'duration' },
  wave_delay_offset: { unit: 's', decimals: 1 },
  max_life_modifier: { unit: '', decimals: 1 },
  restore_life_after_loss_offset: { unit: '', decimals: 0 },
  tower_sell_refund_modifier: { scale: 100, unit: '%', decimals: 0 },
  artifact_steal_victory_modifier: { scale: 100, unit: '%', decimals: 0 },
  artifact_steal_defeat_modifier: { scale: 100, unit: '%', decimals: 0 },
  spy_workshop: { unit: '', decimals: 2 },
};

/**
 * Format effect key with its translated description
 */
function _fmtDuration(secs) {
  const sign = secs < 0 ? '-' : '';
  secs = Math.abs(secs);
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  if (h > 0 && m > 0) return `${sign}${h}h ${m}m`;
  if (h > 0) return `${sign}${h}h`;
  if (m > 0 && s > 0) return `${sign}${m}m ${s}s`;
  if (m > 0) return `${sign}${m}m`;
  return `${sign}${s}s`;
}

export function formatEffect(key, value) {
  const description = dict[key] || key;
  const meta = effectMeta[key] || {};

  if (meta.fmt === 'duration') {
    return `${description} (${_fmtDuration(value)})`;
  }

  const scale = meta.scale ?? 1;
  const unit = meta.unit ?? '';
  const decimals = meta.decimals;

  const scaled = value * scale;
  const formatted =
    decimals != null ? scaled.toFixed(decimals) : (Math.round(scaled * 100) / 100).toString();

  const sign = scaled > 0 ? '+' : '';
  return `${description} (${sign}${formatted}${unit})`;
}

export default { dict, t, formatEffect };
