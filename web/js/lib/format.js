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
  research_effort_modifier:       ['🔬', 'Research effort',          (v) => `-${(v * 100).toFixed(0)}%`,                                                                'Reduces the required effort of each research'],
  scientist_citizen_bonus:        ['🔭', 'Scientist bonus',          (v) => `×${(1 + v).toFixed(1)} per scientist`,                                                     'Increases the research speed bonus per scientist citizen'],
  gold_lump_sum_after_research:   ['💰', 'Research reward',          (v) => `+${v.toLocaleString('de-DE')} gold`,                                                       'Grants a one-time gold bonus each time a research is completed'],
  workshop_cost_modifier:         ['🔧', 'Workshop discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                                'Reduces the gold cost of workshop item upgrades'],
  travel_time_modifier:           ['🚀', 'Travel speed',             (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Reduces travel time of armies by a percentage'],
  travel_offset:                  ['🚀', 'Travel time',              (v) => `${v > 0 ? '+' : ''}${v}s`,                                                                 'Modifies travel time of armies'],
  siege_offset:                   ['⚔️', 'Siege time',               (v) => `${v > 0 ? '+' : ''}${(v / 3600).toFixed(1)}h`,                                          'Modifies siege time of armies'],
  siege_time_modifier:            ['⚔️', 'Siege speed',              (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Accelerates siege by a multiplier'],
  wave_delay_offset:              ['⏳', 'Wave delay',               (v) => `${v > 0 ? '+' : ''}${(v / 1000).toFixed(1)}s`,                                          'Increases delay between incoming waves'],
  artifact_steal_victory_modifier:['⚜',  'Max. Artifact steal (victory)', (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases artifact maximum steal chance on victory'],
  artifact_steal_defeat_modifier: ['⚜',  'Max. Artifact steal (defeat)',  (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases artifact maximum steal chance on defeat'],
  tower_sell_refund_modifier:     ['💰', 'Tower refund',             (v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`,                                              'Increases tower sell refund'],
  spy_workshop:                   ['🕵️', 'Workshop intel',           () => 'Unlocked',                                                                                  'Unlocks workshop intelligence in spy reports'],
  spy_artifacts:                  ['🕵️', 'Artifact intel',           () => 'Unlocked',                                                                                  'Unlocks the artifact list in spy reports'],
  spy_ruler:                      ['🕵️', 'Ruler intel',              () => 'Unlocked',                                                                                  'Unlocks ruler information in spy reports'],
  spy_queues:                     ['🕵️', 'Queue intel',              () => 'Unlocked',                                                                                  'Reveals the target\'s current build and research queue in spy reports'],
  ruler_unlock:                   ['👑', 'Ruler',                    () => 'Unlocked',                                                                                  'Assign a powerful ruler to your empire'],
  enable_army:                    ['⚔',  'Army',                     () => 'Unlocked',                                                                                  'Unlocks the Army view to compose and send attack waves'],
  enable_techtree:                ['⬡',  'Tech Tree',                () => 'Unlocked',                                                                                  'Unlocks the Tech Tree view for advanced research'],
  enable_workshop:                ['⚙',  'Workshop',                 () => 'Unlocked',                                                                                  'Unlocks the Workshop view for tower and critter upgrades'],
  enable_messages:                ['✉',  'Messages',                 () => 'Unlocked',                                                                                  'Unlocks the Messages view for battle reports'],
  // -- Cost modifiers
  citizen_cost_modifier:          ['🫂', 'Citizen discount',         (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the culture cost of acquiring new citizens'],
  tile_cost_modifier:             ['🗺️', 'Land discount',            (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of acquiring new land tiles'],
  building_cost_modifier:         ['🏗',  'Building discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of constructing buildings'],
  wave_cost_modifier:             ['⚔️', 'Wave discount',            (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of adding new waves to armies'],
  wave_era_cost_modifier:         ['⚔️', 'Wave era discount',        (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of upgrading wave era'],
  wave_slot_cost_modifier:        ['⚔️', 'Wave slot discount',       (v) => `-${(v * 100).toFixed(0)}%`,                                                               'Reduces the gold cost of purchasing additional critter slots'],
  // -- Citizen modifiers
  citizen_effect_modifier:        ['🫂', 'Citizen efficiency',       (v) => `+${(v * 100).toFixed(1)}%`,                                                               'Adds to the productivity bonus of each citizen'],
  other_citizen_gold_modifier:    ['💰', 'Artist/Scientist gold',    (v) => `+${(v * 100).toFixed(1)}% per citizen`,                                                  'Artists and scientists also contribute to gold income'],
  critter_gold_modifier:          ['🐜', 'Critter gold bonus',       (v) => `+${(v * 100).toFixed(0)}%`,                                                               'Grants bonus gold when critters are defeated, proportional to gold earned this battle'],
  increase_start_gold:            ['💰', 'Starting gold',   (v) => `+${v.toLocaleString('de-DE')} gold`,                                                       'Grants extra gold when respawning after season restart'],
  // -- One-shot lump sums (shown in ruler skill tooltips only)
  gold_lump_sum_on_skill_up:      ['💰', 'Skill-up gold reward',     (v) => `+${v.toLocaleString('de-DE')} gold`,                                                     'Grants a one-time gold bonus when this skill level is reached'],
  culture_lump_sum_on_skill_up:   ['🎭', 'Skill-up culture reward',  (v) => `+${v.toLocaleString('de-DE')} culture`,                                                  'Grants a one-time culture bonus when this skill level is reached'],
  // -- Ruler aura effects
  increase_armour_modifier:       ['🛡', 'Aura: Armour boost',   (v) => `+${(v * 100).toFixed(0)}% armour`,                                                           'Boosts armour of nearby friendly critters'],
  increase_critter_speed:         ['⚡', 'Aura: Speed boost',    (v) => `+${(v * 100).toFixed(0)}% speed`,                                                           'Boosts speed of nearby friendly critters'],
  slow_tower_modifier:            ['❄', 'Aura: Tower slow',      (v) => `-${(v * 100).toFixed(0)}% reload`,                                                    'Slows reload speed of nearby enemy towers'],
  reduce_tower_damage:            ['💢', 'Aura: Tower damage',   (v) => `-${(v * 100).toFixed(0)}% damage`,                                                    'Reduces damage of nearby enemy towers'],
  artifact_retention_time:            ['⚜',  'Artifact protection',      (v) => `${Math.round(v / 3600)}h`,                                                           'Newly acquired artifacts cannot be stolen for this duration'],
  // -- Combat
  restore_life_during_battle_modifier: ['❤️', 'Battle life regen',   (v) => `+${v}/s`,                                                                              'Adds to life regeneration while in battle'],
  enemy_siege_time_modifier:      ['⚔️', 'Siege corruption',         (v) => `-${(v * 100).toFixed(0)}% enemy siege`,                                                  'Reduces the siege duration of your own attacks'],
  max_siege_construction_speed_modifier:      ['🏗', 'Max siege disruption', (v) => `${(v * 100).toFixed(0)}% build speed`,   'Maximum construction speed reduction during siege'],
  siege_construction_speed_per_army_modifier: ['🏗', 'Siege resilience',    (v) => `-${(v * 100).toFixed(0)}% per army`,        'Reduces the construction speed penalty per besieging army'],
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
export function fmtEffectsInline(effects, { labeled = false } = {}) {
  if (!effects || Object.keys(effects).length === 0) return '';
  return Object.entries(effects)
    .map(([k, v]) => {
      const meta = EFFECT_META[k];
      if (meta) return labeled ? `${meta[0]} ${meta[1]}: ${meta[2](v)}` : `${meta[0]} ${meta[2](v)}`;
      const [, label, val] = _fallback(k, v);
      return `${label}: ${val}`;
    })
    .join(', ');
}

// Trophy condition display metadata: {type → [icon, labelFn(threshold, condition)]}
export const CONDITION_META = {
  // Legacy combined counters
  defense_won:     ['🛡', (t) => `Defend successfully ${t} time${t !== 1 ? 's' : ''}`],
  attacks_won:     ['⚔️', (t) => `Win ${t} attack${t !== 1 ? 's' : ''}`],
  critters_killed: ['💀', (t) => `Kill ${t} enemy critters`],
  hexes_owned:     ['🗺️', (t) => `Own ${t} hex tiles at once`],
  // Per-type win/loss
  defense_won_ai:    ['🛡', (t) => `Defend ${t} time${t !== 1 ? 's' : ''} vs AI`],
  defense_won_human: ['🛡', (t) => `Defend ${t} time${t !== 1 ? 's' : ''} vs human`],
  attacks_won_ai:    ['⚔️', (t) => `Win ${t} attack${t !== 1 ? 's' : ''} vs AI`],
  attacks_won_human: ['⚔️', (t) => `Win ${t} attack${t !== 1 ? 's' : ''} vs human`],
  // Cowardice / punching up
  coward_attacks:           ['🐔', (t) => `Attack below your own era ${t} time${t !== 1 ? 's' : ''} in a season`],
  max_lucky_punch_levels:   ['🍀', (t) => `Beat a defender ${t} era${t !== 1 ? 's' : ''} above you`],
  // Espionage
  spies_sent:      ['🔍', (t) => `Send ${t} spy mission${t !== 1 ? 's' : ''} in a season`],
  // Loot
  artifacts_stolen:               ['⚜', (t) => `Steal ${t} artifact${t !== 1 ? 's' : ''} in a season`],
  max_artifacts_stolen_one_battle:['⚜', (t) => `Steal ${t}+ artifacts in a single battle`],
  max_artifacts_lost_one_battle:  ['😱', (t) => `Lose ${t}+ artifacts in a single battle`],
  culture_won:     ['🎭', (t) => `Win ${t} culture in a season`],
  culture_stolen:  ['🎭', (t) => `Lose ${t} culture to raiders in a season`],
  research_won:    ['📖', (t) => `Win ${t} research in a season`],
  research_stolen: ['📖', (t) => `Lose ${t} research to raiders in a season`],
  longest_battle_ms:        ['⏱', (t) => `Survive a battle lasting ${Math.round(t / 1000)}s`],
  one_hp_def_wins:          ['❤️', (t) => `Win ${t > 1 ? t + ' defenses' : 'a defense'} with 1 HP remaining`],
  // Map / path
  path_length: ['🗺️', (t) => `Build a maze with ${t}+ path tiles`],
  // Ruler
  ruler_level: ['👑', (t) => `Reach ruler level ${t}`],
  // Era firsts (condition carries an `era` field)
  first_in_era: ['🏅', (t, c) => {
    const ERA_LABEL_EN = {
      stone: 'Stone Age', neolithic: 'Neolithic', bronze: 'Bronze Age',
      iron: 'Iron Age', medieval: 'Medieval', renaissance: 'Renaissance',
      industrial: 'Industrial Age', modern: 'Modern Age', future: 'Future',
    };
    return `First to reach the ${ERA_LABEL_EN[c?.era] ?? c?.era ?? '?'}`;
  }],
  // Meta
  all_era_firsts: ['🌟', () => 'Earn all "First in Era" trophies'],
  all_trophies:   ['🏆', () => 'Earn every other trophy'],
};

/** Format a trophy's current/target progress as a compact fraction, e.g. "37 / 50". */
export function fmtTrophyProgress(current, target) {
  if (target == null) return '';
  const fmt = (v) => (Number.isInteger(v) ? v : v.toFixed(1));
  return `${fmt(current ?? 0)} / ${fmt(target)}`;
}

/** Format a trophy condition object → human-readable string. */
export function fmtTrophyCondition(condition) {
  if (!condition?.type) return '—';
  const meta = CONDITION_META[condition.type];
  const t = condition.threshold ?? 1;
  if (meta) return `${meta[0]} ${meta[1](t, condition)}`;
  return condition.type;
}

/** Alliance/diplomacy relationship status → {label, badgeClass} for the Empire Details page. */
export function fmtAllianceStatus(status) {
  switch (status) {
    case 'allied':           return { label: '🤝 Allied',           badgeClass: 'badge--completed' };
    case 'pending_sent':     return { label: '💬 Request Sent',     badgeClass: 'badge--in-progress' };
    case 'pending_received': return { label: '💬 Request Received', badgeClass: 'badge--available' };
    default:                 return { label: '💬 Diplomacy',        badgeClass: 'badge--available' };
  }
}

/**
 * Fixed-size square action button style for empire leaderboard rows
 * (⚔ attack / 🏰 detail buttons in status.js and globalempires.js).
 * A shared fixed box (not padding-based) keeps both buttons the exact same
 * size regardless of the visual width of the glyph/emoji inside, and
 * regardless of whether the element is a <button> or an <a>.
 */
export const EMPIRE_ROW_ACTION_BTN_STYLE =
  'font-size:11px;font-family:inherit;line-height:1;margin:0;padding:0;' +
  'width:24px;height:24px;box-sizing:border-box;box-shadow:none;color:#fff;' +
  'text-decoration:none;display:inline-flex;align-items:center;justify-content:center;' +
  'border-radius:var(--radius,4px);';

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

/** Format a resource value: 3–4 significant digits, floor, integer life. */
export function fmtRes(value) {
  const v = Math.floor(value ?? 0);
  if (v >= 1_000_000) {
    const d = v / 1_000_000;
    return (d >= 100 ? Math.floor(d) : d >= 10 ? d.toFixed(1) : d.toFixed(2)) + 'M';
  }
  if (v >= 1_000) {
    const d = v / 1_000;
    return (d >= 100 ? Math.floor(d) : d >= 10 ? d.toFixed(1) : d.toFixed(2)) + 'k';
  }
  return String(v);
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

export function showIconLegend() {
  document.querySelector('.icon-legend-overlay')?.remove();
  const ov = document.createElement('div');
  ov.className = 'icon-legend-overlay tt-overlay visible';
  ov.innerHTML = `
    <div class="tt-panel">
      <button class="tt-close">&times;</button>
      <div class="tt-dp-name">Player Icons</div>
      <div class="tt-dp-desc" style="margin-top:10px;font-style:normal;line-height:1.9;font-size:0.92em">
        <div>🥇🥈🥉 &nbsp;Top 3 of the <strong>last season</strong></div>
        <div>🎖️ &nbsp;Winner of a <strong>past season</strong></div>
        <div>🤖 &nbsp;AI-controlled empire</div>
        <div>⚜ &nbsp;Artifact — a powerful item that can be conquered from other empires</div>
        <div><span style="color:#4fc3f7;text-shadow:0 0 8px #4fc3f7;">⚜</span> &nbsp;Artifact with <strong>steal protection</strong> — cannot currently be conquered</div>
      </div>
    </div>`;
  ov.addEventListener('click', e => {
    if (e.target === ov || e.target.classList.contains('tt-close')) ov.remove();
  });
  document.body.appendChild(ov);
}
