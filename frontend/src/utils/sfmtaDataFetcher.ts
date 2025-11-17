import { Blockface, ParkingRule } from '@/types/parking';

const SFMTA_METERS_API = 'https://data.sfgov.org/resource/fqfu-vcqd.json';
const SFMTA_REGULATIONS_API = 'https://data.sfgov.org/resource/qbyz-te2i.json';
const CACHE_KEY = 'curby-sfmta-data';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Expanded Mission + SOMA bounding box (approximate)
const MISSION_SOMA_BOUNDS = {
  minLat: 37.74,
  maxLat: 37.79,
  minLng: -122.44,
  maxLng: -122.38,
};

// Bryant & 24th area (tighter bounds for demo)
const DEMO_AREA_BOUNDS = {
  minLat: 37.751,
  maxLat: 37.755,
  minLng: -122.411,
  maxLng: -122.403,
};

interface CachedData {
  timestamp: number;
  blockfaces: Blockface[];
}

/**
 * Check if coordinates are within bounds
 */
function isInBounds(lat: number, lng: number, bounds = MISSION_SOMA_BOUNDS): boolean {
  return (
    lat >= bounds.minLat &&
    lat <= bounds.maxLat &&
    lng >= bounds.minLng &&
    lng <= bounds.maxLng
  );
}

/**
 * Fetch data from SFMTA with error handling
 */
