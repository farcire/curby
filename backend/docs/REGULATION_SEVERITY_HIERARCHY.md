# Regulation Severity Hierarchy

**Document Version:** 1.0  
**Last Updated:** December 30, 2024  
**Status:** Architecture Standard

---

## Overview

This document defines the **severity-based regulation layering architecture** used throughout the Curby parking system. All parking regulations are organized by severity level to ensure users always see the most restrictive rule that applies at any given time.

---

## Core Principle

**Regulations are layered from LEAST to MOST severe**, with the system always displaying the **most severe active regulation** to users.

This ensures:
- User safety (no missed towing risks)
- Clear communication (one primary restriction shown)
- Correct prioritization (absolute restrictions override convenience rules)

---

## Severity Hierarchy

### Level 1: Non-Metered Regulations (LEAST SEVERE)

**Types:**
- Time-limited parking (e.g., "2-hour parking")
- Residential permit parking (RPP zones)
- General parking restrictions
- No parking zones (non-tow)

**User Impact:** Mildest
- You CAN park with time/permit limits
- Violations result in parking tickets ($76+)
- No immediate towing risk

**Example:**
```
"2-hour parking, 9 AM - 6 PM, Monday-Friday"
```

---

### Level 2: Metered Parking (MODERATE)

**Types:**
- **OP** (Paid Operation): Standard metered parking with rates and time limits
- **FREE**: No payment required during this window
- **PRE** (Prepay): Can prepay before enforcement begins
- **TOW**: NO PARKING at meter during this schedule (meter-specific)
- **ALTERNATE**: Different meter rules on certain days (e.g., different rates, time limits)

**User Impact:** Moderate
- You CAN park if you pay (or during free periods)
- Meter TOW schedule = no parking at that specific meter
- Violations result in parking tickets
- Payment required but parking allowed (unless meter TOW active)

**Internal Meter Schedule Priority:**
```
TOW > ALTERNATE > OP/FREE/PRE
```

**Important Distinctions:**
- **TOW** is a meter-specific schedule type (not a separate regulation category)
- **ALTERNATE** means different rules on certain days (NOT alternate side parking)
  - Example: Higher rates during special events, different time limits on weekends
- All meter schedules apply only to metered spaces
- Meter TOW is overridden by street sweeping (Level 3)

**Example:**
```
"Metered parking: $4/hour, 2-hour limit, Mon-Sat 9 AM - 6 PM"
"Meter TOW: No parking at this meter, Thu 2-4 PM"
"Meter ALTERNATE: $12/hour during special events"
```

---

### Level 3: Street Sweeping (MOST SEVERE)

**Types:**
- Street cleaning schedules
- Absolute parking prohibition during sweeping times

**User Impact:** Most Severe
- GUARANTEED towing if parked during sweeping
- No exceptions or workarounds
- Overrides ALL other regulations (including meter TOW schedules)
- Applies to entire street segment (not just metered areas)
- Violations result in towing ($300+) + ticket ($76+)

**Example:**
```
"Street Sweeping: No parking Tuesday 8-10 AM"
```

**Critical Distinction:**
- **Street sweeping** = Street-level absolute restriction (applies to entire segment)
- **Meter TOW** = Meter-specific restriction (applies only to that metered space)
- Street sweeping overrides meter TOW because it's a higher severity level

---

## Data Processing Flow

When determining parking legality at a specific time:

```
1. Check street sweeping (Level 3)
   ↓ Is it currently sweeping time?
   → If YES: Display "Street Sweeping - No Parking" (STOP HERE)
   
2. Check metered parking (Level 2)
   ↓ Is there a meter? What schedule is active?
   → Check meter schedule priority: TOW > ALTERNATE > OP/FREE/PRE
   → If meter TOW: Display "Tow-Away - No Parking (Meter)"
   → If meter ALTERNATE: Display alternate rules
   → If meter OP/FREE/PRE: Display standard meter info
   
3. Check non-metered regulations (Level 1)
   ↓ What base regulations apply?
   → Display time limits, RPP requirements, etc.
```

---

