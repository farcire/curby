# ALTERNATE Schedule Analysis Summary

**Date:** December 31, 2024  
**Dataset:** Meter Operating Schedules (6cqg-dxku)  
**Status:** ✅ COMPLETE ANALYSIS

---

## Key Findings

### 1. ALTERNATE Schedules with "Posted Events"

**Total Records:** 19 entries  
**Schedule Type:** ALTERNATE  
**Days Applied:** "Posted Events"  
**Cap Color:** WHITE (Passenger loading zone) and GREY/GREEN

### 2. Locations Identified

**Howard St 800 Block (Even side):**
- 15 meters with Post IDs: 470-08161 through 470-08327
- Cap Color: GREY
- Applied Color Rule: WHITE - Passenger loading zone
- Time: 12:00 AM - 12:00 AM (all day)
- Time Limit: 0 minutes (no parking allowed)

**16th St 3100 Block (Odd side):**
- 2 meters with Post IDs: 216-31010, 216-31030
- Cap Color: GREY
- Applied Color Rule: WHITE - Passenger loading zone
- Time: 12:00 AM - 12:00 AM (all day)
- Time Limit: 0 minutes

**Stockton St 1600 Block (Even side):**
- 2 meters with Post IDs: 664-16120, 664-16140
- Cap Color: GREEN
- Applied Color Rule: WHITE - Passenger loading zone
- Time: 12:00 AM - 12:00 AM (all day)
- Time Limit: 0 minutes

---

## Critical Discovery: WHITE Applied Color Rule

### What WHITE Means

**WHITE = Passenger Loading Zone ONLY**

- **NOT for parking** - vehicles cannot park here
- **Passenger loading/unloading only** - brief stops to pick up or drop off passengers
- **Severity Level:** 3 (TOW + VIOLATION)
- **Consequence:** Vehicle will be towed + parking violation ticket
- **Time Limit:** 0 minutes (no parking duration allowed)

### Distinction from Cap Color

**Important:** The "Applied Color Rule" field shows WHITE, while the physical "Cap Color" may be GREY or GREEN.

- **Cap Color:** Physical color of meter cap (GREY, GREEN, etc.)
- **Applied Color Rule:** Regulatory restriction (WHITE = passenger loading)
- **Priority:** Applied Color Rule overrides Cap Color for regulation purposes

---

## ALTERNATE Schedule Pattern: "Posted Events"

### What "Posted Events" Means

**NOT standard day-of-week pattern** - this is a special designation:

1. **Event-Based Activation:** These ALTERNATE schedules activate during posted special events
2. **Dynamic Application:** Not every Sunday or Monday - only when events are posted
3. **Geospatial Correlation:** These meters should fall within Special Event Area boundaries
4. **Passenger Loading:** During events, these spaces convert to passenger loading zones

### Example Use Case

**Howard St 800 block during Oracle Park game:**
- Normal days: Standard metered parking (OP schedule)
- Posted event days: Passenger loading zone only (ALTERNATE schedule with WHITE rule)
- Purpose: Facilitate passenger drop-off/pick-up during high-traffic events

---

## Regulation Normalization Requirements

### 1. Cap Color + Applied Color Rule Handling

