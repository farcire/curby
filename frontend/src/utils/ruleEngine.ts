import { ParkingRule, LegalityResult, LegalityStatus, Blockface } from '@/types/parking';
import { addMinutes, getDay, format } from 'date-fns';

/**
 * Evaluates parking legality for a blockface at a specific time and duration
 * Returns simplified status: legal (green) or illegal (red)
 * Rule: If you can park for the FULL duration without any restrictions, it's legal. Otherwise, illegal.
 */
export function evaluateLegality(
  blockface: Blockface,
  checkTime: Date,
  durationMinutes: number
): LegalityResult {
  // Handle insufficient data case
  if (!blockface.rules || blockface.rules.length === 0) {
    return {
      status: 'insufficient-data',
      explanation: 'No parking data available for this location. Always check signs on-site!',
      applicableRules: [],
      warnings: ['Always verify parking signs at the location'],
    };
  }

  const endTime = addMinutes(checkTime, durationMinutes);
  const applicableRules: ParkingRule[] = [];
  
  // Check each rule to see if it applies during the parking duration
  for (const rule of blockface.rules) {
    if (ruleAppliesDuringPeriod(rule, checkTime, endTime)) {
      applicableRules.push(rule);
    }
  }

  // If no rules apply, it's legal
  if (applicableRules.length === 0) {
    return {
      status: 'legal',
      explanation: 'You can park here! No restrictions apply during your time.',
      applicableRules: [],
      warnings: ['Always verify parking signs at the location'],
    };
  }

  // Sort by precedence (highest first)
  applicableRules.sort((a, b) => b.precedence - a.precedence);

  const primaryRule = applicableRules[0];
  
  // Generate explanation based on rule type
  return generateLegalityResult(primaryRule, applicableRules, durationMinutes);
}

/**
 * Checks if a rule applies during the specified time period
 */
function ruleAppliesDuringPeriod(
  rule: ParkingRule,
  startTime: Date,
  endTime: Date
): boolean {
  for (const timeRange of rule.timeRanges) {
    // Check if any day in the period matches the rule's days
    let currentCheck = new Date(startTime);
    while (currentCheck <= endTime) {
      const dayOfWeek = getDay(currentCheck);
      
      if (timeRange.daysOfWeek.includes(dayOfWeek)) {
        // Check if time overlaps
        const checkTimeStr = format(currentCheck, 'HH:mm');
        if (timeOverlaps(checkTimeStr, timeRange.startTime, timeRange.endTime)) {
          return true;
        }
      }
      
      // Move to next day
      currentCheck = addMinutes(currentCheck, 60);
    }
  }
  
  return false;
}

/**
 * Checks if a time falls within a range
 */
function timeOverlaps(checkTime: string, rangeStart: string, rangeEnd: string): boolean {
  return checkTime >= rangeStart && checkTime <= rangeEnd;
}

/**
 * Generates a legality result with plain-language explanation
 * Simplified to return only 'legal' or 'illegal'
 */
function generateLegalityResult(
  primaryRule: ParkingRule,
  allRules: ParkingRule[],
  durationMinutes: number
): LegalityResult {
  let status: LegalityStatus;
  let explanation: string;
  const warnings: string[] = [];

  switch (primaryRule.type) {
    case 'tow-away':
      status = 'illegal';
      explanation = `Don't park here! ${primaryRule.description}. Your car will be towed.`;
      break;

    case 'street-sweeping':
      status = 'illegal';
      explanation = `Don't park here! ${primaryRule.description}. You'll get a ticket and may be towed.`;
      break;

    case 'no-parking':
      status = 'illegal';
      explanation = `Don't park here! ${primaryRule.description}.`;
      break;

    case 'meter':
      // Check for time limits
      const timeLimitRule = allRules.find(r => r.type === 'time-limit');
      if (timeLimitRule && timeLimitRule.metadata?.timeLimit) {
        const limitMinutes = timeLimitRule.metadata.timeLimit;
        if (durationMinutes > limitMinutes) {
          status = 'illegal';
          explanation = `Don't park here! Your ${durationMinutes / 60}-hour stay exceeds the ${limitMinutes / 60}-hour limit.`;
          break;
        }
      }
      
      // Meters are legal if you pay and within time limit
      status = 'legal';
      const rate = primaryRule.metadata?.meterRate || 3.50;
      explanation = `You can park here! ${primaryRule.description}. Rate: $${rate}/hour.`;
      
      if (timeLimitRule && timeLimitRule.metadata?.timeLimit) {
        const limitMinutes = timeLimitRule.metadata.timeLimit;
        explanation += ` ${limitMinutes / 60}-hour limit applies.`;
      }
      break;

    case 'time-limit':
      const limitMinutes = primaryRule.metadata?.timeLimit || 120;
      if (durationMinutes > limitMinutes) {
        status = 'illegal';
        explanation = `Don't park here! Your ${durationMinutes / 60}-hour stay exceeds the ${limitMinutes / 60}-hour limit.`;
      } else {
        status = 'legal';
        explanation = `You can park here! ${primaryRule.description} - you're within the limit.`;
      }
      break;

    case 'rpp-zone':
      // RPP zones are illegal for non-residents during enforcement hours
      status = 'illegal';
      const zone = primaryRule.metadata?.permitZone || 'Unknown';
      explanation = `Don't park here! Residential Permit Zone ${zone} - permit required. Non-residents will be ticketed.`;
      warnings.push('Visitors may have limited time - check signs carefully');
      break;

    default:
      status = 'insufficient-data';
      explanation = 'Unable to determine parking legality. Please verify signs on-site.';
  }

  warnings.push('Always verify parking signs at the location');

  return {
    status,
    explanation,
    applicableRules: allRules,
    warnings,
  };
}

/**
 * Gets color for map visualization based on legality status
 */
export function getStatusColor(status: LegalityStatus): string {
  switch (status) {
    case 'legal':
      return '#10b981'; // green-500
    case 'illegal':
      return '#ef4444'; // red-500
    case 'insufficient-data':
      return '#9ca3af'; // gray-400 (lighter gray)
    default:
      return '#9ca3af'; // gray-400 (lighter gray)
  }
}