import { Blockface, ParkingRule } from '@/types/parking';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BACKEND_API = `${API_BASE_URL}/api/v1/blockfaces`;

/**
 * Utility functions for formatting days and times
 */

// Convert abbreviated day names to full names
function formatDayName(dayStr: string): string {
  const dayMap: { [key: string]: string } = {
    'Mon': 'Monday',
    'Tue': 'Tuesday',
    'Tues': 'Tuesday',
    'Wed': 'Wednesday',
    'Thu': 'Thursday',
    'Thurs': 'Thursday',
    'Fri': 'Friday',
    'Sat': 'Saturday',
    'Sun': 'Sunday',
    'M': 'Monday',
    'Tu': 'Tuesday',
    'W': 'Wednesday',
    'Th': 'Thursday',
    'F': 'Friday',
    'Sa': 'Saturday',
    'Su': 'Sunday',
  };
  
  // Handle ranges like "M-F" or "Mon-Fri"
  if (dayStr.includes('-')) {
    const parts = dayStr.split('-');
    if (parts.length === 2) {
      const start = dayMap[parts[0].trim()] || parts[0].trim();
      const end = dayMap[parts[1].trim()] || parts[1].trim();
      return `${start}-${end}`;
    }
  }
  
  return dayMap[dayStr] || dayStr;
}

// Convert 24-hour time to 12-hour format with am/pm
function formatTime12Hour(time24: string): string {
  if (!time24 || time24 === '00:00') return 'Midnight';
  if (time24 === '12:00') return 'Noon';
  
  const [hourStr, minuteStr] = time24.split(':');
  const hour = parseInt(hourStr, 10);
  const minute = parseInt(minuteStr, 10);
  
  if (isNaN(hour)) return time24;
  
  const period = hour >= 12 ? 'pm' : 'am';
  const hour12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  
  // Only include minutes if they're not :00
  if (minute && minute !== 0) {
    return `${hour12}:${minuteStr}${period}`;
  }
  
  return `${hour12}${period}`;
}

// Format a time range (e.g., "09:00-11:00" -> "9am-11am")
function formatTimeRange(startTime: string, endTime: string): string {
  return `${formatTime12Hour(startTime)}-${formatTime12Hour(endTime)}`;
}

// Default center (20th & Bryant)
const DEFAULT_CENTER = {
  lat: 37.76272,
  lng: -122.40920,
};

/**
 * Fetch blockfaces from the backend API
 */
export async function fetchSFMTABlockfaces(
  lat: number = DEFAULT_CENTER.lat,
  lng: number = DEFAULT_CENTER.lng,
  radius: number = 1000
): Promise<Blockface[]> {
  try {
    const params = new URLSearchParams({
      lat: lat.toString(),
      lng: lng.toString(),
      radius_meters: Math.round(radius).toString(),
    });

    console.log(`Fetching from ${BACKEND_API}?${params}`);
    const response = await fetch(`${BACKEND_API}?${params}`);
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data = await response.json();
    console.log(`Received ${data.length} blockfaces from backend`);
    return data.map(transformBackendBlockface);
  } catch (error) {
    console.error('Error fetching blockfaces:', error);
    // Return empty array to fallback to mock data if needed (handled in component)
    return [];
  }
}

function transformBackendBlockface(backendData: any): Blockface {
  // Transform schedules to rules
  const rules: ParkingRule[] = [];
  
  // 1. Handle explicit rules from backend (e.g. street sweeping)
  if (backendData.rules && Array.isArray(backendData.rules)) {
    backendData.rules.forEach((rule: any, index: number) => {
      try {
        const transformedRule = transformBackendRule(rule, backendData.id, index);
        if (transformedRule) {
          rules.push(transformedRule);
        }
      } catch (e) {
        console.warn('Failed to transform rule:', rule, e);
      }
    });
  }

  // 2. Handle schedules (implicit meter rules)
  if (backendData.schedules && backendData.schedules.length > 0) {
    // Create a meter rule if we have schedules
    // For S1, we simplify: if schedules exist, treat as standard meter
    
    // Try to find rate
    const rateSchedule = backendData.schedules.find((s: any) => s.rate !== null);
    const rate = rateSchedule ? parseFloat(rateSchedule.rate) : 3.50;

    // Check if we already have a meter rule from the rules array to avoid duplicates
    // (though currently backend seems to separate them)
    const hasMeterRule = rules.some(r => r.type === 'meter');
    
    if (!hasMeterRule) {
      rules.push({
        id: `meter-${backendData.id}`,
        type: 'meter',
        timeRanges: [{
          startTime: '09:00', // Default SF meter hours
          endTime: '18:00',
          daysOfWeek: [1, 2, 3, 4, 5, 6], // Mon-Sat
        }],
        description: 'Metered Parking',
        precedence: 70,
        metadata: {
          meterRate: rate,
        }
      });
    }
  }

  // Handle missing street name
  const streetName = backendData.streetName || 'Unknown Street';

  return {
    id: backendData.id,
    geometry: backendData.geometry,
    streetName: streetName,
    side: parseSide(backendData.side),
    rules: rules,
    fromStreet: backendData.fromStreet,
    toStreet: backendData.toStreet,
    fromAddress: backendData.fromAddress,
    toAddress: backendData.toAddress,
    cardinalDirection: backendData.cardinalDirection ? backendData.cardinalDirection.replace(/\s*Side$/i, '') : undefined
  };
}

