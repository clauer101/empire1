/**
 * Shared formatting utilities.
 *
 * Effect helpers (all effects go through here — do not inline elsewhere):
 *   formatEffect(key, value)     → long-form string with description: "Increases gold (+3.6/h)"
 *   fmtEffectRow(key, value)     → HTML "<span>icon label:</span><span>+value</span>" for two-column display
 *   fmtEffectsInline(effects)    → compact comma-separated string, e.g. "💰 +3.6/h, 🎭 +5%"
 *   fmtTowerEffects(effects)     → tower combat effects: burn / slow / splash
 *   fmtEffectLabel(key)          → "💰 Gold income"
 *   fmtEffectValue(key, value)   → "+3.6/h"
 */

// Per-effect display metadata: [icon, label, valueFn, description]
const EFFECT_META = {
  gold_offset:                    ['💰', 'Gold income',              (v) => `${v > 0 ? '+' : ''}${(v * 3600).toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`, 'Increases gold production by a fixed amount'],
  gold_modifier:                  ['💰', 'Gold bonus',               (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases gold production by a multiplier'],
  culture_offset:                 ['🎭', 'Culture income',           (v) => `${v > 0 ? '+' : ''}${(v * 3600).toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`, 'Increases culture production by a fixed amount'],
  culture_modifier:               ['🎭', 'Culture bonus',            (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases culture production by a multiplier'],
  life_regen_modifier:            ['❤️', 'Life regen',               (v) => `${v > 0 ? '+' : ''}${(v * 3600).toFixed(1)}/h`,                                            'Increases life energy regeneration'],
  max_life_modifier:              ['❤️', 'Max life',                 (v) => `${v > 0 ? '+' : ''}${v}`,                                                                  'Increases maximum life'],
  restore_life_after_loss_offset: ['❤️', 'Life restore',             (v) => `${v > 0 ? '+' : ''}${v}`,                                                                  'Restores life after a lost battle'],
  build_speed_modifier:           ['🏗',  'Build speed',             (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                               'Accelerates building construction by a multiplier'],
  build_speed_offset:             ['🏗',  'Build speed',             (v) => `${v > 0 ? '+' : ''}${(v * 3600).toFixed(1)}/h`,                                             'Accelerates building construction by a fixed amount'],
  research_speed_modifier:        ['🔬', 'Research speed',           (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Accelerates research by a multiplier'],
  research_speed_offset:          ['🔬', 'Research speed',           (v) => `${v > 0 ? '+' : ''}${(v * 3600).toFixed(1)}/h`,                                            'Accelerates research by a fixed amount'],
  research_cost_modifier:         ['🔬', 'Research cost',            (v) => `-${(v * 100).toFixed(0)}%`,                                                                'Reduces the effort cost of each research'],
  scientist_citizen_bonus:        ['🔭', 'Scientist bonus',          (v) => `×${(1 + v).toFixed(1)} per scientist`,                                                     'Increases the research speed bonus per scientist citizen'],
  gold_lump_sum_after_research:   ['💰', 'Research reward',          (v) => `+${v.toLocaleString('de-DE')} gold`,                                                       'Grants a one-time gold bonus each time a research is completed'],
  workshop_cost_modifier:         ['🔧', 'Workshop discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                                'Reduces the gold cost of workshop item upgrades'],
  travel_time_modifier:           ['🚀', 'Travel speed',             (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Reduces travel time of armies by a percentage'],
  travel_offset:                  ['🚀', 'Travel time',              (v) => `${v > 0 ? '+' : ''}${v}s`,                                                                 'Modifies travel time of armies'],
  siege_offset:                   ['⚔️', 'Siege time',               (v) => `${v > 0 ? '+' : ''}${v}s`,                                                                 'Modifies siege time of armies'],
  siege_time_modifier:            ['⚔️', 'Siege speed',              (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Accelerates siege by a multiplier'],
  wave_delay_offset:              ['⏳', 'Wave delay',               (v) => `${v > 0 ? '+' : ''}${v}s`,                                                                 'Increases delay between incoming waves'],
  artifact_steal_victory_modifier:['⚜',  'Artifact steal (victory)', (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases artifact steal chance on victory'],
  artifact_steal_defeat_modifier: ['⚜',  'Artifact steal (defeat)',  (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases artifact steal chance on defeat'],
  tower_sell_refund_modifier:     ['💰', 'Tower refund',             (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases tower sell refund'],
  spy_workshop:                   ['🕵️', 'Workshop intel',           () => 'Unlocked',                                                                                  'Unlocks workshop intelligence in spy reports'],
  ruler_unlock:                   ['👑', 'Ruler',                    () => 'Unlocked',                                                                                  'Assign a powerful ruler to your empire'],
  // -- Cost modifiers
  citizen_cost_modifier:          ['🫂', 'Citizen discount',         (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the culture cost of acquiring new citizens'],
  tile_cost_modifier:             ['🗺️', 'Land discount',            (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of acquiring new land tiles'],
  building_cost_modifier:         ['🏗',  'Building discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of constructing buildings'],
  wave_cost_modifier:             ['⚔️', 'Wave discount',            (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of adding new waves to armies'],
  wave_era_cost_modifier:         ['⚔️', 'Wave era discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of upgrading wave era'],
  wave_slot_cost_modifier:        ['⚔️', 'Wave slot discount',       (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of purchasing additional critter slots'],
  // -- Citizen modifiers
  citizen_effect_modifier:        ['🫂', 'Citizen efficiency',       (v) => `+${(v * 100).toFixed(0)}%`,                                                               'Adds to the productivity bonus of each citizen'],
  other_citizen_gold_modifier:    ['💰', 'Artist/Scientist gold',    (v) => `+${(v * 100).toFixed(0)}% per citizen`,                                                  'Artists and scientists also contribute to gold income'],
  // -- One-shot lump sums (shown in ruler skill tooltips only)
  gold_lump_sum_on_skill_up:      ['💰', 'Skill-up gold reward',     (v) => `+${v.toLocaleString('de-DE')} gold`,                                                     'Grants a one-time gold bonus when this skill level is reached'],
  culture_lump_sum_on_skill_up:   ['🎭', 'Skill-up culture reward',  (v) => `+${v.toLocaleString('de-DE')} culture`,                                                  'Grants a one-time culture bonus when this skill level is reached'],
  // -- Combat
  restore_life_during_battle_modifier: ['❤️', 'Battle life regen',   (v) => `+${v}/s`,                                                                              'Adds to life regeneration while actively defending against an attack'],
  enemy_siege_time_modifier:      ['⚔️', 'Siege corruption',         (v) => `-${(v * 100).toFixed(0)}% enemy siege`,                                                  'Reduces the siege duration of your own attacks'],
};

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

function _fallback(k, v) {
  const sign = v > 0 ? '+' : '';
  const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const val = Math.abs(v) < 1 ? `${sign}${(v * 100).toFixed(0)}%` : `${sign}${v}`;
  return [null, label, val];
}

/** Long-form string with description and formatted value, e.g. "Increases gold production (+3.6/h)" */
export function formatEffect(key, value) {
  const meta = EFFECT_META[key];
  if (meta) {
    const desc = meta[3] || meta[1];
    // siege/travel offsets use duration formatting
    if (key === 'siege_offset' || key === 'travel_offset') {
      return `${desc} (${_fmtDuration(value)})`;
    }
    return `${desc} (${meta[2](value)})`;
  }
  const sign = value > 0 ? '+' : '';
  const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const val = Math.abs(value) < 1 ? `${sign}${(value * 100).toFixed(0)}%` : `${sign}${value}`;
  return `${label} (${val})`;
}

/** Formatted value string for an effect key, e.g. "+10.8/h". */
export function fmtEffectValue(key, value) {
  const meta = EFFECT_META[key];
  if (meta) return meta[2](value);
  const [,, val] = _fallback(key, value);
  return val;
}

/** Formatted label with icon for an effect key, e.g. "❤️ Life regen". */
export function fmtEffectLabel(key) {
  const meta = EFFECT_META[key];
  if (meta) return `${meta[0]} ${meta[1]}`;
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
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
