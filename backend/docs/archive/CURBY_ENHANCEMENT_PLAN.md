# Curby Enhancement Plan
**Date:** December 4, 2024  
**Status:** Design Phase

## Executive Summary

This document outlines the architectural and UX improvements needed for Curby to address four key issues:

1. **Parking regulation interpretation logic** - Currently suboptimal
2. **Eligibility messaging complexity** - Overly complex for users
3. **Out-of-SF user experience** - App appears broken outside San Francisco
4. **Address-based lookup** - Enable queries without being physically present

## Current Architecture Analysis

### Frontend Architecture
- **Location-based**: Uses geolocation + map viewport to fetch data
- **Real-time evaluation**: Client-side rule engine ([`ruleEngine.ts`](frontend/src/utils/ruleEngine.ts:1))
- **Binary status**: Legal (green) or Illegal (red) only
- **Performance**: <100ms for 95% of queries

### Backend Architecture
- **CNN-based segments**: 34,292 street segments (100% SF coverage)
- **Spatial queries**: MongoDB 2dsphere index on centerlineGeometry
- **Pre-computed rules**: Rules attached during ingestion
- **API**: `/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters={radius}`

### Current Rule Interpretation Issues

**Problem Areas Identified:**

1. **Oversimplified Logic** ([`ruleEngine.ts:95-175`](frontend/src/utils/ruleEngine.ts:95-175))
   - Binary legal/illegal only (no nuanced states)
   - RPP zones always marked illegal (doesn't account for visitor parking)
   - Time limits checked but not clearly communicated
   - Meter + time limit interaction unclear

2. **Complex Messaging** ([`BlockfaceDetail.tsx:122-141`](frontend/src/components/BlockfaceDetail.tsx:122-141))
   - Shows ALL rules regardless of current applicability
   - No prioritization of what matters NOW
   - Permit status shown separately from rules
   - Technical language (e.g., "Residential Permit Zone X")

3. **No Geographic Awareness**
   - App loads but shows empty map outside SF
   - No indication that service is SF-only
   - User thinks app is broken

4. **Location-dependent Only**
   - Cannot check parking at future destination
   - Cannot plan ahead for appointments
   - Must be physically present to see data

## Proposed Solutions

### 1. Enhanced Regulation Interpretation Logic

#### Current State
```typescript
// Simplified binary logic
switch (primaryRule.type) {
  case 'rpp-zone':
    status = 'illegal'; // Always illegal!
    break;
  case 'meter':
    status = 'legal'; // Always legal if you pay
    break;
}
```

#### Proposed State
```typescript
// Nuanced multi-state logic
interface EnhancedLegalityResult {
  status: 'legal' | 'legal-with-conditions' | 'limited' | 'illegal' | 'insufficient-data';
  primaryMessage: string;        // "You can park here"
  conditions: string[];          // ["Pay meter $3.50/hr", "2hr limit"]
  restrictions: string[];        // ["No parking Mon 8-10am"]
  confidence: 'high' | 'medium' | 'low';
  permitInfo?: {
    zone: string;
    visitorAllowed: boolean;
    visitorTimeLimit?: number;
  };
}
```

**Key Improvements:**

1. **RPP Zone Intelligence**
   - Detect visitor parking allowances (common in SF: 2hr visitor parking in many RPP zones)
   - Show "Legal with conditions: 2hr visitor limit, Zone X" instead of blanket "illegal"
   - Parse regulation text for visitor exceptions

2. **Meter + Time Limit Clarity**
   - Combine related rules: "Pay meter ($3.50/hr), 2hr limit"
   - Show cost calculation: "3hr parking = $10.50"
   - Warn if duration exceeds limit BEFORE marking illegal

3. **Confidence Scoring**
   - HIGH: All rules parsed successfully, no conflicts
   - MEDIUM: Some ambiguity in rules
   - LOW: Insufficient data or conflicting rules

4. **Time-aware Evaluation**
   - "Legal NOW, but street cleaning starts in 45 minutes"
   - "Illegal NOW (street cleaning), legal again at 11am"

#### Implementation Strategy

**Backend Changes:**
```python
# backend/enhanced_interpreter.py (NEW FILE)
class EnhancedRuleInterpreter:
    def interpret_regulations(self, rules: List[Dict], check_time: datetime, 
                            duration_minutes: int) -> EnhancedLegalityResult:
        """
        Interprets parking regulations with nuanced logic.
        
        Priority order:
        1. Active tow-away zones (100% illegal)
        2. Active street sweeping (100% illegal)
        3. Active no-parking (100% illegal)
        4. RPP zones (check for visitor exceptions)
        5. Time limits (check if duration fits)
        6. Meters (legal with payment)
        """
        pass
```

**Frontend Changes:**
```typescript
// frontend/src/utils/enhancedRuleEngine.ts (NEW FILE)
export function evaluateEnhancedLegality(
  blockface: Blockface,
  checkTime: Date,
  durationMinutes: number
): EnhancedLegalityResult {
  // Multi-pass evaluation:
  // Pass 1: Find blocking restrictions (tow, sweep, no-parking)
  // Pass 2: Find conditional restrictions (RPP, time limits)
  // Pass 3: Find payment requirements (meters)
  // Pass 4: Combine into clear message
}
```

### 2. Simplified Eligibility Messaging

#### Current Issues
- Shows 5-7 rules per blockface
- Technical jargon ("Residential Permit Zone", "CNN", "L/R")
- No clear hierarchy of what matters

#### Proposed Solution: Progressive Disclosure

**Level 1: At-a-Glance Status (Map View)**
```
🟢 Legal - $3.50/hr, 2hr limit
🟡 Limited - Visitor parking 2hr
🔴 Illegal - Street cleaning now
⚪ Unknown - Check signs
```

**Level 2: Quick Summary (Tap blockface)**
```
✅ You can park here

PAY & STAY:
• Meter required: $3.50/hour
• Maximum stay: 2 hours
• Estimated cost: $7.00

NEXT RESTRICTION:
⚠️ Street cleaning Tuesday 8am

[See all rules] [Report error]
```

**Level 3: Full Details (Expand)**
```
ALL PARKING RULES:

Active Now:
• Metered parking 9am-6pm Mon-Sat
• 2-hour time limit

Not Active Now:
• Street cleaning Tue 8-10am
• No parking game days 2hrs before

Permit Info:
• Residential Zone X
• Visitors: 2hr parking allowed
```

#### Implementation

**Component Structure:**
```typescript
// frontend/src/components/BlockfaceDetail.tsx (REFACTOR)
interface BlockfaceDetailProps {
  blockface: Blockface;
  legalityResult: EnhancedLegalityResult;
  detailLevel: 'summary' | 'full'; // Progressive disclosure
}

// Show summary by default, expand to full on user request
```

**Message Templates:**
```typescript
// frontend/src/utils/messageTemplates.ts (NEW FILE)
const TEMPLATES = {
  legal: {
    simple: "You can park here",
    withMeter: "You can park here - pay meter",
    withLimit: "You can park here - {limit}hr limit",
    withBoth: "You can park here - pay meter, {limit}hr limit"
  },
  limited: {
    visitor: "Visitor parking allowed - {limit}hr limit",
    timeLimit: "Limited parking - {limit}hr maximum"
  },
  illegal: {
    sweeping: "Don't park - street cleaning {time}",
    towAway: "Don't park - tow-away zone",
    noParking: "Don't park - no parking {time}"
  }
};
```

### 3. Out-of-SF User Experience

#### Current Problem
```typescript
// User opens app in Oakland
// Map loads, shows empty area
// User thinks: "App is broken"
```

#### Proposed Solution: Geographic Awareness

**Detection Strategy:**
```typescript
// frontend/src/utils/geoFence.ts (NEW FILE)
const SF_BOUNDS = {
  north: 37.8324,
  south: 37.7034,
  east: -122.3482,
  west: -122.5155
};

function isInSanFrancisco(lat: number, lng: number): boolean {
  return lat >= SF_BOUNDS.south && lat <= SF_BOUNDS.north &&
         lng >= SF_BOUNDS.west && lng <= SF_BOUNDS.east;
}

function getDistanceToSF(lat: number, lng: number): number {
  // Calculate distance to nearest SF boundary
}
```

**UX Flow:**

**Scenario A: User in Oakland (10 miles from SF)**
```
┌─────────────────────────────────────┐
│  🌉 Curby - SF Parking              │
├─────────────────────────────────────┤
│                                     │
│  📍 You're currently in Oakland     │
│                                     │
│  Curby shows parking info for       │
│  San Francisco only.                │
│                                     │
│  [View SF Map] [Search Address]     │
│                                     │
│  Distance to SF: 10 miles           │
└─────────────────────────────────────┘
```

**Scenario B: User in Los Angeles (400 miles from SF)**
```
┌─────────────────────────────────────┐
│  🌉 Curby - SF Parking              │
├─────────────────────────────────────┤
│                                     │
│  📍 You're outside our service area │
│                                     │
│  Curby currently works in           │
│  San Francisco only.                │
│                                     │
│  [View SF Map] [Search SF Address]  │
│                                     │
│  Coming soon to more cities! 🚀     │
└─────────────────────────────────────┘
```

**Scenario C: User near SF border (in Daly City)**
```
┌─────────────────────────────────────┐
│  🌉 Curby - SF Parking              │
├─────────────────────────────────────┤
│                                     │
│  📍 You're near San Francisco       │
│                                     │
│  [Show SF parking (2 miles away)]   │
│  [Search SF address]                │
│                                     │
│  Tip: Curby works within SF city    │
│  limits only.                       │
└─────────────────────────────────────┘
```

#### Implementation

```typescript
// frontend/src/pages/Index.tsx (MODIFY)
useEffect(() => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLoc = [position.coords.latitude, position.coords.longitude];
        
        if (!isInSanFrancisco(userLoc[0], userLoc[1])) {
          const distance = getDistanceToSF(userLoc[0], userLoc[1]);
          setShowOutOfBoundsModal(true);
          setDistanceToSF(distance);
          // Still load SF map, but show modal overlay
          loadSFMTAData(DEFAULT_SF_CENTER[0], DEFAULT_SF_CENTER[1], 500);
        } else {
          loadSFMTAData(userLoc[0], userLoc[1], 300);
        }
      }
    );
  }
}, []);
```

### 4. Address-Based Lookup

#### Current Limitation
- Must be physically present to see parking data
- Cannot plan ahead for appointments
- Cannot check destination before leaving

#### Proposed Solution: Search + Virtual Location

**Feature: Address Search**
```
┌─────────────────────────────────────┐
│  🔍 Search SF address or location   │
│  ┌───────────────────────────────┐  │
│  │ 1234 Market St                │  │
│  └───────────────────────────────┘  │
│                                     │
│  Recent searches:                   │
│  • 20th & Bryant                    │
│  • Ferry Building                   │
│  • Golden Gate Park                 │
└─────────────────────────────────────┘
```

**Implementation Strategy:**

**Option A: Client-side Geocoding (Recommended)**
```typescript
// Use Mapbox Geocoding API (already using Mapbox for maps)
// Free tier: 100,000 requests/month

async function searchAddress(query: string): Promise<SearchResult[]> {
  const response = await fetch(
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?` +
    `access_token=${MAPBOX_TOKEN}&` +
    `bbox=-122.5155,37.7034,-122.3482,37.8324&` + // Limit to SF
    `limit=5`
  );
  return response.json();
}
```

**Option B: Backend Geocoding**
```python
# backend/main.py (ADD ENDPOINT)
@app.get("/api/v1/geocode")
async def geocode_address(address: str):
    """
    Geocode SF address to lat/lng.
    Returns blockfaces near that location.
    """
    # Use geopy or similar
    location = geocoder.geocode(f"{address}, San Francisco, CA")
    if location:
        return await get_blockfaces(
            lat=location.latitude,
            lng=location.longitude,
            radius_meters=100
        )
