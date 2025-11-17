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

// Mock blockfaces with CORRECTED coordinates aligned to actual streets
export const mockBlockfaces: Blockface[] = [
  // ===== BRYANT STREET (runs north-south) =====
  
  // Bryant Street - 24th to 25th (LEGAL - east side)
  {
    id: 'bryant-24th-25th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40975, 37.75265], // 24th St intersection
        [-122.40975, 37.75375], // 25th St intersection
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(3, '08:00', '10:00'), // Wednesday
      createTimeLimitRule(120), // 2-hour limit
    ],
  },
  
  // Bryant Street - 23rd to 24th (ILLEGAL - east side, sweeping now!)
  {
    id: 'bryant-23rd-24th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40975, 37.75155], // 23rd St intersection
        [-122.40975, 37.75265], // 24th St intersection
      ],
    },
    streetName: 'Bryant St',
    side: 'east',
    rules: [
      createStreetSweepingRule(1, '12:00', '14:00'), // Monday noon-2pm - ACTIVE NOW!
    ],
  },
  
  // ===== 24TH STREET (runs east-west) =====
  
  // 24th Street - Bryant to York (LIMITED - north side, meters)
  {
    id: '24th-bryant-york-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40975, 37.75265], // Bryant intersection
        [-122.40775, 37.75265], // York intersection
      ],
    },
    streetName: '24th St',
    side: 'north',
    rules: [
      createMeterRule(),
      createTimeLimitRule(60), // 1-hour limit
    ],
  },
  
  // 24th Street - York to Hampshire (LEGAL - north side, residential)
  {
    id: '24th-york-hampshire-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40775, 37.75265], // York intersection
        [-122.40575, 37.75265], // Hampshire intersection
      ],
    },
    streetName: '24th St',
    side: 'north',
    rules: [
      createStreetSweepingRule(4, '08:00', '10:00'), // Thursday
    ],
  },
  
  // ===== YORK STREET (runs north-south) =====
  
  // York Street - 24th to 25th (LEGAL - west side, best option!)
  {
    id: 'york-24th-25th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40775, 37.75265], // 24th St intersection
        [-122.40775, 37.75375], // 25th St intersection
      ],
    },
    streetName: 'York St',
    side: 'west',
    rules: [
      createStreetSweepingRule(2, '12:00', '14:00'), // Tuesday
      createTimeLimitRule(240), // 4-hour limit
    ],
  },
  
  // York Street - 23rd to 24th (LIMITED - west side, RPP zone)
  {
    id: 'york-23rd-24th-west',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40775, 37.75155], // 23rd St intersection
        [-122.40775, 37.75265], // 24th St intersection
      ],
    },
    streetName: 'York St',
    side: 'west',
    rules: [
      createRPPRule('P'),
      createTimeLimitRule(120), // 2-hour visitor limit
    ],
  },
  
  // ===== HAMPSHIRE STREET (runs north-south) =====
  
  // Hampshire Street - 24th to 25th (LEGAL - east side, quiet residential)
  {
    id: 'hampshire-24th-25th-east',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40575, 37.75265], // 24th St intersection
        [-122.40575, 37.75375], // 25th St intersection
      ],
    },
    streetName: 'Hampshire St',
    side: 'east',
    rules: [
      createStreetSweepingRule(5, '08:00', '10:00'), // Friday
    ],
  },
  
  // ===== 25TH STREET (runs east-west) =====
  
  // 25th Street - Bryant to York (LEGAL - south side)
  {
    id: '25th-bryant-york-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40975, 37.75375], // Bryant intersection
        [-122.40775, 37.75375], // York intersection
      ],
    },
    streetName: '25th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(1, '08:00', '10:00'), // Monday morning
      createTimeLimitRule(120),
    ],
  },
  
  // 25th Street - York to Hampshire (LEGAL - south side)
  {
    id: '25th-york-hampshire-south',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40775, 37.75375], // York intersection
        [-122.40575, 37.75375], // Hampshire intersection
      ],
    },
    streetName: '25th St',
    side: 'south',
    rules: [
      createStreetSweepingRule(3, '12:00', '14:00'), // Wednesday
    ],
  },
  
  // ===== 23RD STREET (runs east-west) =====
  
  // 23rd Street - Bryant to York (LEGAL - north side)
  {
    id: '23rd-bryant-york-north',
    geometry: {
      type: 'LineString',
      coordinates: [
        [-122.40975, 37.75155], // Bryant intersection
        [-122.40775, 37.75155], // York intersection
      ],
    },
    streetName: '23rd St',
    side: 'north',
    rules: [
      createTimeLimitRule(120),
    ],
  },
];