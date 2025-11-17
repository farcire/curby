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

// Mock blockfaces for Mission + SOMA
export const mockBlockfaces: Blockface[] = [
  // Valencia Street (Mission) - Popular corridor
  {
    id: 'valencia-16th-17th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4215, 37.7649],
        [-122.4215, 37.7659],
      ],
    },
    streetName: 'Valencia St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'), // Tuesday
      createMeterRule(),
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  {
    id: 'valencia-17th-18th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4215, 37.7659],
        [-122.4215, 37.7669],
      ],
    },
    streetName: 'Valencia St',
    side: 'east',
    rules: [
      createStreetSweepingRule(2, '08:00', '10:00'),
      createMeterRule(),
      createTimeLimitRule(120),
    ],
  },
  // Mission Street - High traffic area
  {
    id: 'mission-16th-17th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4194, 37.7649],
        [-122.4194, 37.7659],
      ],
    },
    streetName: 'Mission St',
    side: 'west',
    rules: [
      createStreetSweepingRule(4, '12:00', '14:00'), // Thursday
      createMeterRule(),
      createTimeLimitRule(60), // 1-hour limit
    ],
  },
  // 18th Street - Residential with RPP
  {
    id: '18th-valencia-guerrero-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4215, 37.7614],
        [-122.4235, 37.7614],
      ],
    },
    streetName: '18th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'), // Monday
      createRPPRule('M'),
      createTimeLimitRule(120),
    ],
  },
  // Folsom Street (SOMA) - Mixed use
  {
    id: 'folsom-9th-10th-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4125, 37.7745],
        [-122.4125, 37.7755],
      ],
    },
    streetName: 'Folsom St',
    side: 'south',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'), // Wednesday
      createMeterRule(),
    ],
  },
  // Howard Street (SOMA) - Tow-away zone example
  {
    id: 'howard-8th-9th-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4105, 37.7735],
        [-122.4105, 37.7745],
      ],
    },
    streetName: 'Howard St',
    side: 'north',
    rules: [
      {
        id: 'tow-away-rush',
        type: 'tow-away',
        timeRanges: [{
          startTime: '07:00',
          endTime: '09:00',
          daysOfWeek: [1, 2, 3, 4, 5],
        }],
        description: 'Tow-away zone Mon-Fri 7-9am',
        precedence: PRECEDENCE['tow-away'],
      },
      createMeterRule(),
    ],
  },
  // 20th Street - Simple residential
  {
    id: '20th-mission-valencia-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4194, 37.7594],
        [-122.4215, 37.7594],
      ],
    },
    streetName: '20th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(5, '12:00', '14:00'), // Friday
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  // Guerrero Street - Mostly legal
  {
    id: 'guerrero-17th-18th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4235, 37.7659],
        [-122.4235, 37.7669],
      ],
    },
    streetName: 'Guerrero St',
    side: 'west',
    rules: [
      createStreetSweepingRule(2, '12:00', '14:00'),
    ],
  },
  // 11th Street (SOMA) - No parking example
  {
    id: '11th-folsom-harrison-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4125, 37.7765],
        [-122.4145, 37.7765],
      ],
    },
    streetName: '11th St',
    side: 'north',
    rules: [
      {
        id: 'no-parking-anytime',
        type: 'no-parking',
        timeRanges: [{
          startTime: '00:00',
          endTime: '23:59',
          daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
        }],
        description: 'No parking anytime',
        precedence: PRECEDENCE['no-parking'],
      },
    ],
  },
  // Harrison Street - Insufficient data example
  {
    id: 'harrison-10th-11th-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.4145, 37.7755],
        [-122.4145, 37.7765],
      ],
    },
    streetName: 'Harrison St',
    side: 'south',
    rules: [], // No rules = insufficient data
  },
];