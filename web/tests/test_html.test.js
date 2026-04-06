/**
 * Tests for lib/html.js — escHtml(), escAttr(), hilite()
 * Run with: node tests/test_html.test.js
 */

import { escHtml, escAttr, hilite } from '../js/lib/html.js';

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); console.log(`✓ ${name}`); passed++; }
  catch (e) { console.error(`✗ ${name}\n  ${e.message}`); failed++; }
}
function eq(a, b) { if (a !== b) throw new Error(`Expected "${b}", got "${a}"`); }

// ── escHtml ──────────────────────────────────────────────────────────────────

test('escHtml: plain text unchanged', () => eq(escHtml('hello'), 'hello'));
test('escHtml: escapes &', () => eq(escHtml('a&b'), 'a&amp;b'));
test('escHtml: escapes <>', () => eq(escHtml('<script>'), '&lt;script&gt;'));
test('escHtml: escapes quotes', () => eq(escHtml('"test"'), '&quot;test&quot;'));
test('escHtml: all entities', () =>
  eq(escHtml('a & b < c > d "e"'), 'a &amp; b &lt; c &gt; d &quot;e&quot;'));
test('escHtml: number coerced to string', () => eq(escHtml(42), '42'));

// ── escAttr ──────────────────────────────────────────────────────────────────

test('escAttr: plain text unchanged', () => eq(escAttr('hello'), 'hello'));
test('escAttr: escapes & and "', () => eq(escAttr('a&b "c"'), 'a&amp;b &quot;c&quot;'));
test('escAttr: does not escape <>', () => eq(escAttr('<>'), '<>'));

// ── hilite ───────────────────────────────────────────────────────────────────

test('hilite: no query returns escaped', () =>
  eq(hilite('<b>text</b>', ''), '&lt;b&gt;text&lt;/b&gt;'));
test('hilite: highlights match', () => {
  const result = hilite('Hello World', 'World');
  eq(result, 'Hello <mark class="eac-hl">World</mark>');
});
test('hilite: case insensitive', () => {
  const result = hilite('Hello World', 'world');
  eq(result, 'Hello <mark class="eac-hl">World</mark>');
});
test('hilite: no match returns escaped', () => {
  eq(hilite('Hello', 'xyz'), 'Hello');
});
test('hilite: escapes surrounding text', () => {
  const result = hilite('<b>Hello</b>', 'Hello');
  eq(result, '&lt;b&gt;<mark class="eac-hl">Hello</mark>&lt;/b&gt;');
});
test('hilite: custom escape function', () => {
  const result = hilite('Hello World', 'World', s => s.toUpperCase());
  eq(result, 'HELLO <mark class="eac-hl">WORLD</mark>');
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