## Display Logic

### Algorithm

```python
def get_active_regulation(segment, datetime):
    """
    Returns the most severe active regulation.
    """
    # Priority 1: Check street sweeping (Severity 3 - Most Severe)
    for rule in segment['rules']:
        if rule['type'] == 'street-sweeping' and is_active_at_time(rule, datetime):
            return {
                'severity': 3,
                'type': 'street-sweeping',
                'status': 'NO_PARKING',
                'description': 'Street Sweeping - No Parking'
            }
    
    # Priority 2: Check metered parking (Severity 2)
    if segment.get('meters'):
        for meter in segment['meters']:
            meter_schedule = get_effective_meter_schedule(meter['post_id'], datetime)
            if meter_schedule:
                return {
                    'severity': 2,
                    'type': 'metered',
                    'schedule': meter_schedule
                }
    
    # Priority 3: Check non-metered regulations (Severity 1)
    for rule in segment['rules']:
        if rule['type'] in ['time-limit', 'rpp-zone', 'parking-regulation']:
            if is_active_at_time(rule, datetime):
                return {
                    'severity': 1,
                    'type': rule['type'],
                    'rule': rule
                }
    
    return None

def get_effective_meter_schedule(post_id, datetime):
    """
    Determine effective meter schedule respecting internal meter priority.
    Note: Street sweeping is checked at segment level, not here.
    
    Internal meter schedule priority: TOW > ALTERNATE > OP/FREE/PRE
    """
    schedules = get_all_schedules(post_id, datetime)
    
    # Priority 1: Check meter TOW schedules
    tow = [s for s in schedules if s['schedule_type'] == 'TOW']
    if tow and is_time_in_schedule(datetime, tow[0]):
        return {
            'type': 'TOW',
            'status': 'NO_PARKING',
            'description': 'Tow-Away - No Parking (Meter)'
        }
    
    # Priority 2: Check ALTERNATE (different rules on certain days)
    alt = [s for s in schedules if s['schedule_type'] == 'ALTERNATE']
    if alt and is_time_in_schedule(datetime, alt[0]):
        return {
            'type': 'ALTERNATE',
            'status': 'METERED_ALTERNATE',
            'description': f'Metered: {alt[0]["rate"]}/hour, {alt[0]["time_limit"]} min',
            'rate': alt[0]['rate'],
            'time_limit': alt[0]['time_limit']
        }
    
    # Priority 3: Return base metered schedule (OP/FREE/PRE)
    base = [s for s in schedules if s['schedule_type'] in ['OP', 'FREE', 'PRE']]
    return get_applicable_base_schedule(datetime, base)

def get_severity(regulation_type):
    """Map regulation type to severity level"""
    severity_map = {
        'street-sweeping': 3,      # Most severe - street-level
        'metered': 2,              # Includes TOW/ALTERNATE/OP/FREE/PRE
        'time-limit': 1,
        'rpp-zone': 1,
        'parking-regulation': 1    # Least severe
    }
    return severity_map.get(regulation_type, 1)
```

### Display Examples

**Scenario 1: Multiple regulations active**
- Base: "2-hour parking" (Level 1)
- Metered: "$4/hour" (Level 2)
- Sweeping: "Tuesday 8-10 AM" (Level 3)

At Tuesday 9 AM:
```
Display: "Street Sweeping - No Parking"
(Level 3 overrides Levels 1 and 2)
```

At Monday 2 PM:
```
Display: "Metered Parking - $4/hour, 2-hour limit"
(Level 2 overrides Level 1)
```

At Monday 8 PM (after meter hours):
```
Display: "2-hour parking limit"
(Only Level 1 active)
```

**Scenario 2: Meter with TOW schedule + Street Sweeping**
- Meter TOW: "Thursday 2-4 PM" (Level 2)
- Street Sweeping: "Thursday 8-10 AM" (Level 3)

At Thursday 9 AM:
```
Display: "Street Sweeping - No Parking"
(Level 3 overrides meter TOW)
```

At Thursday 3 PM:
```
Display: "Tow-Away - No Parking (Meter)"
(Meter TOW schedule active)
```

