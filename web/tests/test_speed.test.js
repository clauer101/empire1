/**
 * Tests for lib/speed.js — calcBuildSpeed(), calcResearchSpeed()
 * Run with: node tests/test_speed.test.js
 */

import { calcBuildSpeed, calcResearchSpeed } from '../js/lib/speed.js';

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); console.log(`✓ ${name}`); passed++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); failed++; }
}
function close(a, b, tol = 0.0001) {
  if (Math.abs(a - b) > tol) throw new Error(`Expected ~${b}, got ${a}`);
}

// ── calcBuildSpeed ───────────────────────────────────────────────────────────

test('build: base case defaults', () => {
  // base=1, no effects → speed = (1+0)*(1+0) = 1
  close(calcBuildSpeed({}), 1);
});

test('build: with base_build_speed', () => {
  close(calcBuildSpeed({ base_build_speed: 2 }), 2);
});

test('build: with offset', () => {
  // (1 + 0.5) * (1 + 0) = 1.5
  close(calcBuildSpeed({ effects: { build_speed_offset: 0.5 } }), 1.5);
});

test('build: with modifier', () => {
  // (1 + 0) * (1 + 0.5) = 1.5
  close(calcBuildSpeed({ effects: { build_speed_modifier: 0.5 } }), 1.5);
});

test('build: combined', () => {
  // (2 + 0.3) * (1 + 0.2) = 2.3 * 1.2 = 2.76
  close(calcBuildSpeed({
    base_build_speed: 2,
    effects: { build_speed_offset: 0.3, build_speed_modifier: 0.2 }
  }), 2.76);
});

// ── calcResearchSpeed ────────────────────────────────────────────────────────

test('research: base case defaults', () => {
  close(calcResearchSpeed({}), 1);
});

test('research: with scientists', () => {
  // (1+0) * (1 + 0 + 3 * 0.03) = 1 * 1.09 = 1.09
  close(calcResearchSpeed({
    citizens: { scientist: 3 },
    citizen_effect: 0.03,
  }), 1.09);
});

test('research: combined with offset, modifier, scientists', () => {
  // (1.5 + 0.2) * (1 + 0.1 + 2 * 0.03) = 1.7 * 1.16 = 1.972
  close(calcResearchSpeed({
    base_research_speed: 1.5,
    effects: { research_speed_offset: 0.2, research_speed_modifier: 0.1 },
    citizens: { scientist: 2 },
    citizen_effect: 0.03,
  }), 1.972);
});

test('research: no scientists field → 0 bonus', () => {
  close(calcResearchSpeed({ base_research_speed: 1 }), 1);
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
