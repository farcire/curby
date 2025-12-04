import { evaluateRPPZone } from './rppEvaluator';

/**
 * Test suite for RPP evaluator
 * Run this in browser console or create a proper test file
 */

console.log('=== RPP Evaluator Tests ===\n');

// Test 1: 2-hour visitor parking, user wants 1 hour (should be legal)
console.log('Test 1: 2hr visitor parking, 1hr duration');
const test1 = evaluateRPPZone(
  'Residential Permit Zone W - 2 hour visitor parking',
  'W',
  60
);
console.log('Result:', test1);
console.log('Expected: canPark=true, reason includes "2hr visitor parking"');
console.log('✓ Pass:', test1.canPark === true && test1.reason.includes('2hr'));
console.log('');

// Test 2: 2-hour visitor parking, user wants 3 hours (should be illegal)
console.log('Test 2: 2hr visitor parking, 3hr duration');
const test2 = evaluateRPPZone(
  'Residential Permit Zone W - 2 hour visitor parking',
  'W',
  180
);
console.log('Result:', test2);
console.log('Expected: canPark=false, reason mentions exceeding limit');
console.log('✓ Pass:', test2.canPark === false && test2.reason.includes('exceeds'));
console.log('');

// Test 3: Different pattern - "visitors 2 hours"
console.log('Test 3: Different pattern - "visitors 2 hours"');
const test3 = evaluateRPPZone(
  'Permit Zone A - visitors 2 hours',
  'A',
  90
);
console.log('Result:', test3);
console.log('Expected: canPark=true, detects 2hr limit');
console.log('✓ Pass:', test3.canPark === true && test3.visitorLimitMinutes === 120);
console.log('');

// Test 4: No visitor parking mentioned (should be illegal)
console.log('Test 4: No visitor parking mentioned');
const test4 = evaluateRPPZone(
  'Residential Permit Zone X - permit required',
  'X',
  60
);
console.log('Result:', test4);
console.log('Expected: canPark=false, no visitor parking');
console.log('✓ Pass:', test4.canPark === false && test4.visitorLimitMinutes === undefined);
console.log('');

// Test 5: 1-hour visitor parking pattern
console.log('Test 5: 1hr visitor parking');
const test5 = evaluateRPPZone(
  'Zone B - 1 hour non-permit parking',
  'B',
  45
);
console.log('Result:', test5);
console.log('Expected: canPark=true, 1hr limit detected');
console.log('✓ Pass:', test5.canPark === true && test5.visitorLimitMinutes === 60);
console.log('');

// Test 6: Edge case - exactly at limit
console.log('Test 6: Exactly at 2hr limit');
const test6 = evaluateRPPZone(
  'Zone C - 2hr visitor parking',
  'C',
  120
);
console.log('Result:', test6);
console.log('Expected: canPark=true (at limit is OK)');
console.log('✓ Pass:', test6.canPark === true);
console.log('');

console.log('=== All Tests Complete ===');