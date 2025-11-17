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

// Sample rules for different scenarios
const createStreetSweepingRule = (day: number, startTime: string, endTime: string): ParkingRule => ({
  id: `sweep-${day}-${startTime}`,
  type: 'street-sweeping',
  timeRanges: [{
    startTime,
    endTime,
    daysOfWeek: [day],
  }],
  description: `Street sweeping ${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day]} ${startTime}-${endTime}`,
  precedence: PRECEDENCE['street-sweeping'],
});

const createMeterRule = (): ParkingRule => ({
  id: 'meter-weekday',
  type: 'meter',
  timeRanges: [{
    startTime: '09:00',
    endTime: '18:00',
    daysOfWeek: [1, 2, 3, 4, 5], // Mon-Fri
  }],
  description: 'Meter parking required Mon-Fri 9am-6pm',
  precedence: PRECEDENCE['meter'],
  metadata: {
    meterRate: 3.50,
  },
});

const createTimeLimitRule = (minutes: number): ParkingRule => ({
  id: `time-limit-${minutes}`,
  type: 'time-limit',
  timeRanges: [{
    startTime: '08:00',
    endTime: '20:00',
    daysOfWeek: [1, 2, 3, 4, 5, 6], // Mon-Sat
  }],
  description: `${minutes / 60}-hour parking limit`,
  precedence: PRECEDENCE['time-limit'],
  metadata: {
    timeLimit: minutes,
  },
});

