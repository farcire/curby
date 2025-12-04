// Simple test runner for RPP evaluator
// Run with: node test-rpp.js

function evaluateRPPZone(regulation, zone, durationMinutes) {
  const text = regulation.toLowerCase();
  
  const patterns = [
    /visitor[s]?\s+(\d+)\s+hour[s]?/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+visitor/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+(?:for\s+)?non-permit/i,
    /non-permit\s+holder[s]?\s+(\d+)\s+hour[s]?/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+(?:for\s+)?non-resident/i,
  ];
  
  let visitorLimitMinutes = null;
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      visitorLimitMinutes = parseInt(match[1]) * 60;
      break;
    }
  }
  
  if (visitorLimitMinutes === null) {
    if (text.includes('visitor') || text.includes('non-permit') || text.includes('non-resident')) {
      visitorLimitMinutes = 120;
    }
  }
  
  if (visitorLimitMinutes !== null) {
    if (durationMinutes <= visitorLimitMinutes) {
      const hours = visitorLimitMinutes / 60;
      return {
        canPark: true,
        reason: `${hours}hr parking except Zone ${zone}`,
        visitorLimitMinutes
      };
    } else {
      const limitHours = visitorLimitMinutes / 60;
      const requestedHours = Math.round(durationMinutes / 60 * 10) / 10;
      return {
        canPark: false,
        reason: `${limitHours}hr parking except Zone ${zone}`,
        visitorLimitMinutes
      };
    }
  }
  
  return {
    canPark: false,
    reason: `No parking except Zone ${zone}`,
    visitorLimitMinutes: undefined
  };
}

console.log('=== RPP Evaluator Tests ===\n');

// Test 1: 2-hour visitor parking, user wants 1 hour (should be legal)
console.log('Test 1: 2hr visitor parking, 1hr duration');
const test1 = evaluateRPPZone(
  'Residential Permit Zone W - 2 hour visitor parking',
  'W',
  60
);
console.log('Result:', test1);
console.log('Expected: canPark=true, reason: "2hr parking except Zone W"');
console.log('✓ Pass:', test1.canPark === true && test1.reason === '2hr parking except Zone W');
console.log('');

// Test 2: 2-hour visitor parking, user wants 3 hours (should be illegal)
console.log('Test 2: 2hr visitor parking, 3hr duration');
const test2 = evaluateRPPZone(
  'Residential Permit Zone W - 2 hour visitor parking',
  'W',
  180
);
console.log('Result:', test2);
console.log('Expected: canPark=false, reason: "2hr parking except Zone W"');
console.log('✓ Pass:', test2.canPark === false && test2.reason === '2hr parking except Zone W');
console.log('');

// Test 3: Different pattern - "visitors 2 hours"
console.log('Test 3: Different pattern - "visitors 2 hours"');
const test3 = evaluateRPPZone(
  'Permit Zone A - visitors 2 hours',
  'A',
  90
);
console.log('Result:', test3);
console.log('Expected: canPark=true, reason: "2hr parking except Zone A"');
console.log('✓ Pass:', test3.canPark === true && test3.reason === '2hr parking except Zone A');
console.log('');

// Test 4: No visitor parking mentioned (should be illegal)
console.log('Test 4: No visitor parking mentioned');
const test4 = evaluateRPPZone(
  'Residential Permit Zone X - permit required',
  'X',
  60
);
console.log('Result:', test4);
console.log('Expected: canPark=false, reason: "No parking except Zone X"');
console.log('✓ Pass:', test4.canPark === false && test4.reason === 'No parking except Zone X');
console.log('');

// Test 5: 1-hour visitor parking pattern
console.log('Test 5: 1hr visitor parking');
const test5 = evaluateRPPZone(
  'Zone B - 1 hour non-permit parking',
  'B',
  45
);
console.log('Result:', test5);
console.log('Expected: canPark=true, reason: "1hr parking except Zone B"');
console.log('✓ Pass:', test5.canPark === true && test5.reason === '1hr parking except Zone B');
console.log('');

// Test 6: Edge case - exactly at limit
console.log('Test 6: Exactly at 2hr limit');
const test6 = evaluateRPPZone(
  'Zone C - 2hr visitor parking',
  'C',
  120
);
console.log('Result:', test6);
console.log('Expected: canPark=true, reason: "2hr parking except Zone C"');
console.log('✓ Pass:', test6.canPark === true && test6.reason === '2hr parking except Zone C');
console.log('');

// Test 7: Real SF example - Mission District Zone W
console.log('Test 7: Real SF example - 20th & Valencia (Zone W)');
const test7 = evaluateRPPZone(
  'RPP ZONE W 2 HOUR VISITOR PARKING 8AM-6PM MON-SAT',
  'W',
  120
);
console.log('Result:', test7);
console.log('Expected: canPark=true, reason: "2hr parking except Zone W"');
console.log('✓ Pass:', test7.canPark === true && test7.reason === '2hr parking except Zone W');
console.log('');

console.log('=== All Tests Complete ===');

// Summary
const allTests = [test1, test2, test3, test4, test5, test6, test7];
const passed = [
  test1.canPark === true && test1.reason === '2hr parking except Zone W',
  test2.canPark === false && test2.reason === '2hr parking except Zone W',
  test3.canPark === true && test3.reason === '2hr parking except Zone A',
  test4.canPark === false && test4.reason === 'No parking except Zone X',
  test5.canPark === true && test5.reason === '1hr parking except Zone B',
  test6.canPark === true && test6.reason === '2hr parking except Zone C',
  test7.canPark === true && test7.reason === '2hr parking except Zone W'
].filter(Boolean).length;

console.log(`\n✅ ${passed}/7 tests passed`);