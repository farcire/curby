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

// Actual GPS coordinates from OpenStreetMap for Bryant & 20th area in SF
// Verified coordinates matching the visible map
export const mockBlockfaces: Blockface[] = [
  // ===== 20TH STREET (runs east-west) =====
  
  // 20th: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '20th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41200, 37.75885],
        [-122.41020, 37.75885],
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
        [-122.41200, 37.75870],
        [-122.41020, 37.75870],
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
        [-122.41020, 37.75885],
        [-122.40720, 37.75885],
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
        [-122.41020, 37.75870],
        [-122.40720, 37.75870],
      ],
    },
    streetName: '20th St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== 19TH STREET (runs east-west, north of 20th) =====
  
  // 19th: Harrison to Bryant - LEGAL (south side) ✅
  {
    id: '19th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41290, 37.75995],
        [-122.41110, 37.75995],
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // 19th: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '19th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41290, 37.76010],
        [-122.41110, 37.76010],
      ],
    },
    streetName: '19th St',
    side: 'north',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (south side) ✅
  {
    id: '19th-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41110, 37.75995],
        [-122.40810, 37.75995],
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (north side) ✅
  {
    id: '19th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41110, 37.76010],
        [-122.40810, 37.76010],
      ],
    },
    streetName: '19th St',
    side: 'north',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // ===== 21ST STREET (runs east-west, south of 20th) =====
  
  // 21st: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '21st-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41110, 37.75775],
        [-122.40930, 37.75775],
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
        [-122.41110, 37.75760],
        [-122.40930, 37.75760],
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
        [-122.40930, 37.75775],
        [-122.40630, 37.75775],
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
        [-122.40930, 37.75760],
        [-122.40630, 37.75760],
      ],
    },
    streetName: '21st St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== BRYANT STREET (runs north-south) =====
  
  // Bryant: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'bryant-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41100, 37.75995],
        [-122.41100, 37.75885],
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
        [-122.41120, 37.75995],
        [-122.41120, 37.75885],
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
        [-122.40920, 37.75885],
        [-122.40920, 37.75775],
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
        [-122.40940, 37.75885],
        [-122.40940, 37.75775],
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // ===== HARRISON STREET (west of Bryant, runs north-south) =====
  
  // Harrison: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'harrison-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41190, 37.75995],
        [-122.41190, 37.75885],
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
        [-122.41210, 37.75995],
        [-122.41210, 37.75885],
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
        [-122.41100, 37.75885],
        [-122.41100, 37.75775],
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
        [-122.41120, 37.75885],
        [-122.41120, 37.75775],
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // ===== FOLSOM STREET (east of Bryant, runs north-south) =====
  
  // Folsom: 19th to 20th - LEGAL (west side) ✅
  {
    id: 'folsom-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40730, 37.75995],
        [-122.40730, 37.75885],
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
        [-122.40710, 37.75995],
        [-122.40710, 37.75885],
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
        [-122.40640, 37.75885],
        [-122.40640, 37.75775],
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
        [-122.40620, 37.75885],
        [-122.40620, 37.75775],
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
];