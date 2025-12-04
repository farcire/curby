export interface RPPEvaluation {
  canPark: boolean;
  reason: string;
  visitorLimitMinutes?: number;
}

/**
 * Evaluates RPP (Residential Permit Parking) zones for visitor parking eligibility.
 * Many RPP zones allow visitor parking for limited durations (typically 2 hours).
 * This function parses the regulation text to detect visitor parking limits.
 */
export function evaluateRPPZone(
  regulation: string,
  zone: string,
  durationMinutes: number
): RPPEvaluation {
  const text = regulation.toLowerCase();
  
  // Extract visitor time limit from regulation text
  // Common patterns in SF:
  // - "2 hour visitor parking"
  // - "visitors 2 hours"
  // - "2hr visitor parking"
  // - "2 hour non-permit parking"
  // - "non-permit holders 2 hours"
  const patterns = [
    /visitor[s]?\s+(\d+)\s+hour[s]?/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+visitor/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+(?:for\s+)?non-permit/i,
    /non-permit\s+holder[s]?\s+(\d+)\s+hour[s]?/i,
    /(\d+)\s*(?:hr|hour)[s]?\s+(?:for\s+)?non-resident/i,
  ];
  
  let visitorLimitMinutes: number | null = null;
  
  // Try to find visitor parking limit in regulation text
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      visitorLimitMinutes = parseInt(match[1]) * 60;
      break;
    }
  }
  
  // If no visitor limit found, check for common SF default (2 hours)
  // Many SF RPP zones allow 2hr visitor parking even if not explicitly stated
  if (visitorLimitMinutes === null) {
    // Check if regulation mentions "visitor" or "non-permit" at all
    if (text.includes('visitor') || text.includes('non-permit') || text.includes('non-resident')) {
      visitorLimitMinutes = 120; // Default 2hr for SF
    }
  }
  
  // If visitor parking is allowed, check if user's duration fits
  if (visitorLimitMinutes !== null) {
    if (durationMinutes <= visitorLimitMinutes) {
      const hours = visitorLimitMinutes / 60;
      return {
        canPark: true,
        reason: `${hours}hr parking except Zone ${zone}`,
        visitorLimitMinutes
      };
    } else {
      const limitHours = visitorLimitMinutes / 60;
      const requestedHours = Math.round(durationMinutes / 60 * 10) / 10; // Round to 1 decimal
      return {
        canPark: false,
        reason: `${limitHours}hr parking except Zone ${zone}`,
        visitorLimitMinutes
      };
    }
  }
  
  // No visitor parking allowed - permit required
  return {
    canPark: false,
    reason: `No parking except Zone ${zone}`,
    visitorLimitMinutes: undefined
  };
}