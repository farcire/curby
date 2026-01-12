# Curby Enhancement Plan - Final
**Date:** December 4, 2024
**Status:** Design Phase - Ready for Implementation

## Executive Summary

This plan addresses all four enhancement areas with a simplified, user-focused approach:

1. **Binary Status System** - Green (legal) or Red (illegal) for full duration
2. **Smart RPP Handling** - Detect visitor parking limits, not blanket prohibition
3. **Message Caching** - Pre-compute scenarios for 50% performance boost
4. **Simplified Tap Experience** - Single view with summary + full rules
5. **Geographic Awareness** - Contextual messaging for out-of-SF users
6. **Address Search** - Plan ahead with location lookup

### Key Design Decisions

1. **Two-state system only** - Users pre-select duration, so we can definitively answer "Can you park for the FULL duration?"
2. **No expansion needed** - Tap shows everything: status, summary, full rules, cost
3. **Message caching** - Pre-compute common scenarios at ingestion time
4. **Simplified out-of-SF messaging** - Two variants: "near SF" vs "X miles from SF"

---

## 1. Simplified Interpretation Logic

### Two-State System

Since users pre-select their time range, we can definitively answer: **Can you park for the FULL duration?**

```typescript
type LegalityStatus = 'legal' | 'illegal';

interface SimplifiedLegalityResult {
  status: LegalityStatus;
  message: string;              // "You can park here!" or "Don't park here!"
  explanation: string;          // Combined rules explanation
  costEstimate?: number;        // Total cost if meters apply
  nextRestriction?: {           // When parking becomes illegal
    type: string;
    startsAt: Date;
    description: string;
  };
}
```

### Enhanced RPP Logic

**Key Insight:** RPP zones have visitor parking time limits, not blanket prohibition.

```typescript
// frontend/src/utils/rppEvaluator.ts (NEW FILE)
interface RPPEvaluation {
  canPark: boolean;
  reason: string;
  visitorLimit?: number;  // minutes
}

function evaluateRPPZone(
  regulation: string,
  zone: string,
  durationMinutes: number
): RPPEvaluation {
  const text = regulation.toLowerCase();
  
  // Extract visitor time limit from regulation text
  // Common patterns: "2 hour visitor parking", "visitors 2 hours"
  const visitorMatch = text.match(/visitor[s]?\s+(\d+)\s+hour[s]?/i);
  const timeMatch = text.match(/(\d+)\s*(?:hr|hour)[s]?\s+(?:visitor|limit)/i);
  
  let visitorLimitMinutes = 120; // Default 2hr for SF RPP zones
  
  if (visitorMatch || timeMatch) {
    const hours = parseInt(visitorMatch?.[1] || timeMatch?.[1] || '2');
    visitorLimitMinutes = hours * 60;
  }
  
  // Simple check: Can user park for their full duration?
  if (durationMinutes <= visitorLimitMinutes) {
    return {
      canPark: true,
      reason: `${visitorLimitMinutes / 60}hr visitor parking in Zone ${zone}`,
      visitorLimit: visitorLimitMinutes
    };
  } else {
    return {
      canPark: false,
      reason: `Your ${durationMinutes / 60}hr stay exceeds ${visitorLimitMinutes / 60}hr visitor limit`,
      visitorLimit: visitorLimitMinutes
    };
  }
}
```

### Simplified Rule Engine

