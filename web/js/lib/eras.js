/**
 * Shared era constants — single source of truth for frontend era data.
 */

export const ERA_ROMAN = {
  STEINZEIT: 'I', NEOLITHIKUM: 'II', BRONZEZEIT: 'III', EISENZEIT: 'IV',
  MITTELALTER: 'V', RENAISSANCE: 'VI', INDUSTRIALISIERUNG: 'VII',
  MODERNE: 'VIII', ZUKUNFT: 'IX',
};

export const ERA_LABEL_EN = {
  STEINZEIT: 'Stone Age', NEOLITHIKUM: 'Neolithic', BRONZEZEIT: 'Bronze Age',
  EISENZEIT: 'Iron Age', MITTELALTER: 'Middle Ages', RENAISSANCE: 'Renaissance',
  INDUSTRIALISIERUNG: 'Industrial Age', MODERNE: 'Modern Age', ZUKUNFT: 'Future',
};

/** Ordered era keys (matches server ERA_ORDER). */
export const ERA_KEYS = [
  'STEINZEIT', 'NEOLITHIKUM', 'BRONZEZEIT', 'EISENZEIT',
  'MITTELALTER', 'RENAISSANCE', 'INDUSTRIALISIERUNG', 'MODERNE', 'ZUKUNFT',
];

/** Map from item era field value (English snake_case) to canonical era key. */
export const ERA_YAML_TO_KEY = {
  'STONE_AGE':    'STEINZEIT',
  'NEOLITHIC':    'NEOLITHIKUM',
  'BRONZE_AGE':   'BRONZEZEIT',
  'IRON_AGE':     'EISENZEIT',
  'MEDIEVAL':     'MITTELALTER',
  'RENAISSANCE':  'RENAISSANCE',
  'INDUSTRIAL':   'INDUSTRIALISIERUNG',
  'MODERN':       'MODERNE',
  'FUTURE':       'ZUKUNFT',
};

export const ERA_SPRITE_KEY = {
  STEINZEIT: 'stone', NEOLITHIKUM: 'neolithicum', BRONZEZEIT: 'bronze',
  EISENZEIT: 'iron', MITTELALTER: 'middle_ages', RENAISSANCE: 'renaissance',
  INDUSTRIALISIERUNG: 'industrial', MODERNE: 'modern', ZUKUNFT: 'future',
};
