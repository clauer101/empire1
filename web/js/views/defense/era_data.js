/**
 * Pure era/tower data constants and the era-stats HTML builder.
 * No shared state — safe to import from anywhere.
 */

export const _TOWER_ERA = {
  BASIC_TOWER: 'Stone Age',
  SLING_TOWER: 'Stone Age',
  DOUBLE_SLING_TOWER: 'Neolith.',
  SPIKE_TRAP: 'Neolith.',
  ARROW_TOWER: 'Bronze',
  BALLISTA_TOWER: 'Bronze',
  FIRE_TOWER: 'Bronze',
  CATAPULTS: 'Iron Age',
  ARBELESTE_TOWER: 'Iron Age',
  TAR_TOWER: 'Medieval',
  HEAVY_TOWER: 'Medieval',
  BOILING_OIL: 'Medieval',
  CANNON_TOWER: 'Renaissance',
  RIFLE_TOWER: 'Renaissance',
  COLD_TOWER: 'Renaissance',
  ICE_TOWER: 'Renaissance',
  FLAME_THROWER: 'Industrial',
  SHOCK_TOWER: 'Industrial',
  PARALYZNG_TOWER: 'Industrial',
  GATLING_TOWER: 'Industrial',
  NAPALM_THROWER: 'Modern',
  MG_TOWER: 'Modern',
  RAPID_FIRE_MG_BUNKER: 'Modern',
  RADAR_TOWER: 'Modern',
  ANTI_AIR_TOWER: 'Modern',
  LASER_TOWER: 'Modern',
  SNIPER_TOWER: 'Future',
  ROCKET_TOWER: 'Future',
};

export const _ERA_COLORS = {
  'Stone Age': '#8B7355',
  'Neolith.': '#A0887A',
  Bronze: '#CD7F32',
  'Iron Age': '#888888',
  Medieval: '#6B8A8A',
  Renaissance: '#8B6914',
  Industrial: '#FF6B35',
  Modern: '#4B9CD3',
  Future: '#9B59B6',
};

export const _ERA_ORDER_STAT = [
  'Stone Age',
  'Neolith.',
  'Bronze',
  'Iron Age',
  'Medieval',
  'Renaissance',
  'Industrial',
  'Modern',
  'Future',
];

export const _NON_TOWER = new Set(['castle', 'spawnpoint', 'path', 'empty', 'void', '']);

export const _ERA_CASTLE_SPRITES = {
  stone: '/assets/sprites/bases/base_stone.webp',
  neolithic: '/assets/sprites/bases/base_neolithicum.webp',
  bronze: '/assets/sprites/bases/base_bronze.webp',
  iron: '/assets/sprites/bases/base_iron.webp',
  middle_ages: '/assets/sprites/bases/base_middle_ages.webp',
  renaissance: '/assets/sprites/bases/base_renaissance.webp',
  industrial: '/assets/sprites/bases/base_industrial.webp',
  modern: '/assets/sprites/bases/base_modern.webp',
  future: '/assets/sprites/bases/base_future.webp',
};

export const _ROMAN_NUMERALS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'];

export const STRUCTURE_COLORS = [
  { color: '#3a5a4a', stroke: '#4a7a5a' },
  { color: '#4a4a6a', stroke: '#5a5a8a' },
  { color: '#5a3a3a', stroke: '#7a4a4a' },
  { color: '#3a4a5a', stroke: '#4a6a7a' },
  { color: '#5a4a3a', stroke: '#7a6a4a' },
  { color: '#4a5a4a', stroke: '#6a7a6a' },
];

export function _buildEraStatsHTML(tiles) {
  if (!tiles) return '';
  const towers = tiles.filter((t) => !_NON_TOWER.has(t.type));
  if (!towers.length)
    return '<div style="color:var(--text-dim);font-size:11px;padding:4px 0;">No towers placed</div>';
  const byEra = {};
  for (const t of towers) {
    const era = _TOWER_ERA[t.type] || '?';
    byEra[era] = (byEra[era] || 0) + 1;
  }
  const total = Object.values(byEra).reduce((a, b) => a + b, 0);
  const maxCount = Math.max(1, ...Object.values(byEra));
  const rows = _ERA_ORDER_STAT
    .filter((era) => byEra[era])
    .map((era) => {
      const cnt = byEra[era];
      const barPct = Math.round((cnt / maxCount) * 100);
      const pct = Math.round((cnt / total) * 100);
      const col = _ERA_COLORS[era] || '#888';
      return `<div class="age-row">
        <span class="age-name">${era}</span>
        <div class="age-bar-outer"><div class="age-bar-inner" style="width:${barPct}%;background:${col}"></div></div>
        <span class="age-pct">${pct}%</span>
        <span style="color:var(--text-dim);font-size:10px;font-family:monospace">${cnt}×</span>
      </div>`;
    })
    .join('');
  return `<div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">${towers.length} towers total</div><div class="age-bars">${rows}</div>`;
}
