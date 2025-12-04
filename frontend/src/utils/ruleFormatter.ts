import { ParkingRule } from '@/types/parking';

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_NAMES_FULL = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

interface GroupedRule {
  description: string;
  timeRanges: Array<{
    startTime: string;
    endTime: string;
    days: number[];
  }>;
}

/**
 * Formats parking rules by merging same restrictions across multiple days
 * Example: "1hr parking 8am-6pm Mon-Fri" instead of separate lines per day
 */
export function formatRulesForDisplay(rules: ParkingRule[]): string[] {
  if (!rules || rules.length === 0) return [];

  try {
    // Group rules by base description + time to merge holidays with regular days
    const ruleGroups = new Map<string, { days: number[], hasHoliday: boolean, rate?: number }>();

    rules.forEach(rule => {
      // Safety check
      if (!rule || !rule.timeRanges || !Array.isArray(rule.timeRanges) || rule.timeRanges.length === 0) return;
      
      // Group time ranges by their time (startTime-endTime)
      const timeGroups = new Map<string, number[]>();
      
      rule.timeRanges.forEach(range => {
        if (!range || !range.startTime || !range.endTime || !range.daysOfWeek || !Array.isArray(range.daysOfWeek)) return;
        const timeKey = `${range.startTime}-${range.endTime}`;
        const existingDays = timeGroups.get(timeKey) || [];
        timeGroups.set(timeKey, [...existingDays, ...range.daysOfWeek]);
      });
      
      // Skip if no valid time groups were created
      if (timeGroups.size === 0) return;
      
      // Format each time group
      timeGroups.forEach((days, timeKey) => {
      const [startTime, endTime] = timeKey.split('-');
      
      // Format the rule description (remove existing time/day info if present)
      let baseDescription = (rule.description || 'Unknown rule')
        .replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).*/i, '')
        .replace(/\s+\d{1,2}:\d{2}\s*(AM|PM|am|pm).*/i, '')
        .replace(/\s+Daily/i, '') // Remove "Daily" from description
        .trim();
      
      if (!baseDescription) baseDescription = 'Parking rule';
      
      // Extract "except Zone X" suffix to append at the end
      let exceptSuffix = '';
      const exceptMatch = baseDescription.match(/\s+(except\s+Zone\s+\w+)$/i);
      if (exceptMatch) {
        exceptSuffix = ` ${exceptMatch[1]}`;
        baseDescription = baseDescription.replace(/\s+except\s+Zone\s+\w+$/i, '').trim();
      }
      
      // Check if this is a holiday rule
      const isHolidayRule = baseDescription.toLowerCase().includes('holiday');
      
      // Remove "Holiday" from description for grouping
      const cleanDescription = baseDescription.replace(/\s*Holiday\s*/i, '').trim();
      
      // Simplify oversized vehicle restrictions
      if (cleanDescription.toLowerCase().includes('oversized') ||
          cleanDescription.toLowerCase().includes('over-sized') ||
          (cleanDescription.toLowerCase().includes('vehicle') && cleanDescription.toLowerCase().includes('trailer'))) {
        baseDescription = 'No parking for oversized vehicles and trailers';
      } else {
        baseDescription = cleanDescription;
      }
      
      // Standardize time units: "1 hr" -> "1hr", "30 min" -> "30min", etc.
      baseDescription = baseDescription
        .replace(/(\d+)\s*(hr|hour)s?/gi, '$1hr')
        .replace(/(\d+)\s*(min|minute)s?/gi, '$1min');
      
      // Format time (convert 24h to 12h format)
      const formattedTime = formatTimeRange(startTime, endTime);
      
      // Extract meter rate if this is a metered parking rule
      const meterRate = rule.type === 'meter' && rule.metadata?.meterRate
        ? rule.metadata.meterRate
        : undefined;
      
      // Create group key (include exceptSuffix for proper grouping)
      const groupKey = `${baseDescription}|${formattedTime}|${exceptSuffix}`;
      
      // Get or create group
      const existing = ruleGroups.get(groupKey) || { days: [], hasHoliday: false };
      
      if (isHolidayRule) {
        existing.hasHoliday = true;
      } else {
        // Remove duplicates and add days
        const uniqueDays = Array.from(new Set(days));
        existing.days = Array.from(new Set([...existing.days, ...uniqueDays])).sort((a, b) => a - b);
      }
      
      // Store meter rate if available
      if (meterRate !== undefined) {
        existing.rate = meterRate;
      }
      
        ruleGroups.set(groupKey, existing);
      });
    });

    // Format the grouped rules
    const formatted: string[] = [];
    ruleGroups.forEach((group, key) => {
      const parts = key.split('|');
      const baseDescription = parts[0];
      const formattedTime = parts[1];
      const exceptSuffix = parts[2] || '';
      
      // Check if this is metered parking
      const isMetered = baseDescription.toLowerCase().includes('meter');
      
      // Format days
      const formattedDays = group.days.length > 0 ? formatDays(group.days) : '';
      
      // Build final string with exceptSuffix at the end
      if (isMetered && group.rate) {
        // Metered parking format: "Metered ($3.50/hr) 9am-6pm Mon-Fri"
        const rateStr = `($${group.rate.toFixed(2)}/hr)`;
        if (formattedDays && group.hasHoliday) {
          formatted.push(`Metered ${rateStr} ${formattedTime} ${formattedDays} including Holidays${exceptSuffix}`);
        } else if (formattedDays) {
          formatted.push(`Metered ${rateStr} ${formattedTime} ${formattedDays}${exceptSuffix}`);
        } else if (group.hasHoliday) {
          formatted.push(`Metered ${rateStr} ${formattedTime} Holidays${exceptSuffix}`);
        } else {
          formatted.push(`Metered ${rateStr} ${formattedTime}${exceptSuffix}`);
        }
      } else if (formattedDays && group.hasHoliday) {
        formatted.push(`${baseDescription} ${formattedTime} ${formattedDays} including Holidays${exceptSuffix}`);
      } else if (formattedDays) {
        formatted.push(`${baseDescription} ${formattedTime} ${formattedDays}${exceptSuffix}`);
      } else if (group.hasHoliday) {
        formatted.push(`${baseDescription} ${formattedTime} Holidays${exceptSuffix}`);
      } else {
        formatted.push(`${baseDescription} ${formattedTime}${exceptSuffix}`);
      }
    });

    return formatted;
  } catch (error) {
    console.error('Error formatting rules:', error, rules);
    // Fallback: return raw descriptions
    return rules.map(r => r.description || 'Unknown rule');
  }
}

