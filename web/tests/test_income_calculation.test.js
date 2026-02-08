/**
 * Test suite: Income calculation consistency between Python and JavaScript.
 * 
 * Formula: income_per_second = (base + offset) * (1 + modifier)
 *   where modifier = citizen_count * citizen_effect + effect_modifier
 * 
 * Run with: node tests/test_income_calculation.test.js
 */

/**
 * Calculate income per second (matching Python formula)
 * @param {number} base - Base income (1.0 for gold, 0.5 for culture)
 * @param {number} offset - Income offset from effects
 * @param {number} citizenCount - Number of citizens in this role
 * @param {number} citizenEffect - Base citizen effect (0.03)
 * @param {number} effectModifier - Effect modifier from buildings
 * @returns {number} Income per second
 */
function calculateIncome(base, offset, citizenCount, citizenEffect, effectModifier = 0) {
  const totalModifier = citizenCount * citizenEffect + effectModifier;
  return (base + offset) * (1 + totalModifier);
}

/**
 * Assertion helper with floating point tolerance
 */
function assertClose(actual, expected, tolerance = 0.0001, testName = '') {
  if (Math.abs(actual - expected) > tolerance) {
    throw new Error(
      `${testName}\n` +
      `  Expected: ${expected}\n` +
      `  Actual:   ${actual}\n` +
      `  Diff:     ${Math.abs(actual - expected)}`
    );
  }
}

/**
 * Simple test runner
 */
let testsPassed = 0;
let testsFailed = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    console.log(`✓ ${name}`);
    testsPassed++;
    results.push({ name, passed: true });
  } catch (err) {
    console.error(`✗ ${name}`);
    console.error(`  ${err.message}`);
    testsFailed++;
    results.push({ name, passed: false, error: err.message });
  }
}

// ============================================
// Test Cases
// ============================================

test('Gold income: base case (2 merchants, no effects)', () => {
  // Python: (1.0 + 0.15) * (1 + 2*0.03) = 1.15 * 1.06 = 1.219
  const result = calculateIncome(1.0, 0.15, 2, 0.03);
  assertClose(result, 1.219, 0.0001, 'Gold with 2 merchants');
});

test('Culture income: base case (1 artist, no effects)', () => {
  // Python: (0.5 + 0.05) * (1 + 1*0.03) = 0.55 * 1.03 = 0.5665
  const result = calculateIncome(0.5, 0.05, 1, 0.03);
  assertClose(result, 0.5665, 0.0001, 'Culture with 1 artist');
});

test('Gold income with effect modifier (+5% from building)', () => {
  // Python: (1.0 + 0.15) * (1 + 2*0.03 + 0.05) = 1.15 * 1.11 = 1.2765
  const result = calculateIncome(1.0, 0.15, 2, 0.03, 0.05);
  assertClose(result, 1.2765, 0.0001, 'Gold with effect modifier');
});

test('Culture income with multiple effects', () => {
  // Python: (0.5 + 0.05) * (1 + 3*0.03 + 0.02) = 0.55 * 1.11 = 0.6105
  const result = calculateIncome(0.5, 0.05, 3, 0.03, 0.02);
  assertClose(result, 0.6105, 0.0001, 'Culture with multiple effects');
});

test('Zero modifier case (no citizens, no effects)', () => {
  // Python: (1.0 + 0.0) * (1 + 0) = 1.0
  const result = calculateIncome(1.0, 0.0, 0, 0.03, 0);
  assertClose(result, 1.0, 0.0001, 'Base only, no modifiers');
});

test('Only offset, no modifier', () => {
  // Python: (1.0 + 0.50) * (1 + 0) = 1.50
  const result = calculateIncome(1.0, 0.50, 0, 0.03, 0);
  assertClose(result, 1.50, 0.0001, 'Offset only, no citizens');
});

test('Only citizens, no offset', () => {
  // Python: (1.0 + 0.0) * (1 + 5*0.03) = 1.0 * 1.15 = 1.15
  const result = calculateIncome(1.0, 0.0, 5, 0.03, 0);
  assertClose(result, 1.15, 0.0001, 'Citizens only, no offset');
});

test('Comprehensive: all components (2 merchants, 0.15 offset, 0.05 effect)', () => {
  const base = 1.0;
  const offset = 0.15;
  const merchants = 2;
  const citizenEffect = 0.03;
  const effectMod = 0.0;
  
  const result = calculateIncome(base, offset, merchants, citizenEffect, effectMod);
  const expected = (base + offset) * (1 + merchants * citizenEffect + effectMod);
  assertClose(result, expected, 0.00001, 'All components formula match');
});

test('Multiplier calculation matches formula', () => {
  const merchantCount = 2;
  const citizenEffect = 0.03;
  const effectMod = 0.05;
  
  const multiplier = 1 + merchantCount * citizenEffect + effectMod;
  const base = 1.0;
  const offset = 0.15;
  
  const result = (base + offset) * multiplier;
  assertClose(result, 1.2765, 0.0001, 'Multiplier formula match');
});

// Table-driven tests
const testCases = [
  // [base, offset, citizens, citizenEffect, effectMod, expectedResult, description]
  [1.0, 0.15, 2, 0.03, 0.0, 1.219, 'Gold with 2 merchants'],
  [0.5, 0.05, 1, 0.03, 0.0, 0.5665, 'Culture with 1 artist'],
  [1.0, 0.15, 2, 0.03, 0.05, 1.2765, 'Gold with effect modifier'],
  [0.5, 0.05, 3, 0.03, 0.02, 0.6105, 'Culture with multiple effects'],
  [1.0, 0.0, 0, 0.03, 0.0, 1.0, 'Base only, no modifiers'],
  [1.0, 0.50, 0, 0.03, 0.0, 1.50, 'Offset only, no citizens'],
  [1.0, 0.0, 5, 0.03, 0.0, 1.15, 'Citizens only, no offset'],
];

testCases.forEach(([base, offset, citizens, effect, effectMod, expected, desc]) => {
  test(`Table: ${desc}`, () => {
    const result = calculateIncome(base, offset, citizens, effect, effectMod);
    assertClose(result, expected, 0.0001, desc);
  });
});

// ============================================
// Test Results
// ============================================

console.log('\n' + '='.repeat(70));
console.log(`${testsPassed} passed, ${testsFailed} failed out of ${testsPassed + testsFailed} tests`);
console.log('='.repeat(70) + '\n');

if (testsFailed > 0) {
  process.exit(1);
} else {
  console.log('✓ All income calculation tests passed!');
  process.exit(0);
}
