/**
 * Shared formatting utilities.
 *
 * Effect helpers (all effects go through here — do not inline elsewhere):
 *   fmtEffectRow(key, value)     → HTML "<span>icon label:</span><span>+value</span>" for two-column display
 *   fmtEffectsInline(effects)    → compact comma-separated string, e.g. "💰 +3.6/h, 🎭 +5%"
 *   fmtTowerEffects(effects)     → tower combat effects: burn / slow / splash
 */

// Per-effect display metadata: [icon, label, valueFn]
const EFFECT_META = {
  gold_offset:                    ['💰', 'Gold income',       (v) => `${v > 0 ? '+' : ''}${(v * 3600).toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`],
  gold_modifier:                  ['💰', 'Gold bonus',        (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  culture_offset:                 ['🎭', 'Culture income',    (v) => `${v > 0 ? '+' : ''}${(v * 3600).toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`],
  culture_modifier:               ['🎭', 'Culture bonus',     (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  life_regen_modifier:            ['❤️', 'Life regen',        (v) => `${v > 0 ? '+' : ''}${(v * 3600).toFixed(2)}/h`],
  max_life_modifier:              ['❤️', 'Max life',          (v) => `${v > 0 ? '+' : ''}${v}`],
  restore_life_after_loss_offset: ['❤️', 'Life restore',      (v) => `${v > 0 ? '+' : ''}${v}`],
  build_speed_modifier:           ['🏗',  'Build speed',      (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  build_speed_offset:             ['🏗',  'Build speed',      (v) => `${v > 0 ? '+' : ''}${v}`],
  research_speed_modifier:        ['🔬', 'Research speed',    (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  research_speed_offset:          ['🔬', 'Research speed',    (v) => `${v > 0 ? '+' : ''}${v}`],
  travel_time_modifier:           ['🚀', 'Travel speed',      (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  wave_delay_offset:              ['⏳', 'Wave delay',        (v) => `${v > 0 ? '+' : ''}${v}s`],
  artifact_steal_victory_modifier:['⚜',  'Artifact steal (victory)', (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  artifact_steal_defeat_modifier: ['⚜',  'Artifact steal (defeat)',  (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  tower_sell_refund_modifier:     ['💵', 'Tower refund',      (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`],
  spy_workshop:                   ['🕵️', 'Workshop intel',    () => 'Unlocked'],
};

function _fallback(k, v) {
  const sign = v > 0 ? '+' : '';
  const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const val = Math.abs(v) < 1 ? `${sign}${(v * 100).toFixed(0)}%` : `${sign}${v}`;
  return [null, label, val];
}

/** Two-column HTML row: "<span>icon label:</span><span>+value</span>" */
export function fmtEffectRow(key, value) {
  const meta = EFFECT_META[key];
  if (meta) {
    const [icon, label, fmt] = meta;
    return `<span class="tt-dp-label">${icon} ${label}:</span><span>${fmt(value)}</span>`;
  }
  const [, label, val] = _fallback(key, value);
  return `<span class="tt-dp-label">${label}:</span><span>${val}</span>`;
}

/** Compact inline string for an effects dict, e.g. "💰 +3.6/h, 🎭 +5%" */
export function fmtEffectsInline(effects) {
  if (!effects || Object.keys(effects).length === 0) return '';
  return Object.entries(effects)
    .map(([k, v]) => {
      const meta = EFFECT_META[k];
      if (meta) return `${meta[0]} ${meta[2](v)}`;
      const [, label, val] = _fallback(k, v);
      return `${label}: ${val}`;
    })
    .join(', ');
}

/** Tower combat effects: burn / slow / splash */
export function fmtTowerEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) return '';
  return Object.entries(effects)
    .map(([k, v]) => {
      if (k === 'burn_duration') return `🔥 ${(v / 1000).toFixed(1)}s burn`;
      if (k === 'burn_dps')      return `🔥 ${v} dps`;
      if (k === 'slow_duration') return `❄ ${(v / 1000).toFixed(1)}s slow`;
      if (k === 'slow_ratio')    return `❄ ${Math.round(v * 100)}% speed`;
      if (k === 'splash_radius') return `💥 ${v} hex`;
      const sign = v > 0 ? '+' : '';
      const name = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      return Math.abs(v) < 1 ? `${name}: ${sign}${(v * 100).toFixed(0)}%` : `${name}: ${sign}${v}`;
    })
    .join(', ');
}

export function fmtEffort(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

export function fmtSecs(s) {
  if (s == null || s < 0) return '—';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}
