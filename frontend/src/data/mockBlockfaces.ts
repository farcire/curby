import { Blockface, ParkingRule } from '@/types/parking';

// Rule precedence constants
const PRECEDENCE = {
  'tow-away': 100,
  'street-sweeping': 90,
  'no-parking': 80,
  'meter': 70,
  'time-limit': 60,
  'rpp-zone': 50,
};

// Simplified rules for demo
const createTimeLimitRule = (minutes: number): ParkingRule => ({
  id: `time-limit-${minutes}`,
  type: 'time-limit',
  timeRanges: [{
    startTime: '09:00',
    endTime: '18:00',
    daysOfWeek: [1, 2, 3, 4, 5, 6], // Mon-Sat
  }],
  description: `${minutes / 60}-hour limit (9 AM-6 PM Mon-Sat)`,
  precedence: PRECEDENCE['time-limit'],
  metadata: {
    timeLimit: minutes,
  },
});

const createStreetSweepingRule = (): ParkingRule => ({
  id: 'street-sweeping-monday',
  type: 'street-sweeping',
  timeRanges: [{
    startTime: '00:00',
    endTime: '02:00',
    daysOfWeek: [1], // Monday
  }],
  description: 'Street sweeping Monday 12am-2am',
  precedence: PRECEDENCE['street-sweeping'],
});

const createNoParkingRule = (): ParkingRule => ({
  id: 'no-parking-anytime',
  type: 'no-parking',
  timeRanges: [{
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
  }],
  description: 'No parking anytime',
  precedence: PRECEDENCE['no-parking'],
});

const createRPPRule = (): ParkingRule => ({
  id: 'rpp-zone',
  type: 'rpp-zone',
  timeRanges: [{
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
  }],
  description: 'Permit required (Zone P)',
  precedence: PRECEDENCE['rpp-zone'],
  metadata: {
    permitZone: 'P',
  },
});

