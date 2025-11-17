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

// More accurate coordinates matching actual SF street grid
// Bryant St runs NW-SE, cross streets run NE-SW
export const mockBlockfaces: Blockface[] = [
  // ===== BRYANT STREET (your location) =====
  
  // Bryant: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'bryant-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40930, 37.75990],
        [-122.40840, 37.75880],
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
        [-122.40945, 37.75990],
        [-122.40855, 37.75880],
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
        [-122.40840, 37.75880],
        [-122.40750, 37.75770],
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
        [-122.40855, 37.75880],
        [-122.40765, 37.75770],
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // ===== HARRISON STREET (1 block west) =====
  
  // Harrison: 19th to 20th - LEGAL (east side) ✅
  {
    id: 'harrison-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41130, 37.75990],
        [-122.41040, 37.75880],
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // Harrison: 19th to 20th - ILLEGAL (west side) ⚠️ Creates YELLOW
  {
    id: 'harrison-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41145, 37.75990],
        [-122.41055, 37.75880],
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
        [-122.41040, 37.75880],
        [-122.40950, 37.75770],
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
        [-122.41055, 37.75880],
        [-122.40965, 37.75770],
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // ===== FOLSOM STREET (1 block east) =====
  
  // Folsom: 19th to 20th - LEGAL (west side) ✅
  {
    id: 'folsom-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40730, 37.75990],
        [-122.40640, 37.75880],
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
        [-122.40715, 37.75990],
        [-122.40625, 37.75880],
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
        [-122.40640, 37.75880],
        [-122.40550, 37.75770],
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createRPPRule(),
    ],
  },
  
  // Folsom: 20th to 21st - LEGAL (east side) ⚠️ Creates YELLOW
  {
    id: 'folsom-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40625, 37.75880],
        [-122.40535, 37.75770],
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== 19TH STREET (perpendicular) =====
  
  // 19th: Harrison to Bryant - LEGAL (south side) ✅
  {
    id: '19th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41130, 37.75990],
        [-122.40930, 37.75990],
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
        [-122.41130, 37.76005],
        [-122.40930, 37.76005],
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
        [-122.40930, 37.75990],
        [-122.40730, 37.75990],
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
        [-122.40930, 37.76005],
        [-122.40730, 37.76005],
      ],
    },
    streetName: '19th St',
    side: 'north',
    rules: [
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // ===== 20TH STREET (your location) =====
  
  // 20th: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '20th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41040, 37.75880],
        [-122.40840, 37.75880],
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
        [-122.41040, 37.75865],
        [-122.40840, 37.75865],
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
        [-122.40840, 37.75880],
        [-122.40640, 37.75880],
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
        [-122.40840, 37.75865],
        [-122.40640, 37.75865],
      ],
    },
    streetName: '20th St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
  
  // ===== 21ST STREET (perpendicular) =====
  
  // 21st: Harrison to Bryant - LEGAL (north side) ✅
  {
    id: '21st-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40950, 37.75770],
        [-122.40750, 37.75770],
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
        [-122.40950, 37.75755],
        [-122.40750, 37.75755],
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
        [-122.40750, 37.75770],
        [-122.40550, 37.75770],
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
        [-122.40750, 37.75755],
        [-122.40550, 37.75755],
      ],
    },
    streetName: '21st St',
    side: 'south',
    rules: [
      createTimeLimitRule(180), // 3-hour limit
    ],
  },
];