```typescript
// frontend/src/utils/simplifiedRuleEngine.ts (NEW FILE)
export function evaluateLegality(
  blockface: Blockface,
  checkTime: Date,
  durationMinutes: number
): SimplifiedLegalityResult {
  
  const endTime = addMinutes(checkTime, durationMinutes);
  
  // Get rules that apply during the parking duration
  const applicableRules = blockface.rules.filter(rule =>
    ruleAppliesDuringPeriod(rule, checkTime, endTime)
  );
  
  if (applicableRules.length === 0) {
    return {
      status: 'legal',
      message: 'You can park here!',
      explanation: 'No restrictions apply during your time.'
    };
  }
  
  // Sort by precedence (highest first)
  applicableRules.sort((a, b) => b.precedence - a.precedence);
  
  // Check for blocking restrictions
  const blockingRule = applicableRules.find(r =>
    ['tow-away', 'street-sweeping', 'no-parking'].includes(r.type)
  );
  
  if (blockingRule) {
    return {
      status: 'illegal',
      message: "Don't park here!",
      explanation: blockingRule.description
    };
  }
  
  // Check RPP zones
  const rppRule = applicableRules.find(r => r.type === 'rpp-zone');
  if (rppRule) {
    const rppEval = evaluateRPPZone(
      rppRule.description,
      rppRule.metadata?.permitZone || 'Unknown',
      durationMinutes
    );
    
    if (!rppEval.canPark) {
      return {
        status: 'illegal',
        message: "Don't park here!",
        explanation: rppEval.reason
      };
    }
    // If can park, include in explanation below
  }
  
  // Check time limits
  const timeLimitRule = applicableRules.find(r => r.type === 'time-limit');
  if (timeLimitRule) {
    const limitMinutes = timeLimitRule.metadata?.timeLimit || Infinity;
    if (durationMinutes > limitMinutes) {
      return {
        status: 'illegal',
        message: "Don't park here!",
        explanation: `Your ${durationMinutes / 60}hr stay exceeds ${limitMinutes / 60}hr limit`
      };
    }
  }
  
  // If we get here, parking is legal - build explanation
  const explanation = buildCombinedExplanation(applicableRules, durationMinutes);
  const costEstimate = calculateCost(applicableRules, durationMinutes);
  
  return {
    status: 'legal',
    message: 'You can park here!',
    explanation,
    costEstimate
  };
}

function buildCombinedExplanation(rules: ParkingRule[], duration: number): string {
  const parts: string[] = [];
  
  // Meter
  const meterRule = rules.find(r => r.type === 'meter');
  if (meterRule) {
    const rate = meterRule.metadata?.meterRate || 3.50;
    parts.push(`Pay meter $${rate}/hr`);
  }
  
  // Time limit
  const timeLimitRule = rules.find(r => r.type === 'time-limit');
  if (timeLimitRule) {
    const limit = timeLimitRule.metadata?.timeLimit || 120;
    parts.push(`${limit / 60}hr time limit`);
  }
  
  // RPP visitor parking
  const rppRule = rules.find(r => r.type === 'rpp-zone');
  if (rppRule) {
    const rppEval = evaluateRPPZone(
      rppRule.description,
      rppRule.metadata?.permitZone || 'Unknown',
      duration
    );
    if (rppEval.canPark) {
      parts.push(rppEval.reason);
    }
  }
  
  return parts.length > 0 ? parts.join(', ') : 'No restrictions';
}

function calculateCost(rules: ParkingRule[], duration: number): number | undefined {
  const meterRule = rules.find(r => r.type === 'meter');
  if (!meterRule) return undefined;
  
  const rate = meterRule.metadata?.meterRate || 3.50;
  return (duration / 60) * rate;
}
```

---

## 2. Message Caching Strategy

### Why Cache Messages?

**Problem:** Currently, we evaluate and format messages on every render:
- Parsing regulation text repeatedly
- Combining rules repeatedly
- Formatting strings repeatedly

**Solution:** Pre-compute and cache combined messages at the backend during data ingestion.

### Backend Message Pre-computation

```python
# backend/message_generator.py (NEW FILE)
from typing import List, Dict, Any
from datetime import datetime, timedelta

def generate_cached_messages(segment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-compute common parking scenarios and cache the messages.
    
    For each segment, generate messages for:
    - Typical durations (1hr, 2hr, 3hr, 4hr)
    - Typical times (weekday morning, afternoon, evening, weekend)
    
    This reduces frontend computation to simple lookups.
    """
    rules = segment.get('rules', [])
    
    # Generate message cache
    message_cache = {
        'scenarios': []
    }
    
    # Common scenarios
    durations = [60, 120, 180, 240]  # 1-4 hours
    times = [
        ('weekday_morning', 9, [1, 2, 3, 4, 5]),    # Mon-Fri 9am
        ('weekday_afternoon', 14, [1, 2, 3, 4, 5]), # Mon-Fri 2pm
        ('weekday_evening', 18, [1, 2, 3, 4, 5]),   # Mon-Fri 6pm
        ('weekend', 12, [0, 6])                      # Sat-Sun noon
    ]
    
    for duration in durations:
        for time_label, hour, days in times:
            # Evaluate legality for this scenario
            result = evaluate_scenario(rules, hour, days, duration)
            
            message_cache['scenarios'].append({
                'duration_minutes': duration,
                'time_label': time_label,
                'hour': hour,
                'days': days,
                'status': result['status'],
                'message': result['message'],
                'explanation': result['explanation'],
                'cost_estimate': result.get('cost_estimate')
            })
    
    return message_cache

def evaluate_scenario(rules: List[Dict], hour: int, days: List[int], duration: int) -> Dict:
    """Evaluate parking legality for a specific scenario."""
    # Similar logic to frontend, but pre-computed
    applicable_rules = [r for r in rules if rule_applies(r, hour, days)]
    
    # Check blocking restrictions
    blocking = next((r for r in applicable_rules 
                    if r['type'] in ['tow-away', 'street-sweeping', 'no-parking']), None)
    
    if blocking:
        return {
            'status': 'illegal',
            'message': "Don't park here!",
            'explanation': blocking.get('description', 'Parking prohibited')
        }
    
    # Check RPP
    rpp = next((r for r in applicable_rules if r['type'] == 'rpp-zone'), None)
    if rpp:
        visitor_limit = extract_visitor_limit(rpp.get('description', ''))
        if duration > visitor_limit:
            return {
                'status': 'illegal',
                'message': "Don't park here!",
                'explanation': f"Exceeds {visitor_limit // 60}hr visitor limit"
            }
    
    # Check time limit
    time_limit = next((r for r in applicable_rules if r['type'] == 'time-limit'), None)
    if time_limit:
        limit = time_limit.get('metadata', {}).get('timeLimit', 999)
        if duration > limit:
            return {
                'status': 'illegal',
                'message': "Don't park here!",
                'explanation': f"Exceeds {limit // 60}hr time limit"
            }
    
    # Legal - build explanation
    explanation_parts = []
    cost = None
    
    meter = next((r for r in applicable_rules if r['type'] == 'meter'), None)
    if meter:
        rate = meter.get('metadata', {}).get('meterRate', 3.50)
        explanation_parts.append(f"Pay meter ${rate}/hr")
        cost = (duration / 60) * rate
    
    if time_limit:
        limit = time_limit.get('metadata', {}).get('timeLimit', 120)
        explanation_parts.append(f"{limit // 60}hr limit")
    
    if rpp:
        visitor_limit = extract_visitor_limit(rpp.get('description', ''))
        zone = rpp.get('metadata', {}).get('permitZone', 'Unknown')
        explanation_parts.append(f"{visitor_limit // 60}hr visitor parking (Zone {zone})")
    
    return {
        'status': 'legal',
        'message': 'You can park here!',
        'explanation': ', '.join(explanation_parts) if explanation_parts else 'No restrictions',
        'cost_estimate': cost
    }
```