/**
 * Formats time range from 24h to 12h format
 * Example: "08:00-18:00" → "8am-6pm"
 */
function formatTimeRange(start: string, end: string): string {
  const formatTime = (time: string): string => {
    // Safety check
    if (!time || typeof time !== 'string') return '12am';
    
    const parts = time.split(':');
    if (parts.length !== 2) return '12am';
    
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    
    if (isNaN(hours) || isNaN(minutes)) return '12am';
    
    const period = hours >= 12 ? 'pm' : 'am';
    const hour12 = hours % 12 || 12;
    
    // Only show minutes if not :00
    if (minutes === 0) {
      return `${hour12}${period}`;
    }
    return `${hour12}:${minutes.toString().padStart(2, '0')}${period}`;
  };

  return `${formatTime(start)}-${formatTime(end)}`;
}

/**
 * Formats day list with smart grouping
 * Examples:
 * - [1,2,3,4,5] → "Mon-Fri"
 * - [1,2,3,4,5,6] → "except Sun"
 * - [1,3,5] → "Mon, Wed, Fri"
 * - [0,1,2,3,4,5,6] → "Daily"
 */
function formatDays(days: number[]): string {
  // All 7 days
  if (days.length === 7) {
    return 'Daily';
  }
  
  // Mon-Sat (except Sunday)
  if (days.length === 6 && !days.includes(0)) {
    return 'except Sun';
  }
  
  // Sun-Fri (except Saturday)
  if (days.length === 6 && !days.includes(6)) {
    return 'except Sat';
  }
  
  // Check for consecutive ranges
  const ranges = findConsecutiveRanges(days);
  
  if (ranges.length === 1 && ranges[0].length > 2) {
    // Single consecutive range of 3+ days
    const range = ranges[0];
    return `${DAY_NAMES[range[0]]}-${DAY_NAMES[range[range.length - 1]]}`;
  }
  
  // Multiple ranges or non-consecutive days - list them
  return days.map(d => DAY_NAMES[d]).join(', ');
}

/**
 * Finds consecutive day ranges
 * Example: [1,2,3,5,6] → [[1,2,3], [5,6]]
 */
function findConsecutiveRanges(days: number[]): number[][] {
  if (days.length === 0) return [];
  
  const ranges: number[][] = [];
  let currentRange: number[] = [days[0]];
  
  for (let i = 1; i < days.length; i++) {
    if (days[i] === days[i - 1] + 1) {
      currentRange.push(days[i]);
    } else {
      ranges.push(currentRange);
      currentRange = [days[i]];
    }
  }
  ranges.push(currentRange);
  
  return ranges;
}