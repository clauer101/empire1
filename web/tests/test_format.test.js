/**
 * Tests for lib/format.js — fmtEffort() and fmtSecs()
 * Run with: node tests/test_format.test.js
 */

import { fmtEffort, fmtSecs } from '../js/lib/format.js';

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); console.log(`✓ ${name}`); passed++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); failed++; }
}
function eq(a, b) { if (a !== b) throw new Error(`Expected "${b}", got "${a}"`); }

// ── fmtEffort ────────────────────────────────────────────────────────────────

test('fmtEffort: null → dash', () => eq(fmtEffort(null), '—'));
test('fmtEffort: undefined → dash', () => eq(fmtEffort(undefined), '—'));
test('fmtEffort: small number', () => eq(fmtEffort(42), '42'));
test('fmtEffort: rounds float', () => eq(fmtEffort(42.7), '43'));
test('fmtEffort: 1000 → 1.0K', () => eq(fmtEffort(1000), '1.0K'));
test('fmtEffort: 2500 → 2.5K', () => eq(fmtEffort(2500), '2.5K'));
test('fmtEffort: 1000000 → 1.0M', () => eq(fmtEffort(1000000), '1.0M'));
test('fmtEffort: 1500000 → 1.5M', () => eq(fmtEffort(1500000), '1.5M'));
test('fmtEffort: 999 stays as integer', () => eq(fmtEffort(999), '999'));
test('fmtEffort: zero', () => eq(fmtEffort(0), '0'));

// ── fmtSecs ──────────────────────────────────────────────────────────────────

test('fmtSecs: null → dash', () => eq(fmtSecs(null), '—'));
test('fmtSecs: negative → dash', () => eq(fmtSecs(-5), '—'));
test('fmtSecs: 0 → 0s', () => eq(fmtSecs(0), '0s'));
test('fmtSecs: 45 → 45s', () => eq(fmtSecs(45), '45s'));
test('fmtSecs: 60 → 1m 0s', () => eq(fmtSecs(60), '1m 0s'));
test('fmtSecs: 125 → 2m 5s', () => eq(fmtSecs(125), '2m 5s'));
test('fmtSecs: 3600 → 1h 0m 0s', () => eq(fmtSecs(3600), '1h 0m 0s'));
test('fmtSecs: 3661 → 1h 1m 1s', () => eq(fmtSecs(3661), '1h 1m 1s'));
test('fmtSecs: 7384 → 2h 3m 4s', () => eq(fmtSecs(7384), '2h 3m 4s'));

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
