# ALTERNATE Schedules - Complete Analysis & Implementation Guide

**Analysis Date:** December 31, 2024  
**Status:** ✅ COMPLETE  
**Dataset:** Meter Operating Schedules (6cqg-dxku)  
**Total Schedules Analyzed:** 72,365

---

## Executive Summary

This document provides the complete analysis of ALTERNATE schedule patterns in the Meter Operating Schedules dataset, including 7 non-day-of-week patterns representing event-based and condition-based passenger loading zones.

### Key Findings

- **Total ALTERNATE schedules:** 371 (0.51% of all schedules)
- **All are passenger loading zones** when active (Severity 3: TOW + VIOLATION)
- **All have base Operating Schedules** for normal operation (Severity 1)
- **No special calendar integration needed** - display both rules to users

---

## All Non-Day-of-Week ALTERNATE Patterns

### Pattern Summary Table

| Pattern | Count | % of Total | Interpretation | Locations |
|---------|-------|------------|----------------|-----------|
| **School Days** | 177 | 0.24% | School Days | 23rd St 3300 block |
| **Giants Day** | 52 | 0.07% | Giants Day Games | 2nd St 600 block (Oracle Park) |
| **Giants Night** | 52 | 0.07% | Giants Night Games | 2nd St 600 block (Oracle Park) |
| **Performance** | 50 | 0.07% | Special Event Periods | Castro St 400, Fillmore St 2200 |
| **Posted Events** | 19 | 0.03% | Special Event Periods | 16th St 3100, Howard St 800, Stockton St 1600 |
| **Posted Services** | 19 | 0.03% | Service Periods | 23rd St 3200 block |
| **Business Hours** | 2 | 0.00% | Business Hours | California St 700, Eddy St 900 |
| **TOTAL** | **371** | **0.51%** | | |

### Pattern Details

#### 1. School Days (177 schedules)
- **Location:** 23rd St 3300 block
- **Time:** 7:00 AM - 4:00 PM
- **Purpose:** School zone passenger drop-off/pick-up
- **Active:** During school days only
- **Display:** "Passenger Loading Zone on School Days"

#### 2. Giants Day (52 schedules)
- **Location:** 2nd St 600 block (near Oracle Park)
- **Time:** 1:00 PM - 6:00 PM
- **Purpose:** Day game passenger loading
- **Active:** During Giants day games
- **Display:** "Passenger Loading Zone on Giants Day Games"

#### 3. Giants Night (52 schedules)
- **Location:** 2nd St 600 block (near Oracle Park)
- **Time:** 8:00 PM - 12:00 AM
- **Purpose:** Night game passenger loading
- **Active:** During Giants night games
- **Display:** "Passenger Loading Zone on Giants Night Games"

#### 4. Performance (50 schedules)
- **Locations:** Castro St 400, Fillmore St 2200
- **Time:** 12:00 AM - 12:00 AM (all day when active)
- **Purpose:** Theater/venue performance passenger loading
- **Active:** During performances
- **Display:** "Passenger Loading Zone on Special Event Periods"

#### 5. Posted Events (19 schedules)
- **Locations:** 16th St 3100, Howard St 800, Stockton St 1600
- **Time:** 12:00 AM - 12:00 AM (all day when active)
- **Purpose:** General special events passenger loading
- **Active:** During posted events
- **Display:** "Passenger Loading Zone on Special Event Periods"

#### 6. Posted Services (19 schedules)
- **Location:** 23rd St 3200 block
- **Time:** 12:00 AM - 12:00 AM (all day when active)
- **Purpose:** Service-related activities
- **Active:** During posted services
- **Display:** "Passenger Loading Zone on Service Periods"

#### 7. Business Hours (2 schedules)
- **Locations:** California St 700, Eddy St 900
- **Time:** 12:00 AM - 12:00 AM (all day when active)
- **Purpose:** Business-related loading
- **Active:** During business hours
- **Display:** "Passenger Loading Zone on Business Hours"

---

## Common Characteristics

### ALL 371 Non-DOW ALTERNATE Schedules Share:

1. **Schedule Type:** `"Alternate"`
2. **Applied Color Rule:** `"White - Passenger loading zone"`
3. **Time Limit:** `"0 minutes"` (no parking allowed)
4. **Active Meter Status:** `"M - Active meter installed"`
5. **Cap Color:** Typically "Grey" or "Green" (physical meter cap)
6. **Severity When Active:** 3 (TOW + VIOLATION)
7. **Severity When Inactive:** 1 (Standard meter operation)