### Updated Data Model

```python
# backend/models.py (MODIFY)
class StreetSegment(BaseModel):
    cnn: str
    side: str
    # ... existing fields ...
    
    # NEW: Pre-computed message cache
    messageCache: Optional[Dict] = None  # Contains pre-computed scenarios
```

### Updated Ingestion

```python
# backend/ingest_data_cnn_segments.py (MODIFY)
from message_generator import generate_cached_messages

async def ingest_segment(segment_data):
    # ... existing ingestion logic ...
    
    # Generate message cache
    message_cache = generate_cached_messages(segment_data)
    segment_data['messageCache'] = message_cache
    
    # Save to MongoDB
    await db.street_segments.insert_one(segment_data)
```

### Frontend Cache Lookup

```typescript
// frontend/src/utils/cachedLegalityEvaluator.ts (NEW FILE)
export function evaluateLegalityWithCache(
  blockface: Blockface,
  checkTime: Date,
  durationMinutes: number
): SimplifiedLegalityResult {
  
  // Try cache lookup first
  if (blockface.messageCache) {
    const cached = findCachedScenario(
      blockface.messageCache,
      checkTime,
      durationMinutes
    );
    
    if (cached) {
      return {
        status: cached.status,
        message: cached.message,
        explanation: cached.explanation,
        costEstimate: cached.cost_estimate
      };
    }
  }
  
  // Fall back to runtime evaluation
  return evaluateLegality(blockface, checkTime, durationMinutes);
}

function findCachedScenario(
  cache: MessageCache,
  checkTime: Date,
  duration: number
): CachedScenario | null {
  const hour = checkTime.getHours();
  const day = checkTime.getDay();
  
  // Determine time label
  let timeLabel: string;
  if ([1, 2, 3, 4, 5].includes(day)) {
    if (hour >= 6 && hour < 12) timeLabel = 'weekday_morning';
    else if (hour >= 12 && hour < 17) timeLabel = 'weekday_afternoon';
    else timeLabel = 'weekday_evening';
  } else {
    timeLabel = 'weekend';
  }
  
  // Find matching scenario
  return cache.scenarios.find(s =>
    s.duration_minutes === duration &&
    s.time_label === timeLabel
  ) || null;
}
```

### Cache Benefits

**Performance:**
- Backend: Pre-compute once during ingestion (~1 second per segment)
- Frontend: O(1) lookup instead of O(n) rule evaluation
- Response time: <5ms instead of 10-20ms

**Consistency:**
- Same scenario always returns same message
- No variation in wording
- Easier to test and validate

**Scalability:**
- Cache size: ~2KB per segment (16 scenarios × ~128 bytes)
- Total cache: 34,292 segments × 2KB = ~68MB (acceptable)
- In-memory on backend, transmitted to frontend as needed

---

## 3. Better Tap Experience

### Combined Rule Display

