export type LegalityStatus = 'legal' | 'illegal' | 'insufficient-data';

export type RuleType = 
  | 'tow-away'
  | 'street-sweeping'
  | 'no-parking'
  | 'meter'
  | 'time-limit'
  | 'rpp-zone';

export interface TimeRange {
  startTime: string; // HH:mm format
  endTime: string;
  daysOfWeek: number[]; // 0=Sunday, 6=Saturday
}

export interface ParkingRule {
  id: string;
  type: RuleType;
  timeRanges: TimeRange[];
  description: string;
  precedence: number; // Higher = more restrictive
  metadata?: {
    timeLimit?: number; // minutes
    meterRate?: number; // dollars per hour
    permitZone?: string;
  };
}

export interface Blockface {
  id: string;
  geometry: {
    type: 'LineString';
    coordinates: [number, number][]; // [lng, lat]
  };
  streetName: string;
  side: 'north' | 'south' | 'east' | 'west';
  rules: ParkingRule[];
}

export interface LegalityResult {
  status: LegalityStatus;
  explanation: string;
  applicableRules: ParkingRule[];
  warnings?: string[];
}

export interface ErrorReport {
  id: string;
  blockfaceId: string;
  location: {
    lat: number;
    lng: number;
  };
  description: string;
  timestamp: string;
}