/**
 * Shared speed calculation helpers for build and research durations.
 *
 * Single source of truth for the formulas used by buildings.js, research.js,
 * and status.js.  Must stay in sync with empire_service._progress_buildings /
 * _progress_knowledge on the server.
 *
 * Build:    speed = (base + offset) * (1 + modifier)
 * Research: speed = (base + offset) * (1 + modifier + scientists * citizen_effect)
 */

/**
 * @param {object} summary  Empire summary from the API
 * @returns {number}  Build speed in effort-units per second (> 0)
 */
export function calcBuildSpeed(summary) {
  const base = summary.base_build_speed ?? 1;
  const offset = summary.effects?.build_speed_offset || 0;
  const modifier = summary.effects?.build_speed_modifier || 0;
  return (base + offset) * (1 + modifier);
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