---

## Implementation Guidelines

### For Data Ingestion

**File:** [`backend/ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)

1. **STEP 3:** Ingest street sweeping (Level 3) - Most severe, street-level
2. **STEP 4:** Ingest parking regulations (Level 1) - Non-metered
3. **STEP 5:** Ingest meters with schedules (Level 2) - Includes TOW/ALTERNATE/OP/FREE/PRE

All regulations stored in `segment['rules']` array with type field for severity mapping.

### For API Responses

**File:** [`backend/main.py`](main.py)

1. Query all regulations for segment
2. Check street sweeping first (Level 3)
3. If no sweeping, check meter schedules (Level 2) with internal priority
4. If no meters or outside meter hours, check non-metered (Level 1)
5. Return most severe regulation
6. Include severity level in response for client-side logic

### For Frontend Display

**File:** [`frontend/src/utils/ruleEngine.ts`](../frontend/src/utils/ruleEngine.ts)

1. Receive regulations with severity levels
2. Display most severe regulation prominently
3. Show lower severity regulations as "Additional Info"
4. Use color coding: Red (Level 3), Orange (Level 2), Green (Level 1)

---

## Data Quality Implications

### Missing Street Sweeping Data = CRITICAL

Street sweeping is **Level 3 (Most Severe)**. Missing this data is more critical than missing any other regulation type because:

1. **User Safety:** Guaranteed towing risk
2. **Financial Impact:** $300+ towing + $76+ ticket
3. **Display Logic:** System will show incorrect "most severe" regulation
4. **Hierarchy Violation:** Users see Level 1-2 rules but miss Level 3 absolute restriction
5. **Street-Level Impact:** Affects entire segment, not just metered areas

**Reference:** See Issue #006 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

### Manual Override Priority

When applying manual overrides (STEP 5.4), prioritize by severity:
1. First: Street sweeping corrections (Level 3)
2. Second: Meter schedule corrections (Level 2)
3. Third: Time-limit corrections (Level 1)

---

## Key Distinctions

### Street Sweeping vs Meter TOW

| Aspect | Street Sweeping (Level 3) | Meter TOW (Level 2) |
|--------|---------------------------|---------------------|
| **Scope** | Entire street segment | Specific metered space only |
| **Severity** | 3 (Most Severe) | 2 (within meter schedules) |
| **Override** | Overrides everything | Overridden by street sweeping |
| **Source** | Street Cleaning Schedules dataset | Meter Operating Schedules dataset |
| **Type** | Street-level regulation | Meter-specific schedule type |

### ALTERNATE Schedule

**What it IS:**
- Different meter rules on certain days
- Example: Higher rates during special events ($12/hour vs $4/hour)
- Example: Different time limits on weekends (4 hours vs 2 hours)

**What it is NOT:**
- NOT alternate side parking
- NOT a separate regulation category
- NOT street-level (meter-specific only)

---

## Testing Requirements

### Unit Tests

Test severity mapping:
```python
def test_severity_mapping():
    assert get_severity('street-sweeping') == 3
    assert get_severity('metered') == 2
    assert get_severity('time-limit') == 1
```

### Integration Tests

Test display logic:
```python
def test_display_most_severe():
    segment = {
        'rules': [
            {'type': 'time-limit', 'active': True},
            {'type': 'street-sweeping', 'active': True}
        ],
        'meters': [{'post_id': '123', 'schedules': [...]}]
    }
    result = get_active_regulation(segment, datetime.now())
    assert result['type'] == 'street-sweeping'  # Level 3 wins
```

---

## Related Documentation

- [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Layer 5 regulation architecture
- [`CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md`](CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md) - Meter schedule priority
- [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Issue #1: Missing street sweeping
- [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) - Issue #006: Street sweeping severity
- [`CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`](../CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md) - Section 15: Meter integration

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-30 | Initial documentation of severity-based hierarchy |

---

**Document Status:** Architecture Standard  
**Approval Required:** Yes (for any changes to severity levels)  
**Review Cycle:** Quarterly