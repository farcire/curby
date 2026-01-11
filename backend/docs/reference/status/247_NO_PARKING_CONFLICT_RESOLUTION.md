# 24/7 No Parking Conflict Resolution

**Date**: January 4, 2026  
**Issue**: CNN 8713000 R (500-598 MARIPOSA North) and 23 other segments showing conflicting rules  
**Root Cause**: Spatial matching adds both "No Parking" and "Time Limit with RPP" rules without conflict detection

## Problem Statement

### Observed Behavior
Segments with 24/7 "No Parking" regulations were displaying conflicting rules:
- "No Parking except permit"
- "1hr limit M-Sa 8am-10pm except permit"

### Physical Verification
User confirmed CNN 8713000 R (Mariposa Street) has "No Parking Any Time" signage, making the time-limit rules incorrect.

### Data Architecture Issue
1. **Ingestion Layer** (`repopulate_segment_rules.py`): Blindly appends all spatially-matched regulations
2. **Interpretation Layer** (`generate_interpretation_layer.py`): Was NOT filtering conflicting rules

## Solution Implemented

### Conflict Resolution Logic

Added to `generate_interpretation_layer.py` lines 201-220:

```python
# Check for 24/7 "No Parking" rules (no time/day restrictions)
# These override time-limit and RPP rules since parking is never allowed
has_247_no_parking = any(
    'no parking' in str(r.get('regulation', '')).lower() and
    r.get('type') == 'no-parking' and
    (not r.get('activeDays') or len(r.get('activeDays', [])) == 0) and
    (not r.get('startTimeMin') or r.get('startTimeMin') == 0) and
    (not r.get('endTimeMin') or r.get('endTimeMin') == 0)
    for r in rules
)

# Filter out conflicting rules if 24/7 no-parking exists
if has_247_no_parking:
    # Keep: no-parking, street-sweeping, tow-away
    # Remove: time-limit, rpp-zone (these conflict with 24/7 no parking)
    filtered_rules = [
        r for r in rules 
        if r.get('type') in ('no-parking', 'street-sweeping', 'tow-away') or
           'no parking' in str(r.get('regulation', '')).lower()
    ]
else:
    filtered_rules = rules
```

### Detection Criteria for 24/7 No Parking

A rule is considered "24/7 No Parking" if ALL of the following are true:
1. Contains "no parking" in regulation text (case-insensitive)
2. Type is `no-parking`
3. No active days specified OR empty array
4. No start time OR start time is 0 (midnight)
5. No end time OR end time is 0 (midnight)

### Conflict Resolution Rules

When 24/7 No Parking is detected:
- **KEEP**: `no-parking`, `street-sweeping`, `tow-away` rules
- **REMOVE**: `time-limit`, `rpp-zone` rules (these conflict)

### Why This Works

1. **Time-bound No Parking** (e.g., "No Parking M, W 10pm-12am") has `activeDays` and time bounds → NOT filtered
2. **24/7 No Parking** has no time/day restrictions → Filters out conflicting time-limits
3. **Street Cleaning** is kept because it's additional information about when towing occurs
4. **Tow-Away** is kept as it's enforcement-related, not a parking allowance

## Expected Display for CNN 8713000 R

### Before Fix
```
- No Parking except permit
- Street Cleaning Tu 1am-6am
- 1hr limit M-Sa 8am-10pm except permit  ← WRONG (conflicts with No Parking)
```

### After Fix
```
- No Parking
- Street Cleaning Tu 1am-6am
```

### Eligibility Logic
- **Status**: `always_ineligible` = true
- **Reason**: 24/7 No Parking applies at all times and days
- **User can park**: false (never eligible)

## Affected Segments

24 segments identified with conflicting rules:
- CNN 11114000 L: RODGERS ST
- CNN 4929000 R: DORE ST
- CNN 7702000 R: JUNIPER ST
- CNN 4110000 L: CLAY ST
- CNN 6700000 L: HARRIET ST
- CNN 8713000 R: MARIPOSA ST (user-verified)
- ... and 18 others

## Implementation Steps

1. ✅ Added conflict detection logic to `generate_interpretation_layer.py`
2. ⏳ Regenerate interpretation layer for all 34,324 segments
3. ⏳ Verify CNN 8713000 R displays correctly
4. ⏳ Update API response (remove duplicate `street_name` field)

## Testing

### Test Case 1: 24/7 No Parking
```python
rules = [
    {'type': 'no-parking', 'regulation': 'No parking any time', 'activeDays': []},
    {'type': 'time-limit', 'timeLimit': '1', 'permitArea': 'EE'},
    {'type': 'street-sweeping', 'day': 'Tu'}
]
# Expected: Only no-parking and street-sweeping displayed
```

### Test Case 2: Time-Bound No Parking
```python
rules = [
    {'type': 'no-parking', 'regulation': 'No parking', 'activeDays': [0, 2], 'startTimeMin': 1320},
    {'type': 'time-limit', 'timeLimit': '2', 'activeDays': [1, 3, 4]}
]
# Expected: Both rules displayed (no conflict)
```

## Related Issues

- **Issue #007**: 21.5% of meters lack operating schedules
- **Schema Cleanup**: Removed unused `street_name` field
- **Day Mapping Bug**: Fixed canonical day format (0=Monday)

## References

- `backend/generate_interpretation_layer.py` lines 184-220
- `backend/cleanup_street_segments_schema.py`
- `backend/repopulate_segment_rules.py`