/**
 * Pure era/tower data constants and the era-stats HTML builder.
 * No shared state — safe to import from anywhere.
 */

import { ERA_KEYS, ERA_LABEL_EN } from '../../lib/eras.js';

// Colors keyed by canonical lowercase era key (matches structures.yaml `era:`)
export const _ERA_COLORS = {
  stone: '#8B7355',
  neolithic: '#A0887A',
  bronze: '#CD7F32',
  iron: '#888888',
  medieval: '#6B8A8A',
  renaissance: '#8B6914',
  industrial: '#FF6B35',
  modern: '#4B9CD3',
  future: '#9B59B6',
};

export const _NON_TOWER = new Set(['castle', 'spawnpoint', 'path', 'empty', 'void', '']);

export const _ERA_CASTLE_SPRITES = {
  stone: '/assets/sprites/bases/base_stone.webp',
  neolithic: '/assets/sprites/bases/base_neolithicum.webp',
  bronze: '/assets/sprites/bases/base_bronze.webp',
  iron: '/assets/sprites/bases/base_iron.webp',
  medieval: '/assets/sprites/bases/base_medieval.webp',
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

export function _buildEraStatsHTML(tiles, pathLength, catalog) {
  if (!tiles) return '';
  const pathRow = pathLength != null
    ? `<div style="font-size:11px;color:var(--text-dim);margin-bottom:6px;">Path length: <span style="color:var(--text);font-family:monospace">${pathLength} tiles</span></div>`
    : '';
  const towers = tiles.filter((t) => !_NON_TOWER.has(t.type));
  if (!towers.length)
    return pathRow + '<div style="color:var(--text-dim);font-size:11px;padding:4px 0;">No towers placed</div>';
  // Era per tower comes from the item catalog (structures.yaml `era:` field)
  const cat = catalog || {};
  const byEra = {};
  for (const t of towers) {
    const era = cat[t.type]?.era || '?';
    byEra[era] = (byEra[era] || 0) + 1;
  }
  const total = Object.values(byEra).reduce((a, b) => a + b, 0);
  const maxCount = Math.max(1, ...Object.values(byEra));
  const rows = [...ERA_KEYS, '?']
    .filter((era) => byEra[era])
    .map((era) => {
      const cnt = byEra[era];
      const barPct = Math.round((cnt / maxCount) * 100);
      const pct = Math.round((cnt / total) * 100);
      const col = _ERA_COLORS[era] || '#888';
      return `<div class="age-row">
        <span class="age-name">${ERA_LABEL_EN[era] || era}</span>
        <div class="age-bar-outer"><div class="age-bar-inner" style="width:${barPct}%;background:${col}"></div></div>
        <span class="age-pct">${pct}%</span>
        <span style="color:var(--text-dim);font-size:10px;font-family:monospace">${cnt}×</span>
      </div>`;
    })
    .join('');
  return pathRow + `<div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">${towers.length} towers total</div><div class="age-bars">${rows}</div>`;
}
