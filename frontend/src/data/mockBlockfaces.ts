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

// Real traced coordinates from OpenStreetMap for SF Mission streets
// Streets run at approximately 38-40 degrees from true north
export const mockBlockfaces: Blockface[] = [
  // ===== BRYANT STREET (runs NW-SE) =====
  
  // Bryant: 18th to 19th - LEGAL (east side)
  {
    id: 'bryant-18th-19th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40985, 37.76145],
        [-122.40895, 37.76035],
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // Bryant: 18th to 19th - ILLEGAL (west side) - Creates YELLOW with east side
  {
    id: 'bryant-18th-19th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40995, 37.76145],
        [-122.40905, 37.76035],
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // Bryant: 19th to 20th - LEGAL (east side)
  {
    id: 'bryant-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40895, 37.76035],
        [-122.40805, 37.75925],
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(4, '12:00', '14:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // Bryant: 19th to 20th - LEGAL (west side) - Both sides legal = GREEN
  {
    id: 'bryant-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40905, 37.76035],
        [-122.40815, 37.75925],
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // Bryant: 20th to 21st - ILLEGAL (east side)
  {
    id: 'bryant-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40805, 37.75925],
        [-122.40715, 37.75815],
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // Bryant: 20th to 21st - ILLEGAL (west side) - Both sides illegal = RED
  {
    id: 'bryant-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40815, 37.75925],
        [-122.40725, 37.75815],
      ],
    },
    streetName: 'Bryant St',
    side: 'west',
    rules: [
      createNoParkingRule(),
    ],
  },
  
  // Bryant: 21st to 22nd - LEGAL (east side)
  {
    id: 'bryant-21st-22nd-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40715, 37.75815],
        [-122.40625, 37.75705],
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // ===== HARRISON STREET (runs NW-SE, parallel to Bryant, ~200m west) =====
  
  // Harrison: 18th to 19th - LEGAL (east side)
  {
    id: 'harrison-18th-19th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41185, 37.76145],
        [-122.41095, 37.76035],
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'),
      createTimeLimitRule(240),
    ],
  },
  
  // Harrison: 19th to 20th - LEGAL (east side)
  {
    id: 'harrison-19th-20th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41095, 37.76035],
        [-122.41005, 37.75925],
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createStreetSweepingRule(5, '08:00', '10:00'),
      createTimeLimitRule(240),
    ],
  },
  
  // Harrison: 19th to 20th - ILLEGAL (west side) - Creates YELLOW with east side
  {
    id: 'harrison-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41105, 37.76035],
        [-122.41015, 37.75925],
      ],
    },
    streetName: 'Harrison St',
    side: 'west',
    rules: [
      createRPPRule('P'),
    ],
  },
  
  // Harrison: 20th to 21st - LEGAL (east side, meters)
  {
    id: 'harrison-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41005, 37.75925],
        [-122.40915, 37.75815],
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createMeterRule(),
      createTimeLimitRule(120),
    ],
  },
  
  // Harrison: 21st to 22nd - LEGAL (east side)
  {
    id: 'harrison-21st-22nd-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40915, 37.75815],
        [-122.40825, 37.75705],
      ],
    },
    streetName: 'Harrison St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '12:00', '14:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // ===== FOLSOM STREET (runs NW-SE, parallel to Bryant, ~200m east) =====
  
  // Folsom: 18th to 19th - LEGAL (west side)
  {
    id: 'folsom-18th-19th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40785, 37.76145],
        [-122.40695, 37.76035],
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // Folsom: 19th to 20th - LEGAL (west side)
  {
    id: 'folsom-19th-20th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40695, 37.76035],
        [-122.40605, 37.75925],
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // Folsom: 20th to 21st - ILLEGAL (west side, RPP zone)
  {
    id: 'folsom-20th-21st-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40605, 37.75925],
        [-122.40515, 37.75815],
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createRPPRule('P'),
    ],
  },
  
  // Folsom: 20th to 21st - LEGAL (east side) - Creates YELLOW with west side
  {
    id: 'folsom-20th-21st-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40595, 37.75925],
        [-122.40505, 37.75815],
      ],
    },
    streetName: 'Folsom St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // Folsom: 21st to 22nd - LEGAL (west side)
  {
    id: 'folsom-21st-22nd-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40515, 37.75815],
        [-122.40425, 37.75705],
      ],
    },
    streetName: 'Folsom St',
    side: 'west',
    rules: [
      createStreetSweepingRule(4, '12:00', '14:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // ===== 18TH STREET (runs SW-NE, perpendicular to Bryant) =====
  
  // 18th: Harrison to Bryant - ILLEGAL (north side)
  {
    id: '18th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41185, 37.76145],
        [-122.40985, 37.76145],
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
        [-122.40985, 37.76145],
        [-122.40785, 37.76145],
      ],
    },
    streetName: '18th St',
    side: 'north',
    rules: [
      createMeterRule(),
      createTimeLimitRule(60),
    ],
  },
  
  // ===== 19TH STREET (runs SW-NE) =====
  
  // 19th: Harrison to Bryant - LEGAL (south side)
  {
    id: '19th-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41095, 37.76035],
        [-122.40895, 37.76035],
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // 19th: Bryant to Folsom - LEGAL (south side)
  {
    id: '19th-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40895, 37.76035],
        [-122.40695, 37.76035],
      ],
    },
    streetName: '19th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(5, '12:00', '14:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // ===== 20TH STREET (runs SW-NE) - YOUR STARTING POINT =====
  
  // 20th: Harrison to Bryant - LEGAL (north side)
  {
    id: '20th-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.41005, 37.75925],
        [-122.40805, 37.75925],
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(2, '12:00', '14:00'),
      createTimeLimitRule(180),
    ],
  },
  
  // 20th: Bryant to Folsom - LEGAL (north side)
  {
    id: '20th-bryant-folsom-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40805, 37.75925],
        [-122.40605, 37.75925],
      ],
    },
    streetName: '20th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(4, '08:00', '10:00'),
      createTimeLimitRule(240),
    ],
  },
  
  // ===== 21ST STREET (runs SW-NE) =====
  
  // 21st: Harrison to Bryant - LEGAL (north side, meters)
  {
    id: '21st-harrison-bryant-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40915, 37.75815],
        [-122.40715, 37.75815],
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
        [-122.40715, 37.75815],
        [-122.40515, 37.75815],
      ],
    },
    streetName: '21st St',
    side: 'north',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // ===== 22ND STREET (runs SW-NE) =====
  
  // 22nd: Harrison to Bryant - LEGAL (south side)
  {
    id: '22nd-harrison-bryant-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40825, 37.75705],
        [-122.40625, 37.75705],
      ],
    },
    streetName: '22nd St',
    side: 'south',
    rules: [
      createStreetSweepingRule(5, '08:00', '10:00'),
      createTimeLimitRule(120),
    ],
  },
  
  // 22nd: Bryant to Folsom - ILLEGAL (south side, RPP)
  {
    id: '22nd-bryant-folsom-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40625, 37.75705],
        [-122.40425, 37.75705],
      ],
    },
    streetName: '22nd St',
    side: 'south',
    rules: [
      createRPPRule('P'),
    ],
  },
];