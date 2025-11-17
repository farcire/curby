import { ParkingRule, LegalityResult, LegalityStatus, Blockface } from '@/types/parking';
import { isWithinInterval, addMinutes, getDay, format } from 'date-fns';

/**
 * Evaluates parking legality for a blockface at a specific time and duration
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
      explanation: 'Insufficient parking data available for this location. Please verify signs on-site.',
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

  // Sort by precedence (highest first)
  applicableRules.sort((a, b) => b.precedence - a.precedence);

  // Determine status based on highest precedence rule
  if (applicableRules.length === 0) {
    return {
      status: 'legal',
      explanation: 'Legal to park. No restrictions apply during this time.',
      applicableRules: [],
    };
  }

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
      explanation = `🚫 Illegal to park: ${primaryRule.description}. Your vehicle will be towed.`;
      break;

    case 'street-sweeping':
      status = 'illegal';
      explanation = `🚫 Illegal to park: ${primaryRule.description}. Parking during street sweeping results in citations.`;
      break;

    case 'no-parking':
      status = 'illegal';
      explanation = `🚫 Illegal to park: ${primaryRule.description}.`;
      break;

    case 'meter':
      status = 'limited';
      const rate = primaryRule.metadata?.meterRate || 3.50;
      explanation = `⚠️ Limited parking: ${primaryRule.description}. Rate: $${rate}/hour.`;
      
      // Check for additional restrictions
      const timeLimitRule = allRules.find(r => r.type === 'time-limit');
      if (timeLimitRule && timeLimitRule.metadata?.timeLimit) {
        const limitMinutes = timeLimitRule.metadata.timeLimit;
        if (durationMinutes > limitMinutes) {
          explanation += ` ${limitMinutes / 60}-hour time limit applies - your ${durationMinutes / 60}-hour duration exceeds this.`;
          warnings.push('Your parking duration exceeds the time limit');
        } else {
          explanation += ` ${limitMinutes / 60}-hour time limit.`;
        }
      }
      break;

    case 'time-limit':
      const limitMinutes = primaryRule.metadata?.timeLimit || 120;
      if (durationMinutes > limitMinutes) {
        status = 'limited';
        explanation = `⚠️ Limited parking: ${primaryRule.description}. Your ${durationMinutes / 60}-hour duration exceeds the ${limitMinutes / 60}-hour limit.`;
        warnings.push('Your parking duration exceeds the time limit');
      } else {
        status = 'legal';
        explanation = `✅ Legal to park: ${primaryRule.description} applies, but your ${durationMinutes / 60}-hour duration is within the limit.`;
      }
      break;

    case 'rpp-zone':
      status = 'limited';
      const zone = primaryRule.metadata?.permitZone || 'Unknown';
      explanation = `⚠️ Limited parking: ${primaryRule.description}. Permit required for extended parking.`;
      warnings.push(`Residential Permit Zone ${zone} - visitors may have time limits`);
      break;

    default:
      status = 'insufficient-data';
      explanation = 'Unable to determine parking legality. Please verify signs on-site.';
  }

  // Add sweeping warnings if applicable
  const sweepingRule = allRules.find(r => r.type === 'street-sweeping' && r !== primaryRule);
  if (sweepingRule) {
    warnings.push(`Note: ${sweepingRule.description}`);
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
      return '#10b981'; // green
    case 'limited':
      return '#f59e0b'; // yellow/amber
    case 'illegal':
      return '#ef4444'; // red
    case 'insufficient-data':
      return '#6b7280'; // gray
    default:
      return '#6b7280';
  }
}