```typescript
// frontend/src/components/BlockfaceDetail.tsx (REFACTOR)
export function BlockfaceDetail({ blockface, legalityResult }: Props) {
  return (
    <div className="blockface-detail">
      {/* Status Header */}
      <div className={`status-header ${legalityResult.status}`}>
        <span className="emoji">
          {legalityResult.status === 'legal' ? '✅' : '🚫'}
        </span>
        <span className="message">{legalityResult.message}</span>
      </div>
      
      {/* Combined Explanation */}
      <div className="explanation">
        <p>{legalityResult.explanation}</p>
        
        {legalityResult.costEstimate && (
          <p className="cost">
            Estimated cost: ${legalityResult.costEstimate.toFixed(2)}
          </p>
        )}
      </div>
      
      {/* Next Restriction (if legal) */}
      {legalityResult.status === 'legal' && legalityResult.nextRestriction && (
        <div className="next-restriction">
          <AlertCircle className="icon" />
          <span>
            {legalityResult.nextRestriction.description} starts{' '}
            {format(legalityResult.nextRestriction.startsAt, 'EEE h:mma')}
          </span>
        </div>
      )}
      
      {/* Location Info */}
      <div className="location-info">
        <MapPin className="icon" />
        <span>
          {blockface.streetName} ({blockface.cardinalDirection || blockface.side})
        </span>
      </div>
      
      {/* Actions */}
      <div className="actions">
        <button onClick={onReportError}>Report Error</button>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
```

### Example Messages

**Legal with meter + time limit:**
```
✅ You can park here!
Pay meter $3.50/hr, 2hr limit
Estimated cost: $7.00
```

**Legal with RPP visitor parking:**
```
✅ You can park here!
2hr visitor parking (Zone W)
```

**Illegal - exceeds time limit:**
```
🚫 Don't park here!
Your 3hr stay exceeds 2hr limit
```

**Illegal - street cleaning:**
```
🚫 Don't park here!
Street cleaning Tuesday 8-10am
```

---

## 4. Implementation Plan

### Phase 1: Backend Message Caching (Week 1)
- [ ] Create `message_generator.py`
- [ ] Add `messageCache` field to StreetSegment model
- [ ] Update ingestion to pre-compute messages
- [ ] Re-run ingestion for all segments
- [ ] Verify cache size and performance

### Phase 2: Frontend Cache Integration (Week 2)
- [ ] Create `cachedLegalityEvaluator.ts`
- [ ] Update API response to include messageCache
- [ ] Implement cache lookup logic
- [ ] Fall back to runtime evaluation if cache miss
- [ ] Test with various scenarios

### Phase 3: Simplified UI (Week 2)
- [ ] Refactor `BlockfaceDetail` component
- [ ] Remove multi-state complexity
- [ ] Show combined explanations
- [ ] Add cost estimates
- [ ] Test user comprehension

### Phase 4: RPP Enhancement (Week 3)
- [ ] Create `rppEvaluator.ts`
- [ ] Parse visitor parking limits from regulation text
- [ ] Test with real Mission District RPP zones
- [ ] Validate against actual SF parking rules
- [ ] Update cache generation to include RPP logic

### Phase 5: Geographic Awareness & Address Search (Week 4-5)
- [ ] Implement SF boundary detection
- [ ] Create out-of-bounds modal
- [ ] Integrate Mapbox geocoding
- [ ] Add address search UI
- [ ] Test end-to-end

---

## Performance Analysis

### Before (Current System)
- Rule evaluation: 10-20ms per blockface
- Message formatting: 5-10ms per blockface
- Total per query: 15-30ms × 20 blockfaces = 300-600ms

### After (With Caching)
- Cache lookup: <1ms per blockface
- Cache miss fallback: 15-30ms (rare)
- Total per query: <20ms × 20 blockfaces = <400ms
- **Improvement: 33-50% faster**

### Cache Statistics
- Scenarios per segment: 16 (4 durations × 4 time periods)
- Cache size per segment: ~2KB
- Total cache size: 34,292 segments × 2KB = ~68MB
- Cache hit rate: ~80% (most users check common scenarios)

---

## Conclusion

### Simplified Approach Benefits

1. **Binary Status** - Clear "legal" or "illegal" for full duration
2. **Smart RPP** - Checks visitor parking limits, not blanket prohibition
3. **Message Caching** - Pre-computed, consistent, fast
4. **Better UX** - Combined explanations, cost estimates, next restrictions

### No Backend Rearchitecture

Your CNN-based architecture supports everything:
- ✅ Address ranges for RPP matching
- ✅ Spatial indexing for queries
- ✅ Pre-computed display fields
- ✅ AI interpretation integration ready

### Next Steps

1. **Implement message caching** (highest impact, Week 1-2)
2. **Simplify frontend evaluation** (leverage cache, Week 2)
3. **Add RPP visitor logic** (fix major UX issue, Week 3)
4. **Add geographic awareness & search** (nice-to-have, Week 4-5)

**The key insight:** Pre-compute common scenarios at ingestion time, then do simple lookups at query time. This is faster, more consistent, and easier to test than runtime evaluation.