// REAL GPS coordinates from actual San Francisco intersections
// These follow the actual diagonal street grid of SF
export const mockBlockfaces: Blockface[] = [
  // ===== 19TH STREET (runs east-west at diagonal) =====
  
  // 19th: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '19th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41190, 37.75997], // 19th & Harrison
        [-122.41010, 37.75982], // 19th & Bryant
      ],
    },
    streetName: '19th St',
    side: 'north',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // 19th: Harrison to Bryant - LEGAL (south side) ✅
  {
    id: '19th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41185, 37.75985], // 19th & Harrison (south)
        [-122.41005, 37.75970], // 19th & Bryant (south)
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (north side) ✅
  {
    id: '19th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41010, 37.75982], // 19th & Bryant
        [-122.40710, 37.75952], // 19th & Folsom
      ],
    },
    streetName: '19th St',
    side: 'north',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (south side) ✅
  {
    id: '19th-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41005, 37.75970], // 19th & Bryant (south)
        [-122.40705, 37.75940], // 19th & Folsom (south)
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== 20TH STREET (runs east-west at diagonal) =====
  
  // 20th: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '20th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41100, 37.75887], // 20th & Harrison
        [-122.40920, 37.75872], // 20th & Bryant
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // 20th: Harrison to Bryant - LEGAL (south side) ✅
  {
    id: '20th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41095, 37.75875], // 20th & Harrison (south)
        [-122.40915, 37.75860], // 20th & Bryant (south)
      ],
    },
    streetName: '20th St',
    side: 'south',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // 20th: Bryant to Folsom - LEGAL (north side) ✅
  {
    id: '20th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40920, 37.75872], // 20th & Bryant
        [-122.40620, 37.75842], // 20th & Folsom
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // 20th: Bryant to Folsom - LEGAL (south side) ✅
  {
    id: '20th-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40915, 37.75860], // 20th & Bryant (south)
        [-122.40615, 37.75830], // 20th & Folsom (south)
      ],
    },
    streetName: '20th St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== 21ST STREET (runs east-west at diagonal) =====
  
  // 21st: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '21st-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41010, 37.75777], // 21st & Harrison
        [-122.40830, 37.75762], // 21st & Bryant
      ],
    },
    streetName: '21st St',
    side: 'north',
    rules: [
      createTimeLimitRule(60), // 1-hour limit
    ],
  },
  
  // 21st: Harrison to Bryant - LEGAL (south side) ✅
  {
    id: '21st-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41005, 37.75765], // 21st & Harrison (south)
        [-122.40825, 37.75750], // 21st & Bryant (south)
      ],
    },
    streetName: '21st St',
    side: 'south',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // 21st: Bryant to Folsom - LEGAL (north side) ✅
  {
    id: '21st-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40830, 37.75762], // 21st & Bryant
        [-122.40530, 37.75732], // 21st & Folsom
      ],
    },
    streetName: '21st St',
    side: 'north',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // 21st: Bryant to Folsom - LEGAL (south side) ✅
  {
    id: '21st-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40825, 37.75750], // 21st & Bryant (south)
        [-122.40525, 37.75720], // 21st & Folsom (south)
      ],
    },
    streetName: '21st St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== BRYANT STREET (runs north-south at diagonal) =====
  
  // Bryant: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'bryant-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41010, 37.75982], // 19th & Bryant
        [-122.40920, 37.75872], // 20th & Bryant
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
      createStreetSweepingRule(), // Street sweeping Monday 12am-2am
    ],
  },
  
  // Bryant: 19th to 20th - LEGAL (west side) ✅
  {
    id: 'bryant-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41020, 37.75985], // 19th & Bryant (west)
        [-122.40930, 37.75875], // 20th & Bryant (west)
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
      createStreetSweepingRule(), // Street sweeping Monday 12am-2am
    ],
  },
  
  // Bryant: 20th to 21st - ILLEGAL (east side) 🚫
  {
    id: 'bryant-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40920, 37.75872], // 20th & Bryant
        [-122.40830, 37.75762], // 21st & Bryant
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // Bryant: 20th to 21st - ILLEGAL (west side) 🚫
  {
    id: 'bryant-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40930, 37.75875], // 20th & Bryant (west)
        [-122.40840, 37.75765], // 21st & Bryant (west)
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // ===== HARRISON STREET (runs north-south at diagonal) =====
  
  // Harrison: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'harrison-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41190, 37.75997], // 19th & Harrison
        [-122.41100, 37.75887], // 20th & Harrison
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // Harrison: 19th to 20th - ILLEGAL (west side) 🚫
  {
    id: 'harrison-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41200, 37.76000], // 19th & Harrison (west)
        [-122.41110, 37.75890], // 20th & Harrison (west)
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // Harrison: 20th to 21st - LEGAL (east side) ✅
  {
    id: 'harrison-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41100, 37.75887], // 20th & Harrison
        [-122.41010, 37.75777], // 21st & Harrison
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // Harrison: 20th to 21st - ILLEGAL (west side) 🚫
  {
    id: 'harrison-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41110, 37.75890], // 20th & Harrison (west)
        [-122.41020, 37.75780], // 21st & Harrison (west)
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // ===== FOLSOM STREET (runs north-south at diagonal) =====
  
  // Folsom: 19th to 20th - LEGAL (west side) ✅
  {
    id: 'folsom-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40710, 37.75952], // 19th & Folsom
        [-122.40620, 37.75842], // 20th & Folsom
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // Folsom: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'folsom-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40700, 37.75955], // 19th & Folsom (east)
        [-122.40610, 37.75845], // 20th & Folsom (east)
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // Folsom: 20th to 21st - ILLEGAL (west side) 🚫
  {
    id: 'folsom-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40620, 37.75842], // 20th & Folsom
        [-122.40530, 37.75732], // 21st & Folsom
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // Folsom: 20th to 21st - LEGAL (east side) ✅
  {
    id: 'folsom-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40610, 37.75845], // 20th & Folsom (east)
        [-122.40520, 37.75735], // 21st & Folsom (east)
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
];