async function fetchSFMTAData(url: string, params: Record<string, string> = {}): Promise<any[]> {
  try {
    const queryParams = new URLSearchParams({
      $limit: '5000', // Get more records
      ...params,
    });

    const response = await fetch(`${url}?${queryParams}`);
    
    if (!response.ok) {
      throw new Error(`SFMTA API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching SFMTA data:', error);
    return [];
  }
}

/**
 * Parse SFMTA meter data into parking rules
 */
function parseMeterData(meterData: any[]): Map<string, ParkingRule[]> {
  const rulesByStreet = new Map<string, ParkingRule[]>();

  for (const meter of meterData) {
    if (!meter.location?.coordinates) continue;

    const [lng, lat] = meter.location.coordinates;
    if (!isInBounds(lat, lng)) continue;

    const streetKey = `${meter.street_name || 'Unknown'}-${meter.street_segment || ''}`;
    
    const meterRule: ParkingRule = {
      id: `meter-${meter.post_id || Math.random()}`,
      type: 'meter',
      timeRanges: [{
        startTime: meter.active_hours_start || '09:00',
        endTime: meter.active_hours_end || '18:00',
        daysOfWeek: parseDaysOfWeek(meter.active_days || 'Mon-Fri'),
      }],
      description: `Meter parking required ${meter.active_days || 'Mon-Fri'} ${meter.active_hours_start || '9am'}-${meter.active_hours_end || '6pm'}`,
      precedence: 70,
      metadata: {
        meterRate: parseFloat(meter.rate_per_hour || '3.50'),
      },
    };

    if (!rulesByStreet.has(streetKey)) {
      rulesByStreet.set(streetKey, []);
    }
    rulesByStreet.get(streetKey)!.push(meterRule);
  }

  return rulesByStreet;
}

/**
 * Parse SFMTA regulation data into parking rules
 */
function parseRegulationData(regulationData: any[]): Map<string, ParkingRule[]> {
  const rulesByStreet = new Map<string, ParkingRule[]>();

  for (const regulation of regulationData) {
    if (!regulation.geometry?.coordinates) continue;

    // Handle different geometry types
    let coordinates: [number, number][] = [];
    if (regulation.geometry.type === 'LineString') {
      coordinates = regulation.geometry.coordinates;
    } else if (regulation.geometry.type === 'MultiLineString') {
      coordinates = regulation.geometry.coordinates[0] || [];
    }

    if (coordinates.length === 0) continue;

    // Check if any point is in bounds
    const inBounds = coordinates.some(([lng, lat]) => isInBounds(lat, lng));
    if (!inBounds) continue;

    const streetKey = `${regulation.street_name || 'Unknown'}-${regulation.cnn || ''}`;
    
    const rules = parseRegulationRules(regulation);
    
    if (!rulesByStreet.has(streetKey)) {
      rulesByStreet.set(streetKey, []);
    }
    rulesByStreet.get(streetKey)!.push(...rules);
  }

  return rulesByStreet;
}

/**
 * Parse individual regulation into rules
 */
function parseRegulationRules(regulation: any): ParkingRule[] {
  const rules: ParkingRule[] = [];

  // Street sweeping
  if (regulation.street_sweeping_schedule && typeof regulation.street_sweeping_schedule === 'string') {
    const sweepingRule: ParkingRule = {
      id: `sweep-${regulation.cnn || Math.random()}`,
      type: 'street-sweeping',
      timeRanges: parseTimeRanges(regulation.street_sweeping_schedule),
      description: `Street sweeping ${regulation.street_sweeping_schedule}`,
      precedence: 90,
    };
    rules.push(sweepingRule);
  }

  // Time limits
  if (regulation.time_limit_minutes) {
    const timeLimitRule: ParkingRule = {
      id: `time-limit-${regulation.cnn || Math.random()}`,
      type: 'time-limit',
      timeRanges: [{
        startTime: '08:00',
        endTime: '20:00',
        daysOfWeek: [1, 2, 3, 4, 5, 6],
      }],
      description: `${regulation.time_limit_minutes / 60}-hour parking limit`,
      precedence: 60,
      metadata: {
        timeLimit: parseInt(regulation.time_limit_minutes),
      },
    };
    rules.push(timeLimitRule);
  }

  // RPP zones
  if (regulation.rpp_area) {
    const rppRule: ParkingRule = {
      id: `rpp-${regulation.cnn || Math.random()}`,
      type: 'rpp-zone',
      timeRanges: [{
        startTime: '00:00',
        endTime: '23:59',
        daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
      }],
      description: `Residential Permit Zone ${regulation.rpp_area} required`,
      precedence: 50,
      metadata: {
        permitZone: regulation.rpp_area,
      },
    };
    rules.push(rppRule);
  }

  // No parking
  if (typeof regulation.regulation_type === 'string' && regulation.regulation_type.toLowerCase().includes('no parking')) {
    const noParkingRule: ParkingRule = {
      id: `no-parking-${regulation.cnn || Math.random()}`,
      type: 'no-parking',
      timeRanges: [{
        startTime: '00:00',
        endTime: '23:59',
        daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
      }],
      description: regulation.regulation_description || 'No parking anytime',
      precedence: 80,
    };
    rules.push(noParkingRule);
  }

  return rules;
}

/**
 * Parse days of week string into array
 */
function parseDaysOfWeek(daysStr: string): number[] {
  if (typeof daysStr !== 'string') {
    return [1, 2, 3, 4, 5]; // Default to weekdays
  }
  const days: number[] = [];
  const lower = daysStr.toLowerCase();

  if (lower.includes('mon')) days.push(1);
  if (lower.includes('tue')) days.push(2);
  if (lower.includes('wed')) days.push(3);
  if (lower.includes('thu')) days.push(4);
  if (lower.includes('fri')) days.push(5);
  if (lower.includes('sat')) days.push(6);
  if (lower.includes('sun')) days.push(0);

  // Default to weekdays if nothing parsed
  return days.length > 0 ? days : [1, 2, 3, 4, 5];
}

/**
 * Parse time range strings
 */
function parseTimeRanges(scheduleStr: string): Array<{ startTime: string; endTime: string; daysOfWeek: number[] }> {
  // This is simplified - real parsing would be more complex
  // Example: "Tuesday 8am-10am"
  const days = parseDaysOfWeek(scheduleStr);
  
  // Extract times (simplified)
  let startTime = '08:00';
  let endTime = '10:00';
  
  const timeMatch = scheduleStr.match(/(\d+)(am|pm)-(\d+)(am|pm)/i);
  if (timeMatch) {
    const [, start, startPeriod, end, endPeriod] = timeMatch;
    startTime = convertTo24Hour(parseInt(start), startPeriod);
    endTime = convertTo24Hour(parseInt(end), endPeriod);
  }

  return [{
    startTime,
    endTime,
    daysOfWeek: days,
  }];
}

/**
 * Convert 12-hour time to 24-hour format
 */
function convertTo24Hour(hour: number, period: string): string {
  let h = hour;
  if (period.toLowerCase() === 'pm' && h !== 12) h += 12;
  if (period.toLowerCase() === 'am' && h === 12) h = 0;
  return `${h.toString().padStart(2, '0')}:00`;
}

/**
 * Parses side of street string into a valid type
 */
function parseSide(side: any): 'north' | 'south' | 'east' | 'west' {
  if (typeof side !== 'string' || side.length === 0) {
    return 'east'; // A sensible default
  }
  const lowerSide = side.toLowerCase();
  if (lowerSide.startsWith('n')) return 'north';
  if (lowerSide.startsWith('s')) return 'south';
  if (lowerSide.startsWith('e')) return 'east';
  if (lowerSide.startsWith('w')) return 'west';
  return 'east'; // Fallback for other values
}

/**
 * Convert SFMTA data to Blockface format
 */
function convertToBlockfaces(
  regulationData: any[],
  meterRules: Map<string, ParkingRule[]>,
  regulationRules: Map<string, ParkingRule[]>
): Blockface[] {
  const blockfaces: Blockface[] = [];

  for (const regulation of regulationData) {
    if (!regulation.geometry?.coordinates) continue;

    let coordinates: [number, number][] = [];
    if (regulation.geometry.type === 'LineString') {
      coordinates = regulation.geometry.coordinates;
    } else if (regulation.geometry.type === 'MultiLineString') {
      coordinates = regulation.geometry.coordinates[0] || [];
    }

    if (coordinates.length === 0) continue;

    const inBounds = coordinates.some(([lng, lat]) => isInBounds(lat, lng));
    if (!inBounds) continue;

    const streetKey = `${regulation.street_name || 'Unknown'}-${regulation.cnn || ''}`;
    const rules = [
      ...(meterRules.get(streetKey) || []),
      ...(regulationRules.get(streetKey) || []),
    ];

    const blockface: Blockface = {
      id: `sfmta-${regulation.cnn || Math.random()}`,
      geometry: {
        type: 'LineString',
        coordinates,
      },
      streetName: regulation.street_name || 'Unknown Street',
      side: parseSide(regulation.side),
      rules,
    };

    blockfaces.push(blockface);
  }

  return blockfaces;
}

/**
 * Main function to fetch and parse SFMTA data
 */
export async function fetchSFMTABlockfaces(): Promise<Blockface[]> {
  // Check cache first
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    try {
      const data: CachedData = JSON.parse(cached);
      if (Date.now() - data.timestamp < CACHE_DURATION) {
        console.log('Using cached SFMTA data');
        return data.blockfaces;
      }
    } catch (error) {
      console.error('Error parsing cached data:', error);
    }
  }

  console.log('Fetching fresh SFMTA data...');

  // Fetch both datasets
  const [meterData, regulationData] = await Promise.all([
    fetchSFMTAData(SFMTA_METERS_API),
    fetchSFMTAData(SFMTA_REGULATIONS_API),
  ]);

  if (meterData.length === 0 && regulationData.length === 0) {
    throw new Error('Failed to fetch SFMTA data');
  }

  // Parse data
  const meterRules = parseMeterData(meterData);
  const regulationRules = parseRegulationData(regulationData);

  // Convert to blockfaces
  const blockfaces = convertToBlockfaces(regulationData, meterRules, regulationRules);

  // Cache the results
  const cacheData: CachedData = {
    timestamp: Date.now(),
    blockfaces,
  };
  localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));

  console.log(`Loaded ${blockfaces.length} blockfaces from SFMTA data`);
  return blockfaces;
}

/**
 * Clear cached data
 */
export function clearSFMTACache(): void {
  localStorage.removeItem(CACHE_KEY);
}