const createRPPRule = (zone: string): ParkingRule => ({
  id: `rpp-${zone}`,
  type: 'rpp-zone',
  timeRanges: [{
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
  }],
  description: `Residential Permit Zone ${zone} required`,
  precedence: PRECEDENCE['rpp-zone'],
  metadata: {
    permitZone: zone,
  },
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

// Mock blockfaces for 5-block radius around 20th & Bryant (18th-22nd, Harrison-Potrero)
export const mockBlockfaces: Blockface[] = [
  // ===== BRYANT STREET (main north-south arterial) =====
  
  // Bryant: 18th to 19th - LEGAL (east side)
  {
    id: 'bryant-18th-19th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7610], // 18th St
        [-122.4093, 37.7599], // 19th St
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'), // Tuesday
      createTimeLimitRule(120),
    ],
  },
  
  // Bryant: 19th to 20th - LEGAL (east side) - YOUR STARTING POINT
  {
    id: 'bryant-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7599], // 19th St
        [-122.4093, 37.7588], // 20th St
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(4, '12:00', '14:00'), // Thursday
      createTimeLimitRule(180),
    ],
  },
  
  // Bryant: 20th to 21st - ILLEGAL (east side, sweeping active)
  {
    id: 'bryant-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7588], // 20th St
        [-122.4093, 37.7577], // 21st St
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(1, '12:00', '14:00'), // Monday - ACTIVE NOW
    ],
  },
  
  // Bryant: 21st to 22nd - LEGAL (east side)
  {
    id: 'bryant-21st-22nd-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7577], // 21st St
        [-122.4093, 37.7566], // 22nd St
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'), // Wednesday
      createTimeLimitRule(120),
    ],
  },
  
  // ===== HARRISON STREET (one block west of Bryant) =====
  
  // Harrison: 19th to 20th - LEGAL (west side)
  {
    id: 'harrison-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7599], // 19th St
        [-122.4113, 37.7588], // 20th St
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createStreetSweepingRule(5, '08:00', '10:00'), // Friday
      createTimeLimitRule(240),
    ],
  },
  
  // Harrison: 20th to 21st - LEGAL (west side, meters)
  {
    id: 'harrison-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7588], // 20th St
        [-122.4113, 37.7577], // 21st St
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createMeterRule(),
      createTimeLimitRule(120),
    ],
  },
  
  // ===== FOLSOM STREET (one block east of Bryant) =====
  
  // Folsom: 19th to 20th - LEGAL (east side)
  {
    id: 'folsom-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4073, 37.7599], // 19th St
        [-122.4073, 37.7588], // 20th St
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'), // Monday
      createTimeLimitRule(120),
    ],
  },
  
  // Folsom: 20th to 21st - LEGAL (east side, RPP zone)
  {
    id: 'folsom-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4073, 37.7588], // 20th St
        [-122.4073, 37.7577], // 21st St
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createRPPRule('P'),
      createTimeLimitRule(120), // 2hr visitor parking
    ],
  },
  
  // ===== 20TH STREET (your starting point - runs east-west) =====
  
  // 20th: Harrison to Bryant - LEGAL (north side)
  {
    id: '20th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7588], // Harrison
        [-122.4093, 37.7588], // Bryant
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(2, '12:00', '14:00'), // Tuesday
      createTimeLimitRule(180),
    ],
  },
  
  // 20th: Bryant to Folsom - LEGAL (north side, best option!)
  {
    id: '20th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7588], // Bryant
        [-122.4073, 37.7588], // Folsom
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(4, '08:00', '10:00'), // Thursday
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // 20th: Folsom to York - LEGAL (north side)
  {
    id: '20th-folsom-york-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4073, 37.7588], // Folsom
        [-122.4053, 37.7588], // York
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(3, '12:00', '14:00'), // Wednesday
      createTimeLimitRule(120),
    ],
  },
  
  // ===== 19TH STREET (runs east-west) =====
  
  // 19th: Harrison to Bryant - LEGAL (south side)
  {
    id: '19th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7599], // Harrison
        [-122.4093, 37.7599], // Bryant
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'), // Monday
      createTimeLimitRule(120),
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (south side)
  {
    id: '19th-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7599], // Bryant
        [-122.4073, 37.7599], // Folsom
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(5, '12:00', '14:00'), // Friday
      createTimeLimitRule(180),
    ],
  },
  
  // ===== 21ST STREET (runs east-west) =====
  
  // 21st: Harrison to Bryant - LEGAL (north side, meters)
  {
    id: '21st-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7577], // Harrison
        [-122.4093, 37.7577], // Bryant
      ],
    },
    streetName: '21st St',
    side: 'north',
    rules: [
      createMeterRule(),
      createTimeLimitRule(60),
    ],
  },
  
  // 21st: Bryant to Folsom - LEGAL (north side)
  {
    id: '21st-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7577], // Bryant
        [-122.4073, 37.7577], // Folsom
      ],
    },
    streetName: '21st St',
    side: 'north',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'), // Tuesday
      createTimeLimitRule(120),
    ],
  },
  
  // ===== YORK STREET (residential, east of Folsom) =====
  
  // York: 19th to 20th - LEGAL (west side, quiet residential)
  {
    id: 'york-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4053, 37.7599], // 19th St
        [-122.4053, 37.7588], // 20th St
      ],
    },
    streetName: 'York St',
    side: 'west',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'), // Wednesday
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // York: 20th to 21st - LEGAL (west side)
  {
    id: 'york-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4053, 37.7588], // 20th St
        [-122.4053, 37.7577], // 21st St
      ],
    },
    streetName: 'York St',
    side: 'west',
    rules: [
      createStreetSweepingRule(4, '12:00', '14:00'), // Thursday
      createTimeLimitRule(180),
    ],
  },
  
  // ===== 18TH STREET (northern boundary) =====
  
  // 18th: Harrison to Bryant - ILLEGAL (north side, no parking)
  {
    id: '18th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7610], // Harrison
        [-122.4093, 37.7610], // Bryant
      ],
    },
    streetName: '18th St',
    side: 'north',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // 18th: Bryant to Folsom - LEGAL (north side, meters)
  {
    id: '18th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7610], // Bryant
        [-122.4073, 37.7610], // Folsom
      ],
    },
    streetName: '18th St',
    side: 'north',
    rules: [
      createMeterRule(),
      createTimeLimitRule(60),
    ],
  },
  
  // ===== 22ND STREET (southern boundary) =====
  
  // 22nd: Harrison to Bryant - LEGAL (south side)
  {
    id: '22nd-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4113, 37.7566], // Harrison
        [-122.4093, 37.7566], // Bryant
      ],
    },
    streetName: '22nd St',
    side: 'south',
    rules: [
      createStreetSweepingRule(5, '08:00', '10:00'), // Friday
      createTimeLimitRule(120),
    ],
  },
  
  // 22nd: Bryant to Folsom - LEGAL (south side, RPP)
  {
    id: '22nd-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4093, 37.7566], // Bryant
        [-122.4073, 37.7566], // Folsom
      ],
    },
    streetName: '22nd St',
    side: 'south',
    rules: [
      createRPPRule('P'),
      createTimeLimitRule(120),
    ],
  },
];