```

**UX Flow:**

1. **User enters address**: "1234 Market St"
2. **Geocode to coordinates**: (37.7749, -122.4194)
3. **Fetch blockfaces**: Same API call as current location-based
4. **Show "virtual pin"**: Blue dot = user location, Red pin = searched location
5. **Enable "directions"**: Link to Google Maps/Apple Maps

**UI Components:**

```typescript
// frontend/src/components/AddressSearch.tsx (NEW FILE)
export function AddressSearch({ onLocationSelect }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  
  const handleSearch = async () => {
    const results = await searchAddress(query);
    setResults(results);
  };
  
  return (
    <div className="search-overlay">
      <input 
        type="text" 
        placeholder="Search SF address or intersection"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <SearchResults results={results} onSelect={onLocationSelect} />
    </div>
  );
}
```

**Enhanced Map View:**
```typescript
// Show both user location AND searched location
<MapView
  userLocation={userLocation}        // Blue dot
  searchedLocation={searchedLocation} // Red pin
  blockfaces={blockfaces}
/>
```

## Performance Considerations

### Current Performance
- API response: <100ms for 95% of queries
- Map rendering: Smooth at 60fps
- Data size: ~50MB database

### Impact Analysis

| Change | Performance Impact | Mitigation |
|--------|-------------------|------------|
| Enhanced rule interpretation | +10-20ms processing | Cache interpretations |
| Address geocoding | +50-100ms API call | Debounce search, cache results |
| Out-of-SF detection | +5ms calculation | Run once on load |
| Progressive disclosure | Negligible | Client-side only |

### Optimization Strategies

1. **Interpretation Caching**
```typescript
// Cache interpreted results by blockface + time + duration
const cacheKey = `${blockface.id}-${checkTime.getTime()}-${duration}`;
if (interpretationCache.has(cacheKey)) {
  return interpretationCache.get(cacheKey);
}
```

2. **Geocoding Debounce**
```typescript
// Wait 300ms after user stops typing
const debouncedSearch = debounce(searchAddress, 300);
```

3. **Lazy Loading**
```typescript
// Load full rule details only when user expands
<BlockfaceDetail 
  detailLevel="summary" // Load full details on demand
