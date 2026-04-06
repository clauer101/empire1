/**
 * Tests for lib/eras.js — era constants integrity
 * Run with: node tests/test_eras.test.js
 */

import { ERA_ROMAN, ERA_LABEL_EN, ERA_SPRITE_KEY } from '../js/lib/eras.js';

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); console.log(`✓ ${name}`); passed++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); failed++; }
}
function eq(a, b) { if (a !== b) throw new Error(`Expected "${b}", got "${a}"`); }

const ERAS = [
  'STEINZEIT', 'NEOLITHIKUM', 'BRONZEZEIT', 'EISENZEIT',
  'MITTELALTER', 'RENAISSANCE', 'INDUSTRIALISIERUNG', 'MODERNE', 'ZUKUNFT'
];

// ── ERA_ROMAN ────────────────────────────────────────────────────────────────

test('ERA_ROMAN: has 9 entries', () => eq(Object.keys(ERA_ROMAN).length, 9));
test('ERA_ROMAN: covers all eras', () => {
  for (const era of ERAS) {
    if (!(era in ERA_ROMAN)) throw new Error(`Missing ${era}`);
  }
});
test('ERA_ROMAN: STEINZEIT → I', () => eq(ERA_ROMAN.STEINZEIT, 'I'));
test('ERA_ROMAN: ZUKUNFT → IX', () => eq(ERA_ROMAN.ZUKUNFT, 'IX'));

// ── ERA_LABEL_EN ─────────────────────────────────────────────────────────────

test('ERA_LABEL_EN: has 9 entries', () => eq(Object.keys(ERA_LABEL_EN).length, 9));
test('ERA_LABEL_EN: covers all eras', () => {
  for (const era of ERAS) {
    if (!(era in ERA_LABEL_EN)) throw new Error(`Missing ${era}`);
    if (!ERA_LABEL_EN[era]) throw new Error(`Empty label for ${era}`);
  }
});
test('ERA_LABEL_EN: STEINZEIT → Stone Age', () => eq(ERA_LABEL_EN.STEINZEIT, 'Stone Age'));

// ── ERA_SPRITE_KEY ───────────────────────────────────────────────────────────

test('ERA_SPRITE_KEY: has 9 entries', () => eq(Object.keys(ERA_SPRITE_KEY).length, 9));
test('ERA_SPRITE_KEY: covers all eras', () => {
  for (const era of ERAS) {
    if (!(era in ERA_SPRITE_KEY)) throw new Error(`Missing ${era}`);
  }
});
test('ERA_SPRITE_KEY: STEINZEIT → stone', () => eq(ERA_SPRITE_KEY.STEINZEIT, 'stone'));
test('ERA_SPRITE_KEY: ZUKUNFT → future', () => eq(ERA_SPRITE_KEY.ZUKUNFT, 'future'));

// ── Cross-check all maps have same keys ──────────────────────────────────────

test('All maps have identical key sets', () => {
  const romanKeys = Object.keys(ERA_ROMAN).sort().join(',');
  const labelKeys = Object.keys(ERA_LABEL_EN).sort().join(',');
  const spriteKeys = Object.keys(ERA_SPRITE_KEY).sort().join(',');
  if (romanKeys !== labelKeys) throw new Error('ERA_ROMAN vs ERA_LABEL_EN mismatch');
  if (romanKeys !== spriteKeys) throw new Error('ERA_ROMAN vs ERA_SPRITE_KEY mismatch');
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
