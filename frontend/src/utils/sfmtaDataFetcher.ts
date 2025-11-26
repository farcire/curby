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
      radius_meters: radius.toString(),
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
  
  if (backendData.schedules && backendData.schedules.length > 0) {
    // Create a meter rule if we have schedules
    // For S1, we simplify: if schedules exist, treat as standard meter
    
    // Try to find rate
    const rateSchedule = backendData.schedules.find((s: any) => s.rate !== null);
    const rate = rateSchedule ? parseFloat(rateSchedule.rate) : 3.50;

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