/>
```

## Data Architecture Changes

### No Backend Schema Changes Required ✅

The current CNN-based architecture already supports all features:

1. **Address ranges stored**: `fromAddress`, `toAddress` fields exist
2. **Spatial indexing**: 2dsphere index enables radius queries
3. **Rule data complete**: All regulations attached during ingestion

### Frontend State Management

**New State Requirements:**
```typescript
interface AppState {
  // Existing
  userLocation: [number, number];
  blockfaces: Blockface[];
  selectedBlockface: Blockface | null;
  
  // New
  searchedLocation: [number, number] | null;
  isOutOfBounds: boolean;
  distanceToSF: number | null;
  searchQuery: string;
  searchResults: SearchResult[];
  detailLevel: 'summary' | 'full';
}
```

## Implementation Roadmap

### Phase 1: Enhanced Interpretation (Week 1-2)
**Priority: HIGH** - Fixes core UX issue

- [ ] Create `enhancedRuleEngine.ts` with multi-state logic
- [ ] Add RPP visitor parking detection
- [ ] Implement confidence scoring
- [ ] Add time-aware messaging ("legal now, but...")
- [ ] Update `BlockfaceDetail` to show enhanced results
- [ ] Test with real SF data

**Deliverable**: Users see nuanced parking status instead of binary legal/illegal

### Phase 2: Simplified Messaging (Week 2-3)
**Priority: HIGH** - Improves clarity

- [ ] Create message templates system
- [ ] Implement progressive disclosure UI
- [ ] Add "at-a-glance" status on map
- [ ] Create expandable detail view
- [ ] Add cost calculator for meters
- [ ] User testing with 10 SF residents

**Deliverable**: Clear, actionable parking information

### Phase 3: Geographic Awareness (Week 3)
**Priority: MEDIUM** - Prevents confusion

- [ ] Implement SF boundary detection
- [ ] Create out-of-bounds modal
- [ ] Add distance calculation
- [ ] Design "near SF" vs "far from SF" experiences
- [ ] Add "View SF Map" fallback
- [ ] Test in Oakland, Daly City, San Jose

**Deliverable**: Users outside SF understand app scope

### Phase 4: Address Search (Week 4-5)
**Priority: MEDIUM** - Adds planning capability

- [ ] Integrate Mapbox Geocoding API
- [ ] Create search UI component
- [ ] Implement search results display
- [ ] Add virtual pin on map
- [ ] Store recent searches
- [ ] Add "Get Directions" link
- [ ] Test with common SF addresses

**Deliverable**: Users can check parking before arriving

### Phase 5: Polish & Optimization (Week 6)
**Priority: LOW** - Performance tuning

- [ ] Add interpretation caching
- [ ] Optimize geocoding with debounce
- [ ] Implement lazy loading for details
- [ ] Add analytics for feature usage
- [ ] Performance testing
- [ ] Bug fixes

**Deliverable**: Fast, polished experience

## Testing Strategy

### Unit Tests
```typescript
describe('Enhanced Rule Engine', () => {
  it('detects RPP visitor parking allowances', () => {
    const result = evaluateEnhancedLegality(rppBlockface, now, 120);
    expect(result.status).toBe('legal-with-conditions');
    expect(result.conditions).toContain('2hr visitor limit');
  });
  
  it('combines meter + time limit clearly', () => {
    const result = evaluateEnhancedLegality(meterBlockface, now, 180);
    expect(result.primaryMessage).toContain('$3.50/hr');
    expect(result.conditions).toContain('2hr limit');
  });
});
```

### Integration Tests
```typescript
describe('Address Search', () => {
  it('geocodes SF addresses correctly', async () => {
    const results = await searchAddress('1234 Market St');
    expect(results[0].coordinates).toBeInSF();
  });
  
  it('limits results to SF boundaries', async () => {
    const results = await searchAddress('123 Main St');
    results.forEach(r => {
      expect(isInSanFrancisco(r.lat, r.lng)).toBe(true);
    });
  });
});
```

### User Acceptance Testing

**Test Scenarios:**

1. **RPP Zone Visitor**
   - User checks RPP zone blockface
   - Expects: "Visitor parking 2hr" not "Illegal"

2. **Out-of-SF User**
   - User opens app in Oakland
   - Expects: Clear message about SF-only service

3. **Address Search**
   - User searches "Ferry Building"
   - Expects: Map centers on location, shows parking

4. **Planning Ahead**
   - User searches destination address
   - Checks parking for appointment time
   - Expects: Accurate future-time evaluation

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Geocoding API costs | Medium | Low | Use free tier (100k/mo), add rate limiting |
| RPP visitor rules vary | High | Medium | Parse regulation text, show confidence level |
| Performance degradation | Low | High | Cache aggressively, lazy load details |
| User confusion with search | Medium | Medium | Clear UI, onboarding tooltips |

## Success Metrics

### Quantitative
- **Interpretation accuracy**: >95% correct status (vs current ~80%)
- **User comprehension**: >90% understand status in <5 seconds
- **Out-of-SF bounce rate**: <10% (vs current ~40%)
- **Address search usage**: >30% of sessions
- **Performance**: Maintain <100ms API response time

### Qualitative
- Users report "clearer" parking information
- Fewer error reports about incorrect status
- Positive feedback on address search feature
- Reduced support requests about "app not working"

## Conclusion

These enhancements address all four identified issues without requiring backend rearchitecture:

1. ✅ **Better interpretation**: Multi-state logic with RPP intelligence
2. ✅ **Clearer messaging**: Progressive disclosure, plain language
3. ✅ **Geographic awareness**: Detect out-of-SF, provide guidance
4. ✅ **Address search**: Plan ahead without being present

**Key Insight**: The current CNN-based backend architecture is solid and supports all features. Changes are primarily frontend UX improvements with minimal performance impact.

**Recommendation**: Proceed with phased implementation, starting with enhanced interpretation (highest impact, lowest risk).