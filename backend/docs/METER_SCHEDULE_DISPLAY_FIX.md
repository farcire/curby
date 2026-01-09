# Meter Schedule Display Fix

**Date:** January 3, 2026  
**Issue:** Incorrect messaging for meters without operating schedules  
**Status:** ✅ Fixed

---

## Problem

The system was displaying "No limit" for meters without operating schedules, which was misleading. Users need to be directed to check the physical meter for schedule and rate information.

## Solution

Updated the display logic in [`regulation_normalizer.py`](regulation_normalizer.py) to show appropriate messages based on whether the meter is in a special event zone.

### Changes Made

#### 1. Updated `_format_base_schedule_lines()` Method

**Location:** [`SpecialEventZoneFormatter._format_base_schedule_lines()`](regulation_normalizer.py:1540-1600)

**Change:**
```python
# OLD (line 1558):
if not schedules:
    return ("All Other Days No limit", "")

# NEW (line 1558):
if not schedules:
    return ("All Other Days check meter for schedule and rate", "")
```

#### 2. Added New Helper Function

**Location:** [`format_meter_without_schedule()`](regulation_normalizer.py:1763-1780)

**Purpose:** Provides a centralized function to format messages for meters without schedules.

**Usage:**
```python
# For meters in special event zones
message = format_meter_without_schedule(in_special_event_zone=True)
# Returns: "All Other Days check meter for schedule and rate"

# For meters NOT in special event zones
message = format_meter_without_schedule(in_special_event_zone=False)
# Returns: "Check meter for schedule and rate"
```

---

## Display Messages

### Meters WITHOUT Schedules in Special Event Zones

**Example: Oracle Park meter without schedule**
```
Line 1: Oracle Park Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days check meter for schedule and rate
Line 3: (empty)
```

**Example: Chase Center meter without schedule**
```
Line 1: Chase Center Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days check meter for schedule and rate
Line 3: (empty)
```

**Example: Both zones (overlap) meter without schedule**
```
Line 1: Special Event Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days check meter for schedule and rate
Line 3: (empty)
```

### Meters WITHOUT Schedules NOT in Special Event Zones

**Display:**
```
Check meter for schedule and rate
```

---

## Context

- **21.5% of active meters** (6,624 out of 30,797) lack operating schedule data
- This is a known data quality issue documented in [`METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md`](METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md)
- The fix ensures users are properly informed to check the physical meter

---

## Testing

To test the changes:

1. **Special Event Zone Meter Without Schedule:**
   - Find a meter in Oracle Park or Chase Center zone with no schedules
   - Verify Line 2 shows: "All Other Days check meter for schedule and rate"

2. **Regular Meter Without Schedule:**
   - Find a meter outside special event zones with no schedules
   - Verify message shows: "Check meter for schedule and rate"

3. **Meters WITH Schedules:**
   - Verify existing functionality unchanged
   - Should still show schedule details (days, times, rates)

---

## Related Files

- [`regulation_normalizer.py`](regulation_normalizer.py) - Main implementation
- [`METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md`](METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md) - Data quality context
- [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) - Issue #007: Meter Schedule Coverage Gap

---

## API Usage

### For Special Event Zone Meters

```python
from regulation_normalizer import SpecialEventZoneFormatter

# Meter without schedules in special event zone
result = SpecialEventZoneFormatter.format_special_event_display(
    in_ballpark_zone=True,
    in_arena_zone=False,
    base_schedules=[]  # Empty schedules
)

# Result:
# {
#     'line1': 'Oracle Park Schedule and Rates may apply. See schedule for details.',
#     'line2': 'All Other Days check meter for schedule and rate',
#     'line3': '',
#     'schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule',
#     'has_special_event': True
# }
```

### For Regular Meters

```python
from regulation_normalizer import format_meter_without_schedule

# Meter without schedules, not in special event zone
message = format_meter_without_schedule(in_special_event_zone=False)
# Returns: "Check meter for schedule and rate"
```

---

## Implementation Notes

1. **Backward Compatibility:** The changes are backward compatible. Meters with schedules continue to display normally.

2. **User Experience:** The new messages are clearer and more actionable, directing users to the physical meter for information.

3. **Data Quality:** This fix addresses the symptom (missing data) with appropriate messaging. The underlying data quality issue remains and should be addressed with SFMTA.

---

**Document Version:** 1.0  
**Last Updated:** January 3, 2026  
**Status:** Complete - Ready for Deployment