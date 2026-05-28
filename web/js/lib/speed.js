/**
 * Shared speed calculation helpers for build and research durations.
 *
 * Single source of truth for the formulas used by buildings.js, research.js,
 * and status.js.  Must stay in sync with empire_service._progress_buildings /
 * _progress_knowledge on the server.
 *
 * Build:    speed = (base + offset) * (1 + modifier) * (1 - siege_penalty)
 * Research: speed = (base + offset) * (1 + modifier + scientists * citizen_effect)
 */

/**
 * @param {object} summary  Empire summary from the API.
 *   If summary.attacks_incoming is present, the siege construction penalty is
 *   applied automatically (mirrors empire_service._siege_construction_speed_penalty).
 * @returns {number}  Build speed in effort-units per second (> 0)
 */
export function calcBuildSpeed(summary) {
  const base = summary.base_build_speed ?? 1;
  const offset = summary.effects?.build_speed_offset || 0;
  const modifier = summary.effects?.build_speed_modifier || 0;
  let speed = (base + offset) * (1 + modifier);

  // Apply siege construction penalty (mirrors server-side logic)
  const siegeCount = (summary.attacks_incoming || []).filter((a) => a.phase === 'in_siege').length;
  if (siegeCount > 0) {
    const baseSiegePerArmy = summary.base_siege_construction_speed_per_army_modifier ?? 0.05;
    const resilienceModifier = summary.effects?.siege_construction_speed_per_army_modifier || 0;
    const effectivePerArmy = Math.max(0, baseSiegePerArmy - resilienceModifier);
    const maxCap = summary.effects?.max_siege_construction_speed_modifier || 0;
    const rawPenalty = siegeCount * effectivePerArmy;
    const penalty = maxCap > 0 ? Math.min(rawPenalty, maxCap) : rawPenalty;
    speed *= (1 - penalty);
  }

  return speed;
}

/**
 * @param {object} summary  Empire summary from the API
 * @returns {number}  Research speed in effort-units per second (> 0)
 */
export function calcResearchSpeed(summary) {
  const base = summary.base_research_speed ?? 1;
  const offset = summary.effects?.research_speed_offset || 0;
  const modifier = summary.effects?.research_speed_modifier || 0;
  const scientistCitizenBonus = 1 + (summary.effects?.scientist_citizen_bonus || 0);
  const scientistBonus = (summary.citizens?.scientist || 0) * (summary.citizen_effect || 0) * scientistCitizenBonus;
  return (base + offset) * (1 + modifier + scientistBonus);
}