---

## Critical Implementation Rules

### Rule 1: Conditional Application

**The `applied_color_rule` ONLY applies when `days_applied` condition is met:**

```
When ALTERNATE Condition ACTIVE:
├─ Use ALTERNATE schedule
├─ Apply WHITE passenger loading restriction
├─ Severity: 3 (TOW + VIOLATION)
├─ Consequence: Vehicle towed if parked
└─ Display: "Passenger Loading Zone on [interpretation]"

When ALTERNATE Condition INACTIVE:
├─ Use base Operating Schedule
├─ Apply standard meter operation
├─ Severity: 1 (Standard metered parking)
├─ Consequence: Parking ticket if unpaid
└─ Display: Base schedule (e.g., "2hr limit M-F ($2.50/hr)")
```

### Rule 2: Two-Line Display Format

**For user display, show BOTH rules:**

```
Line 1: Passenger Loading Zone on [interpretation]
Line 2: All other days [duration] [day range] ($[rate]/hr)
```

**Examples:**

```
School Days:
Line 1: Passenger Loading Zone on School Days
Line 2: All other days 2hr limit M-F ($2.50/hr)

Giants Day Games:
Line 1: Passenger Loading Zone on Giants Day Games
Line 2: All other days 2hr limit M-Sa ($4.00/hr)

Special Event Periods:
Line 1: Passenger Loading Zone on Special Event Periods
Line 2: All other days 2hr limit M-Su ($3.00/hr)
```

### Rule 3: No Calendar Integration Required

**The system does NOT need to determine when events are occurring:**

- Display BOTH rules to users
- Users understand the conditions
- No real-time event calendar needed
- No external API dependencies

---

## Data Structure

### Complete Meter Record Example

```json
{
  "post_id": "223-33390",
  "street_and_block": "23RD ST 3300",
  "block_side": "Odd",
  "cap_color": "Grey",
  "active_meter_status": "M - Active meter installed",
  "location": {
    "type": "Point",
    "coordinates": [-122.xxx, 37.xxx]
  },
  "base_schedules": [
    {
      "schedule_type": "Alternate",
      "days_applied": "School Days",
      "from_time": "7:00 AM",
      "to_time": "4:00 PM",
      "applied_color_rule": "White - Passenger loading zone",
      "time_limit": "0 minutes",
      "cap_color": "Grey",
      "priority": "1"
    },
    {
      "schedule_type": "Operating Schedule",
      "days_applied": "Mo,Tu,We,Th,Fr",
      "from_time": "9:00 AM",
      "to_time": "6:00 PM",
      "time_limit": "120 minutes",
      "rate": "2.50",
      "cap_color": "Grey"
    }
  ],
  "special_event_meter": false
}
```

---

## Implementation Code

### Interpretation Mapping

```python
# Standardized interpretation overrides
ALTERNATE_INTERPRETATIONS = {
    'School Days': 'School Days',
    'Giants Day': 'Giants Day Games',
    'Giants Night': 'Giants Night Games',
    'Performance': 'Special Event Periods',
    'Posted Events': 'Special Event Periods',
    'Posted Services': 'Service Periods',
    'Business Hours': 'Business Hours'
}
```

### Display Format Generator

```python
def format_alternate_schedule_display(alternate_sched, operating_sched):
    """
    Generate two-line display for non-DOW ALTERNATE schedules.
    
    Args:
        alternate_sched: ALTERNATE schedule dict
        operating_sched: Base Operating Schedule dict
    
    Returns:
        dict with line1 and line2 display strings
    """
    days_applied = alternate_sched['days_applied']
    interpretation = ALTERNATE_INTERPRETATIONS.get(days_applied, days_applied)
    
    # Line 1: ALTERNATE condition
    line1 = f"Passenger Loading Zone on {interpretation}"
    
    # Line 2: Base operating schedule
    duration = parse_duration(operating_sched['time_limit'])
    days = format_days(operating_sched['days_applied'])
    rate = operating_sched.get('rate', 'Free')
    
    line2 = f"All other days {duration} {days} (${rate}/hr)"
    
    return {
        'line1': line1,
        'line2': line2,
        'severity_when_active': 3,
        'severity_when_inactive': 1
    }

def parse_duration(time_limit_str):
    """Parse time limit string to display format."""
    if not time_limit_str or '0 minute' in str(time_limit_str):
        return "No parking"
    
    import re
    match = re.search(r'(\d+)', str(time_limit_str))
    if match:
        minutes = int(match.group(1))
        if minutes < 60:
            return f"{minutes}min limit"
        else:
            hours = minutes / 60
            return f"{int(hours) if hours == int(hours) else hours}hr limit"
    return time_limit_str

def format_days(days_str):
    """Format days_applied string for display."""
    mapping = {
        'Mo,Tu,We,Th,Fr': 'M-F',
        'Mo,Tu,We,Th,Fr,Sa': 'M-Sa',
        'Mo,Tu,We,Th,Fr,Sa,Su': 'Daily',
        'Sa,Su': 'Sa-Su'
    }
    return mapping.get(days_str, days_str)
```

