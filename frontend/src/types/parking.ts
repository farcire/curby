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
  side: 'north' | 'south' | 'east' | 'west' | 'L' | 'R'; // Added L/R for new backend
  rules: ParkingRule[];
  rules_display?: string[]; // Deprecated: Use interpretation.rules_display instead
  fromStreet?: string; // Optional limits
  toStreet?: string;
  fromAddress?: number | string;
  toAddress?: number | string;
  cardinalDirection?: string;
  interpretation?: {
    version?: string;
    generated_at?: string;
    parking_status?: {
      status?: string;
      status_text?: string;
      severity?: string;
      user_can_park?: boolean;
      has_meters?: boolean;
      has_time_limits?: boolean;
      has_street_cleaning?: boolean;
      has_rpp?: boolean;
      has_tow_away?: boolean;
      is_unrestricted?: boolean;
    };
    rules_display?: string[]; // Pre-formatted display strings like "3hr limit Weekdays 8am-6pm except permit"
    meter_info?: {
      has_meters?: boolean;
      meter_count?: number;
    };
    next_restriction?: {
      type?: string;
      datetime_iso?: string;
      display?: string;
      days_until?: number;
    };
    manual_overrides_applied?: string[];
    location_display?: {
      location_text?: string;
      cross_streets_text?: string;
      street_name?: string;
      cardinal_direction?: string;
      address_range?: string;
    };
  };
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