/**
 * Helper to transform a single backend rule to frontend structure
 */
function transformBackendRule(rule: any, blockfaceId: string, index: number): ParkingRule | null {
  // Map day string to daysOfWeek array
  const dayMap: { [key: string]: number } = {
    'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'Sun': 0,
    'Tues': 2, 'Thurs': 4, // Add alternative abbreviations
    'Daily': -1 // Special handling
  };
  
  // Handle combined days like "M-F"
  const days: number[] = [];
  
  // Check if this is a parking regulation (has 'days' field) or street sweeping (has 'day' field)
  const dayField = rule.days || rule.day;
  
  if (!dayField) {
    // If no day information, default to all days for safety
    console.warn('Rule has no day information, defaulting to all days:', rule);
    days.push(0, 1, 2, 3, 4, 5, 6);
  } else {
    // Helper to normalize day string
    const normalizedDay = dayField.replace(/\./g, ''); // Remove periods (Mon. -> Mon)

    if (normalizedDay === 'Daily' || normalizedDay === 'All') {
      days.push(0, 1, 2, 3, 4, 5, 6);
    } else if (normalizedDay === 'M-F' || normalizedDay === 'Mon-Fri' || normalizedDay === 'Weekdays') {
      days.push(1, 2, 3, 4, 5);
    } else if (normalizedDay === 'M-Su' || normalizedDay === 'Mon-Sun') {
      days.push(0, 1, 2, 3, 4, 5, 6); // Monday through Sunday = all days
    } else if (normalizedDay === 'M-Sa' || normalizedDay === 'Mon-Sat') {
      days.push(1, 2, 3, 4, 5, 6); // Monday through Saturday
    } else if (normalizedDay === 'S-S' || normalizedDay === 'Sat-Sun' || normalizedDay === 'Weekends') {
      days.push(6, 0);
    } else if (dayMap[normalizedDay] !== undefined) {
      days.push(dayMap[normalizedDay]);
    } else {
      // Try to parse CSV like "Mon, Wed, Fri"
      const parts = normalizedDay.split(/,\s*/);
      let allValid = true;
      for (const part of parts) {
        if (dayMap[part] !== undefined) {
          days.push(dayMap[part]);
        } else {
          allValid = false;
        }
      }
      
      if (!allValid || days.length === 0) {
        console.warn(`Unknown day format: ${dayField}, defaulting to all days`);
        // Default to all days rather than returning null
        days.push(0, 1, 2, 3, 4, 5, 6);
      }
    }
  }

  // Format times (assuming backend sends "0", "6", "12", etc. or "0900")
  // Also handle fromTime/toTime from parking regulations
  const formatTime = (t: string | undefined | null): string => {
    if (!t) return '00:00';
    
    // Handle "900" or "1800" format
    if (t.length >= 3 && /^\d+$/.test(t)) {
      const hour = t.slice(0, -2).padStart(2, '0');
      const min = t.slice(-2);
      return `${hour}:${min}`;
    }

    // Handle simple hour integers (0, 6, 12)
    const hour = parseInt(t, 10);
    if (!isNaN(hour) && t.length <= 2) {
      return `${hour.toString().padStart(2, '0')}:00`;
    }
    
    return t; // Return as is if it's already formatted or complex
  };

  // Handle both street sweeping (startTime/endTime) and parking regulations (fromTime/toTime)
  const startTime = formatTime(rule.startTime || rule.fromTime);
  const endTime = formatTime(rule.endTime || rule.toTime);

  // Map rule type
  let type: any = rule.type;
  let precedence = 50;
  let metadata: any = {};

  switch (rule.type) {
    case 'street-sweeping':
      type = 'street-sweeping';
      precedence = 90;
      break;
    case 'tow-away':
      type = 'tow-away';
      precedence = 100;
      break;
    case 'no-parking':
      type = 'no-parking';
      precedence = 80;
      break;
    case 'parking-regulation':
      // Parse the regulation text to determine actual type
      const regText = (rule.regulation || '').toLowerCase();
      const details = (rule.details || '').toLowerCase();
      
      if (regText.includes('tow') || details.includes('tow')) {
        type = 'tow-away';
        precedence = 100;
      } else if (regText.includes('no parking') || regText.includes('no stopping')) {
        type = 'no-parking';
        precedence = 80;
      } else if (rule.timeLimit || regText.includes('hour') || regText.includes('hr')) {
        type = 'time-limit';
        precedence = 60;
        metadata.timeLimit = rule.timeLimit ? parseInt(rule.timeLimit) * 60 : 120; // Convert hours to minutes
      } else if (rule.permitArea || regText.includes('permit') || regText.includes('residential')) {
        type = 'rpp-zone';
        precedence = 70;
        metadata.permitZone = rule.permitArea;
      } else {
        // Default to no-parking for unknown regulations
        type = 'no-parking';
        precedence = 80;
      }
      break;
    case 'rpp': // Backend might call it 'rpp'
    case 'rpp-zone':
      type = 'rpp-zone';
      precedence = 70;
      metadata.permitZone = rule.permitArea;
      break;
    default:
      // Default to no-parking if unknown but restrictive
      if (!['street-sweeping', 'tow-away', 'no-parking', 'meter', 'time-limit', 'rpp-zone'].includes(type)) {
        console.warn(`Unknown rule type: ${type}, defaulting to no-parking`);
        type = 'no-parking';
        precedence = 80;
      }
  }

  // Build a better description with proper formatting
  let description = rule.description || rule.details || '';
  
  // If no description or it's generic, build one from the data
  if (!description || description === type) {
    // Format the day field to full day names
    const formattedDay = dayField ? formatDayName(dayField) : '';
    // Format the time range
    const formattedTimeRange = formatTimeRange(startTime, endTime);
    
    if (type === 'time-limit' && metadata.timeLimit) {
      const hours = metadata.timeLimit / 60;
      description = `${hours} hr time limit ${formattedDay} ${formattedTimeRange}`;
      if (metadata.permitZone) {
        description += `, permit holder ${metadata.permitZone} exempt`;
      }
    } else if (type === 'rpp-zone' && metadata.permitZone) {
      description = `Residential Permit Zone ${metadata.permitZone}`;
    } else if (type === 'street-sweeping') {
      description = `Street Cleaning ${formattedDay} ${formattedTimeRange}`;
    } else {
      description = `${type} ${formattedDay} ${formattedTimeRange}`;
    }
  } else {
    // If we have a description, expand abbreviated days to full names
    description = description
      .replace(/\bMon\b/g, 'Monday')
      .replace(/\bTues?\b/g, 'Tuesday')
      .replace(/\bWed\b/g, 'Wednesday')
      .replace(/\bThurs?\b/g, 'Thursday')
      .replace(/\bFri\b/g, 'Friday')
      .replace(/\bSat\b/g, 'Saturday')
      .replace(/\bSun\b/g, 'Sunday');
    
    // Format time ranges in the description (e.g., "9-11" -> "9am-11am")
    description = description.replace(/\b(\d{1,2})-(\d{1,2})\b/g, (match, start, end) => {
      const startFormatted = formatTime12Hour(`${start.padStart(2, '0')}:00`);
      const endFormatted = formatTime12Hour(`${end.padStart(2, '0')}:00`);
      return `${startFormatted}-${endFormatted}`;
    });
  }
  
  return {
    id: `${blockfaceId}-${type}-${index}`,
    type: type,
    timeRanges: [{
      startTime,
      endTime,
      daysOfWeek: days,
    }],
    description: description,
    precedence: precedence,
    metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
  };
}

/**
 * Parses side of street string into a valid type
 */
function parseSide(side: any): 'north' | 'south' | 'east' | 'west' | 'L' | 'R' {
  if (typeof side !== 'string' || side.length === 0) {
    return 'east'; // A sensible default
  }
  
  // Handle direct L/R from backend
  if (side === 'L') return 'L';
  if (side === 'R') return 'R';

  const lowerSide = side.toLowerCase();
  if (lowerSide.startsWith('n')) return 'north';
  if (lowerSide.startsWith('s')) return 'south';
  if (lowerSide.startsWith('e')) return 'east';
  if (lowerSide.startsWith('w')) return 'west';
  return 'east'; // Fallback for other values
}

/**
 * Submit an error report to the backend
 */
export async function submitErrorReport(
  blockfaceId: string,
  description: string
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/error-reports`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      blockfaceId,
      description,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit error report: ${response.statusText}`);
  }
}

/**
 * Clear cached data
 * (Kept for compatibility with existing calls)
 */
export function clearSFMTACache(): void {
  // No-op for now as we don't cache in localStorage anymore
  console.log('Cache cleared (no-op)');
}