```python
def normalize_meter_cap_color(cap_color, applied_color_rule):
    """
    Normalize meter restrictions considering both cap color and applied rule.
    Applied Color Rule takes precedence.
    """
    # Priority 1: Check Applied Color Rule
    if applied_color_rule:
        rule_upper = str(applied_color_rule).upper()
        
        if 'WHITE' in rule_upper or 'PASSENGER LOADING' in rule_upper:
            return {
                'restriction_type': 'PASSENGER_LOADING_ONLY',
                'severity': 3,  # TOW + VIOLATION
                'user_eligible_for_parking': False,
                'display_text': 'Passenger Loading Zone',
                'display_detail': 'No parking - Loading/unloading only',
                'consequence': 'Vehicle will be towed if parked'
            }
    
    # Priority 2: Check Cap Color (if no applied rule)
    cap_upper = str(cap_color).upper()
    
    if cap_upper == 'WHITE':
        return {
            'restriction_type': 'PASSENGER_LOADING_ONLY',
            'severity': 3,
            'user_eligible_for_parking': False,
            'display_text': 'Passenger Loading Zone'
        }
    
    elif cap_upper in ['YELLOW', 'RED']:
        return {
            'restriction_type': 'COMMERCIAL_ONLY',
            'severity': 1,
            'user_eligible_for_parking': False,
            'display_text': 'Commercial Vehicles Only'
        }
    
    elif cap_upper in ['GREEN', 'BLACK', 'GREY']:
        return {
            'restriction_type': 'STANDARD',
            'severity': 1,
            'user_eligible_for_parking': True,
            'display_text': 'Standard parking'
        }
    
    else:
        return {
            'restriction_type': 'UNKNOWN',
            'severity': 1,
            'user_eligible_for_parking': False,
            'display_text': 'Check meter for restrictions'
        }
```

### 2. "Posted Events" Days Applied Handling

```python
def is_posted_events_active(days_applied, current_date):
    """
    Check if 'Posted Events' schedule is active.
    Requires checking dynamic event calendar.
    """
    if str(days_applied).lower() == 'posted events':
        # Query event calendar for this date
        active_events = get_active_special_events(current_date)
        return len(active_events) > 0
    
    return False

def get_effective_meter_schedule(meter, datetime):
    """
    Get effective schedule considering Posted Events.
    """
    schedules = meter['base_schedules']
    
    # Check for Posted Events ALTERNATE schedule
    posted_event_alt = [s for s in schedules 
                       if s['schedule_type'] == 'ALTERNATE' 
                       and str(s.get('days_applied', '')).lower() == 'posted events']
    
    if posted_event_alt and is_posted_events_active(posted_event_alt[0]['days_applied'], datetime):
        # Posted event is active - use ALTERNATE schedule
        return posted_event_alt[0]
    
    # Otherwise use standard priority: TOW > ALTERNATE > OP > PRE+FREE
    return get_standard_priority_schedule(schedules, datetime)
```

### 3. Complete Eligibility Check

```python
def check_parking_eligibility_with_posted_events(location, datetime, duration_minutes):
    """
    Complete eligibility check including Posted Events and WHITE zones.
    """
    cnn_data = get_cnn_data(location)
    
    # Severity 3 checks (TOW + VIOLATION)
    
    # 1. Street sweeping
    if has_street_sweeping(cnn_data, datetime):
        return ineligible('STREET_SWEEPING', severity=3)
    
    # 2. Check meters
    if has_meters(cnn_data):
        effective_schedule = get_effective_meter_schedule(cnn_data['meters'][0], datetime)
        
        # 2a. Meter TOW schedule
        if effective_schedule['schedule_type'] == 'TOW':
            return ineligible('METER_TOW', severity=3)
        
        # 2b. WHITE applied color rule (Passenger Loading)
        if effective_schedule.get('applied_color_rule'):
            color_rule = normalize_meter_cap_color(
                effective_schedule.get('cap_color'),
                effective_schedule.get('applied_color_rule')
            )
            
            if color_rule['restriction_type'] == 'PASSENGER_LOADING_ONLY':
                return ineligible('PASSENGER_LOADING_ZONE', severity=3)
        
        # 2c. Check if Posted Events ALTERNATE is active
        if (effective_schedule['schedule_type'] == 'ALTERNATE' and
            str(effective_schedule.get('days_applied', '')).lower() == 'posted events'):
            
            # Check applied color rule for this ALTERNATE schedule
            color_rule = normalize_meter_cap_color(
                effective_schedule.get('cap_color'),
                effective_schedule.get('applied_color_rule')
            )
            
            if color_rule['restriction_type'] == 'PASSENGER_LOADING_ONLY':
                return ineligible('PASSENGER_LOADING_DURING_EVENT', severity=3)
    
    # Continue with Severity 1 checks...
```