### Eligibility Check Logic

```python
def check_parking_eligibility_with_alternates(meter_schedules, datetime, duration_minutes):
    """
    Check parking eligibility considering ALTERNATE schedules.
    
    Note: This is for display purposes. The system shows all rules to users.
    Users determine if ALTERNATE condition applies to their situation.
    """
    # Find ALTERNATE schedule
    alternate = next((s for s in meter_schedules 
                     if s['schedule_type'] == 'Alternate'), None)
    
    # Find base Operating Schedule
    operating = next((s for s in meter_schedules 
                     if s['schedule_type'] == 'Operating Schedule'), None)
    
    if alternate and operating:
        # Display both rules
        display = format_alternate_schedule_display(alternate, operating)
        
        return {
            'has_alternate': True,
            'display_line1': display['line1'],
            'display_line2': display['line2'],
            'note': 'User must determine if ALTERNATE condition applies'
        }
    
    # Standard meter operation
    return check_standard_meter_eligibility(meter_schedules, datetime, duration_minutes)
```

---

## Benefits

### For Users
- ✅ Clear understanding of all applicable rules
- ✅ Know when special restrictions apply
- ✅ Can plan parking accordingly
- ✅ No confusion about conditions

### For System
- ✅ Simple implementation (no calendar integration)
- ✅ No external dependencies
- ✅ Complete information display
- ✅ Standardized interpretation overrides
- ✅ Proper severity classification

### For Maintenance
- ✅ Easy to update interpretations
- ✅ Clear documentation
- ✅ Testable logic
- ✅ Single source of truth

---

## Files Created/Updated

### Analysis Files
1. **[`list_all_non_dow_days_applied.py`](list_all_non_dow_days_applied.py)** - Analysis script
2. **[`non_dow_days_applied_patterns.json`](non_dow_days_applied_patterns.json)** - Complete data
3. **[`non_dow_days_applied_patterns.csv`](non_dow_days_applied_patterns.csv)** - Spreadsheet format
4. **[`generate_alternate_display_format.py`](generate_alternate_display_format.py)** - Display generator
5. **[`inspect_meter_schedule_fields.py`](inspect_meter_schedule_fields.py)** - Field inspection

### Documentation Files
1. **[`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)** - Updated with ALTERNATE section
2. **[`CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md`](CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md)** - Updated with patterns
3. **[`ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md`](ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md)** - Initial analysis
4. **[`ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md`](ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md)** - This document

---

## Next Steps

### Immediate
- [ ] Update `DATA_QUALITY_LOG.md` with findings
- [ ] Update `CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`
- [ ] Review `ingest_data_cnn_segments.py` for any needed updates
- [ ] Update `regulation_normalizer.py` with interpretation mapping

### Future
- [ ] Implement two-line display in frontend
- [ ] Add ALTERNATE schedule handling to eligibility logic
- [ ] Create user documentation for special conditions
- [ ] Monitor for new non-DOW patterns in future data updates

---

## Conclusion

The analysis of ALTERNATE schedules reveals a well-structured system for handling event-based and condition-based passenger loading zones. The key insight is that **no special calendar integration is needed** - the system simply displays both rules to users, who can determine if the special condition applies to their situation.

This approach provides:
- Complete information to users
- Simple implementation
- No external dependencies
- Clear, standardized display format

**Status:** ✅ Analysis Complete - Ready for Implementation

---

**Document Version:** 1.0  
**Last Updated:** December 31, 2024  
**Author:** Regulation Normalization Analysis  
**Related Documents:** See Files Created/Updated section above