/**
 * Shared era constants — single source of truth for frontend era data.
 */

export const ERA_ROMAN = {
  stone: 'I', neolithic: 'II', bronze: 'III', iron: 'IV',
  middle_ages: 'V', renaissance: 'VI', industrial: 'VII',
  modern: 'VIII', future: 'IX',
};

export const ERA_LABEL_EN = {
  stone: 'Stone Age', neolithic: 'Neolithic', bronze: 'Bronze Age',
  iron: 'Iron Age', middle_ages: 'Middle Ages', renaissance: 'Renaissance',
  industrial: 'Industrial Age', modern: 'Modern Age', future: 'Future',
};

/** Ordered era keys (lowercase English, matches server ERA_ORDER). */
export const ERA_KEYS = [
  'stone', 'neolithic', 'bronze', 'iron',
  'middle_ages', 'renaissance', 'industrial', 'modern', 'future',
];

/** Identity map — era keys are already canonical. */
export const ERA_YAML_TO_KEY = {
  stone: 'stone', neolithic: 'neolithic', bronze: 'bronze', iron: 'iron',
  middle_ages: 'middle_ages', renaissance: 'renaissance',
  industrial: 'industrial', modern: 'modern', future: 'future',
};

export const ERA_SPRITE_KEY = {
  stone: 'stone', neolithic: 'neolithic', bronze: 'bronze',
  iron: 'iron', middle_ages: 'middle_ages', renaissance: 'renaissance',
  industrial: 'industrial', modern: 'modern', future: 'future',
};