---

## Updated Severity Hierarchy

### Severity 3 (TOW + VIOLATION)

1. **Street Sweeping** (street-level)
2. **No Parking Anytime zones** (street-level)
3. **Meter TOW schedules** (meter-specific)
4. **WHITE zones - Passenger Loading Only** (meter-specific)
   - Includes ALTERNATE schedules with WHITE applied color rule
   - Includes "Posted Events" ALTERNATE schedules with passenger loading

### Severity 1 (VIOLATION only, no tow)

1. **Time-limited parking** (non-metered)
2. **RPP zones** (non-metered, with non-permit time limits)
3. **Meter OP/ALTERNATE schedules** (metered, paid operation)
4. **YELLOW/RED cap colors** (commercial vehicles only)

---

## Data Structure Updates

### Meter Schedule with Applied Color Rule

```json
{
  "post_id": "470-08161",
  "base_schedules": [
    {
      "schedule_type": "ALTERNATE",
      "days_applied": "Posted Events",
      "from_time": "12:00:00",
      "to_time": "12:00:00",
      "time_limit": 0,
      "rate": null,
      "cap_color": "GREY",
      "applied_color_rule": "White - Passenger loading zone",
      "normalized": {
        "restriction_type": "PASSENGER_LOADING_ONLY",
        "severity": 3,
        "user_eligible": false,
        "display_text": "Passenger Loading Zone",
        "display_detail": "No parking during posted events - Loading/unloading only"
      }
    },
    {
      "schedule_type": "OP",
      "days_applied": "Mon-Sun",
      "from_time": "09:00:00",
      "to_time": "18:00:00",
      "time_limit": 120,
      "rate": "4.00",
      "cap_color": "GREY"
    }
  ]
}
```

---

## Geospatial Verification Needed

### Action Items

1. **Verify Howard St 800 block** is within Special Event Area boundary (likely Oracle Park area)
2. **Verify 16th St 3100 block** location relative to event areas
3. **Verify Stockton St 1600 block** location relative to event areas

### Expected Result

All 19 meters with "Posted Events" ALTERNATE schedules should fall within the geospatial boundaries defined in Special Event Areas dataset (itv4-r6g6).

---

## Summary for Regulation Normalization

### Key Takeaways

1. **ALTERNATE schedules are NOT just day-of-week variations**
   - Can include "Posted Events" designation
   - Requires dynamic event calendar integration

2. **WHITE applied color rule = Severity 3**
   - Same severity as street sweeping and meter TOW
   - Vehicle will be towed if parked
   - Must be checked in eligibility logic

3. **Applied Color Rule overrides Cap Color**
   - Physical cap may be GREY/GREEN
   - Applied rule may specify WHITE (passenger loading)
   - Use Applied Color Rule for regulation determination

4. **Time Limit = 0 minutes means NO PARKING**
   - Not "unlimited parking"
   - Indicates absolute prohibition (loading zone)

5. **Posted Events require event calendar**
   - Cannot determine eligibility from schedule alone
   - Must query active events for the requested date
   - Integration with Meter Policies or event calendar needed

---

## Implementation Priority

### Phase 1: Immediate (Regulation Normalizer)
- ✅ Add WHITE cap color handling (Severity 3)
- ✅ Add Applied Color Rule field parsing
- ✅ Update cap color normalization to check Applied Color Rule first
- ✅ Add "Posted Events" days_applied pattern recognition

### Phase 2: Event Integration
- ⏭️ Create event calendar integration
- ⏭️ Implement Posted Events activation logic
- ⏭️ Geospatial verification of Posted Events meters

### Phase 3: User Display
- ⏭️ Update UI to show "Passenger Loading Zone" for WHITE zones
- ⏭️ Add event-based schedule notifications
- ⏭️ Display "During posted events only" for Posted Events ALTERNATE schedules

---

**Document Version:** 1.0  
**Last Updated:** December 31, 2024  
**Status:** Analysis Complete - Implementation Pending