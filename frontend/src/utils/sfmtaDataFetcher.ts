import { Blockface, ParkingRule } from '@/types/parking';

const BACKEND_API = 'http://localhost:8000/api/v1/blockfaces';

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
  
  // Helper to normalize day string
  const normalizedDay = rule.day.replace(/\./g, ''); // Remove periods (Mon. -> Mon)

  if (normalizedDay === 'Daily') {
    days.push(0, 1, 2, 3, 4, 5, 6);
  } else if (normalizedDay === 'M-F' || normalizedDay === 'Mon-Fri') {
    days.push(1, 2, 3, 4, 5);
  } else if (normalizedDay === 'S-S' || normalizedDay === 'Sat-Sun') {
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
      console.warn(`Unknown day format: ${rule.day}`);
      // Fallback: If description exists, we might want to show it even if we can't parse logic
      // But for now return null to be safe
      return null;
    }
  }

  // Format times (assuming backend sends "0", "6", "12", etc. or "0900")
  // Based on curl output, we saw "0" and "6".
  // Regulations sample saw "900" and "1800".
  const formatTime = (t: string): string => {
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

  const startTime = formatTime(rule.startTime);
  const endTime = formatTime(rule.endTime);

  // Map rule type
  let type: any = rule.type;
  let precedence = 50;

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
    case 'rpp': // Backend might call it 'rpp'
    case 'rpp-zone':
      type = 'rpp-zone';
      precedence = 50;
      break;
    default:
      // Default to no-parking if unknown but restrictive, or maybe ignore?
      // For now let's keep it if it maps to our types, otherwise null
      if (!['street-sweeping', 'tow-away', 'no-parking', 'meter', 'time-limit', 'rpp-zone'].includes(type)) {
        console.warn(`Unknown rule type: ${type}`);
        return null;
      }
  }

  return {
    id: `${blockfaceId}-${type}-${index}`,
    type: type,
    timeRanges: [{
      startTime,
      endTime,
      daysOfWeek: days,
    }],
    description: rule.description || `${type} ${rule.day} ${startTime}-${endTime}`,
    precedence: precedence,
  };
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
 * Submit an error report to the backend
 */
export async function submitErrorReport(
  blockfaceId: string,
  description: string
): Promise<void> {
  const url = 'http://localhost:8000/api/v1/error-reports';
  
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