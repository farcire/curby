# Regulation Normalization - Complete Implementation Summary

**Date:** December 31, 2025
**Status:** ✅ COMPLETE IMPLEMENTATION
**Module:** [`regulation_normalizer.py`](regulation_normalizer.py)

---

## Overview

This document summarizes the complete regulation normalization system including:
1. Special Event Zone Display Logic
2. Non-DOW ALTERNATE Schedules
3. Complete 6-Color Cap Color Legend
4. Meter Schedule Priority Hierarchy

---

## PART 1: Special Event Zone Meters (Geospatial)

### Definition
Meters located within Oracle Park ("Ballpark") or Chase Center ("Arena") boundaries, identified through spatial joins during ingestion.

**Count:** ~2,400 meters (7.9% of total)  
**Data Source:** Special Event Areas dataset (itv4-r6g6)

### Display Rules

**Line 1 Format (Zone-Specific):**
- **Ballpark only**: "Oracle Park Schedule and Rates may apply. See schedule for details."
- **Arena only**: "Chase Center Schedule and Rates may apply. See schedule for details."
- **Both zones (overlap)**: "Special Event Schedule and Rates may apply. See schedule for details."
- Word "schedule" is hyperlinked to: https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule

**Line 2 Format:**
- Single schedule (all 7 days): "All Other Days [duration] [days] [time] ($[rate]/hr)"
- Multiple schedules: "All Other Weekdays [duration] [days] [time] ($[rate]/hr)"

**Line 3 Format (if multiple schedules):**
- "All Other Weekends [duration] [days] [time] ($[rate]/hr)"

### Implementation

```python
# In regulation_normalizer.py - Part 10
from regulation_normalizer import format_special_event_zone_display

# Single schedule example
result = format_special_event_zone_display(
    in_ballpark_zone=True,
    in_arena_zone=False,
    base_schedules=[{
        'duration_minutes': 120,
        'days': [0,1,2,3,4,5,6],
        'from_time': '9:00 AM',
        'to_time': '6:00 PM',
        'rate': '4.00'
    }]
)

# Returns:
# {
#     'line1': 'Oracle Park Schedule and Rates may apply. See schedule for details.',
#     'line2': 'All Other Days 2hr limit Daily 9am-6pm ($4.00/hr)',
#     'line3': '',
#     'schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule',
#     'has_special_event': True
# }

# Multiple schedules example
result = format_special_event_zone_display(
    in_ballpark_zone=False,
    in_arena_zone=True,
    base_schedules=[
        {
            'duration_minutes': 120,
            'days': [0,1,2,3,4],
            'from_time': '9:00 AM',
            'to_time': '6:00 PM',
            'rate': '2.50'
        },
        {
            'duration_minutes': 240,
            'days': [5,6],
            'from_time': '12:00 PM',
            'to_time': '10:00 PM',
            'rate': '3.00'
        }
    ]
)

# Returns:
# {
#     'line1': 'Chase Center Schedule and Rates may apply. See schedule for details.',
#     'line2': 'All Other Weekdays 2hr limit M-F 9am-6pm ($2.50/hr)',
#     'line3': 'All Other Weekends 4hr limit Sa-Su 12pm-10pm ($3.00/hr)',
#     'schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule',
#     'has_special_event': True
# }
```

---

## PART 2: Non-DOW ALTERNATE Schedules (Condition-Based)

### Definition
Meters with ALTERNATE schedule types using non-day-of-week `days_applied` values.

**Count:** 371 schedules (0.51% of total)  
**Data Source:** Meter Operating Schedules dataset (6cqg-dxku)

### All 7 Patterns

| Pattern | Count | % | Interpretation | Display |
|---------|-------|---|----------------|---------|
| School Days | 177 | 0.24% | School Days | "Passenger Loading Zone on School Days" |
| Giants Day | 52 | 0.07% | Giants Day Games | "Passenger Loading Zone on Giants Day Games" |
| Giants Night | 52 | 0.07% | Giants Night Games | "Passenger Loading Zone on Giants Night Games" |
| Performance | 50 | 0.07% | Special Event Periods | "Passenger Loading Zone on Special Event Periods" |
| Posted Events | 19 | 0.03% | Special Event Periods | "Passenger Loading Zone on Special Event Periods" |
| Posted Services | 19 | 0.03% | Service Periods | "Passenger Loading Zone on Service Periods" |
| Business Hours | 2 | 0.00% | Business Hours | "Passenger Loading Zone on Business Hours" |

### Common Characteristics

ALL 371 non-DOW ALTERNATE schedules:
- `schedule_type: "Alternate"`
- `applied_color_rule: "White - Passenger loading zone"`
- `time_limit: "0 minutes"` (no parking when active)
- **Absolute prohibition** (TOW + VIOLATION) when condition active
- **Standard metered parking availability** when condition inactive

### Display Rules

**Line 1 Format:**
- "Passenger Loading Zone on [interpretation]"

**Line 2 Format:**
- "All other days [duration] [days] ($[rate]/hr)"

### Key Implementation Rule: Conditional Application

The `applied_color_rule` ONLY applies when the `days_applied` condition is met:

**When ALTERNATE Condition ACTIVE** (e.g., during School Days):
- Use ALTERNATE schedule
- Apply WHITE passenger loading restriction
- **Restriction**: Absolute prohibition (TOW + VIOLATION)
- Display: "Passenger Loading Zone on [interpretation]"

**When ALTERNATE Condition INACTIVE** (e.g., not School Days):
- Use base Operating Schedule
- Apply standard meter operation
- **Availability**: Standard metered parking
- Display: Base schedule (e.g., "2hr limit M-F ($2.50/hr)")

---

## PART 3: Complete Cap Color Legend

### Official 6-Color System (Dec 31, 2024)

| Cap Color | Vehicle Type | Curby User Eligible | Display Text |
|-----------|--------------|---------------------|--------------|
| **BLACK** | Motorcycle only | ❌ NO | "Motorcycle only" |
| **BROWN** | Tour Bus only | ❌ NO | "Tour Bus only" |
| **GREY** | General parking | ✅ YES | "General parking" |
| **GREEN** | General parking | ✅ YES | "General parking" |
| **PURPLE** | Boat Trailer only | ❌ NO | "Boat Trailer only" |
| **RED** | Commercial Vehicles 6+ wheels | ❌ NO | "Commercial Vehicles 6+ wheels" |
| **YELLOW** | Commercial Vehicle | ❌ NO | "Commercial Vehicle" |

### For Curby Users (Standard Cars)

**ELIGIBLE:** GREY, GREEN only  
**INELIGIBLE:** BLACK, BROWN, PURPLE, RED, YELLOW

**Default Assumption:** Curby users are in standard cars

### Blockface-Level Aggregation (Majority Rule)

Cap colors are aggregated at the CNN+SIDE (blockface) level:

- **All meters eligible** → Block ELIGIBLE for Curby users
- **Majority eligible** → Block ELIGIBLE for Curby users
- **Majority ineligible** → Block INELIGIBLE for Curby users
- **All meters ineligible** → Block INELIGIBLE for Curby users

### Implementation

```python
# In regulation_normalizer.py - Part 8
from regulation_normalizer import normalize_cap_color, aggregate_blockface_cap_colors

# Single meter
result = normalize_cap_color('GREY')
# Returns: {'canonical': {'restriction': 'GENERAL', ...}, 'display': {'user_eligible': True, ...}}

# Blockface aggregation
meters = [
    {'cap_color': 'GREY'},
    {'cap_color': 'GREEN'},
    {'cap_color': 'YELLOW'}
]
result = aggregate_blockface_cap_colors(meters)
# Returns: {'eligible_for_curby_user': True, 'majority_rule': 'MAJORITY_ELIGIBLE', ...}
```

---

## PART 4: Meter Schedule Priority Hierarchy

### Priority Order (Highest to Lowest)

```
TOW > ALTERNATE > OP > PRE+FREE
```

**Note:** PRE and FREE have equal priority (lowest). PRE is treated as FREE for display purposes.

### Schedule Types

1. **TOW** (Highest Priority)
   - No parking allowed at meter during this time
   - Meter-specific schedule type
   - Overridden by street sweeping (absolute prohibition)

2. **ALTERNATE**
   - Different meter rules on certain days
   - Examples: Higher rates during events, different time limits on weekends
   - NOT alternate side parking - means alternate rules/rates

3. **OP** (Paid Operation)
   - Standard metered parking with rates and time limits
   - Cap color restrictions apply during OP hours

4. **PRE** (Prepay)
   - Users can prepay before enforcement begins
   - Treated as FREE for display purposes
   - No cap color restrictions

5. **FREE** (Lowest Priority)
   - No payment required
   - No time restrictions
   - No cap color restrictions

### Implementation

```python
# In regulation_normalizer.py - Part 9
from regulation_normalizer import prioritize_meter_schedules, get_effective_meter_schedule

# Sort schedules by priority
schedules = [
    {'schedule_type': 'OP', ...},
    {'schedule_type': 'TOW', ...},
    {'schedule_type': 'FREE', ...}
]
prioritized = prioritize_meter_schedules(schedules)
# Returns: [TOW, OP, FREE] (sorted by priority)

# Get effective schedule at specific time
meter = {'base_schedules': schedules}
effective = get_effective_meter_schedule(meter, check_day=0, check_time_min=540)
# Returns: The highest priority active schedule
```

---

## PART 5: Street Cleaning Integration (yhqp-riqs)

### Definition
Street cleaning schedules from the Street Cleaning Schedules dataset, representing **absolute prohibition** (Severity 3 - Most Severe) that overrides all parking availability types.

**Count:** 37,878 records covering 12,253 CNNs
**Data Source:** Street Cleaning Schedules dataset (yhqp-riqs)
**Status:** ✅ Analysis Complete, Ready for Integration

### Dataset Structure

**Unique Identifier:** CNN + corridor_side (e.g., "6113000_L", "6113000_R")

**Key Fields:**
- `cnn`: Centerline Network ID
- `corridor_side`: L (Left) or R (Right)
- `fullname`: Day name or "HOLIDAY"
- `weekday`: Day abbreviation
- `fromhour`, `tohour`: Time range (0-23)
- `week1-week5`: Week-of-month active flags (1/0)
- `holidays`: Clean on holidays flag (1/0)

### Week-of-Month Scheduling

**100% of records** use week-of-month scheduling:
- All weeks (1st-5th): 62.8%
- 2nd & 4th only: 18.4%
- 1st & 3rd only: 11.6%
- 1st, 3rd, 5th: 5.9%

**Display Format:** Use ordinal numbers
- "2nd & 4th Thu" (not "Week 2 & 4 Thu")
- "1st, 3rd, 5th Mon"
- "Every Thu" (when all 5 weeks active)

### Holiday Logic (Simplified - Verified Dec 31, 2024)

**Critical Understanding:** The HOLIDAY entry is only special when it **CONTRADICTS** a day's holidays=1 setting.

**Three Cases:**

1. **Override Case** (172 CNN+sides, 1.40%):
   - Day has holidays=1 (cleaning on holidays)
   - HOLIDAY entry has holidays=0 (no cleaning on holidays)
   - **Result**: HOLIDAY overrides → Show "except holidays"

2. **Consistent Case** (rest with HOLIDAY entry):
   - HOLIDAY holidays value matches all day holidays values
   - **Result**: Use that consistent value (0 or 1)

3. **No HOLIDAY Entry** (majority, 98.6%):
   - **Result**: Use day's holidays field directly

**SF Holidays** (No cleaning when holidays=0):
- January 1 (New Year's Day)
- December 25 (Christmas Day)
- 4th Thursday of November (Thanksgiving)

### Display Format

**Template:**
```
Street Cleaning {days} {time_range} {holiday_clause}
```

**Examples:**
```
Street Cleaning 2nd & 4th Thu 8am-10am except holidays
Street Cleaning Every Mon 6am-8am except holidays
Street Cleaning Tu, Th, Su 6am-8am except holidays
```

### Data Quality Issue: Asymmetric Coverage

**Issue:** 15.8% of CNNs (1,933 out of 12,253) have cleaning on only ONE side
- **Impact:** Users won't see restrictions for missing side
- **Solution:** Display only the side we have data for
- **Verification List:** `street_cleaning_manual_verification.csv`
- **Documentation:** Issue #1 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

### Implementation

```python
def should_skip_holidays(cnn_side_records):
    """
    The HOLIDAY entry is only special when it CONTRADICTS a day's holidays=1.
    """
    # Check for override case: HOLIDAY=0 contradicting days=1
    has_override = any(
        r.get("fullname") == "HOLIDAY" and str(r.get("holidays")) == "0"
        for r in cnn_side_records
    )
    has_days_with_1 = any(
        r.get("fullname") != "HOLIDAY" and str(r.get("holidays")) == "1"
        for r in cnn_side_records
    )
    
    if has_override and has_days_with_1:
        return True  # Override case
    
    # Otherwise use day's holidays field (consistent)
    regular_days = [r for r in cnn_side_records if r.get("fullname") != "HOLIDAY"]
    if regular_days:
        return str(regular_days[0].get("holidays")) == "0"
    
    return True
```

### References

- **Integration Guide:** [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)
- **Analysis Scripts:**
  - [`analyze_street_cleaning_dataset.py`](analyze_street_cleaning_dataset.py)
  - [`analyze_week_fields_correct.py`](analyze_week_fields_correct.py)
  - [`verify_holiday_consistency.py`](verify_holiday_consistency.py)
- **Data Quality:** Issue #013 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

---

## Integration Points

### In regulation_normalizer.py

**Part 8:** Cap Color Normalization
- `CapColorNormalizer` class
- `normalize_cap_color()` function
- `aggregate_blockface_cap_colors()` function

**Part 9:** Meter Schedule Priority
- `MeterScheduleSelector` class
- `prioritize_meter_schedules()` function
- `get_effective_meter_schedule()` function
- `aggregate_blockface_tow_schedules()` function

**Part 10:** Special Event Zone Display
- `SpecialEventZoneFormatter` class
- `format_special_event_zone_display()` function

### In ingest_data_cnn_segments.py

**STEP 5.6:** Meter Integration
- Check special event zones (geospatial)
- Check for non-DOW ALTERNATE schedules
- Apply cap color normalization
- Apply schedule priority hierarchy

---

## Key Differences: Special Event Zones vs Non-DOW ALTERNATE

| Aspect | Special Event Zones | Non-DOW ALTERNATE |
|--------|-------------------|-------------------|
| **Identification** | Geospatial (in zone boundary) | Schedule-based (days_applied field) |
| **Line 1 Text** | "[Zone] Schedule and Rates may apply. See schedule for details." | "Passenger Loading Zone on [condition]" |
| **Line 1 Includes URL** | Yes (word "schedule" hyperlinked) | No |
| **Line 2 Prefix** | "All Other Days" (single) OR "All Other Weekdays" (multiple) | "All other days" |
| **Line 3** | "All Other Weekends" (if multiple schedules) | N/A |
| **When Active** | During events (user checks schedule) | During condition (School Days, etc.) |
| **Restriction When Active** | Varies (event-dependent) | Absolute prohibition (TOW + VIOLATION) |
| **Count** | ~2,400 meters (7.9%) | 371 schedules (0.51%) |
| **Data Source** | Special Event Areas (itv4-r6g6) | Meter Operating Schedules (6cqg-dxku) |

---

## Benefits

### For Users
- ✅ Clear understanding of all applicable rules
- ✅ Zone-specific messaging for special events
- ✅ Know when special restrictions apply
- ✅ Understand vehicle eligibility (cap colors)
- ✅ Can plan parking accordingly

### For System
- ✅ Simple implementation (no calendar integration for non-DOW)
- ✅ No external dependencies
- ✅ Complete information display
- ✅ Standardized interpretation overrides
- ✅ Proper restriction classification (absolute prohibition vs parking availability)
- ✅ Single source of truth in regulation_normalizer.py

### For Maintenance
- ✅ Easy to update interpretations
- ✅ Clear documentation
- ✅ Testable logic
- ✅ Centralized normalization

---

## Files Updated

### Core Implementation
1. ✅ [`regulation_normalizer.py`](regulation_normalizer.py) - Complete implementation
   - Part 8: Cap Color Normalization (6 colors)
   - Part 9: Meter Schedule Priority
   - Part 10: Special Event Zone Display

### Analysis & Data
2. ✅ [`list_all_non_dow_days_applied.py`](list_all_non_dow_days_applied.py) - Analysis script
3. ✅ [`non_dow_days_applied_patterns.json`](non_dow_days_applied_patterns.json) - Complete data
4. ✅ [`non_dow_days_applied_patterns.csv`](non_dow_days_applied_patterns.csv) - Spreadsheet format
5. ✅ [`generate_alternate_display_format.py`](generate_alternate_display_format.py) - Display generator

### Documentation
6. ✅ [`ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md`](ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md) - Complete analysis
7. ✅ [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md) - This document
8. ✅ [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Updated with meter rates
9. ✅ [`CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md`](CNN_MASTER_FULL_METER_INTEGRATION_GUIDE.md) - Updated with meter rates
10. ✅ [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) - Added Issue #012 (meter rates)
11. ✅ [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Added Issue #10 (meter rates)
12. ✅ [`CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`](../CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md) - Updated with meter rates

### Meter Rate Application (December 31, 2024)
13. ✅ [`apply_meter_rates_to_cnn_master.py`](apply_meter_rates_to_cnn_master.py) - Rate application script
14. ✅ [`METER_RATE_APPLICATION_SUMMARY.md`](METER_RATE_APPLICATION_SUMMARY.md) - Complete documentation

---

## Testing Checklist

- [ ] Special event zone meters display correct zone-specific message
- [ ] Overlap zone meters show generic "Special Event" message
- [ ] Non-DOW ALTERNATE meters show "Passenger Loading Zone" message
- [ ] All displays include proper Line 2 with base schedule
- [ ] SFMTA URL is correctly formatted and clickable
- [ ] Duration and rate formatting is consistent
- [ ] Days display uses proper abbreviations
- [ ] Cap color eligibility correctly filters for Curby users (GREY/GREEN only)
- [ ] Blockface aggregation uses majority rule correctly
- [ ] Schedule priority hierarchy is respected (TOW > ALTERNATE > OP > PRE+FREE)

---

## PART 6: Fallback Matching for Unmatched Regulations

### Definition
Fallback matching strategy for parking regulations that failed standard geospatial matching, using synthetic boundaries generated from district, neighborhood, and RPP area data.

**Count:** 7 regulations (0.03% of dataset)
**Status:** ✅ Strategy Defined, Implementation In Progress
**Date:** January 3, 2026

### Two Types of Unmatched Regulations

**Type 1: Geometry + District + Neighborhood (3 regulations)**
- **Regulation IDs**: 4973, 64, 2191
- **Pattern**: Have geometry, supervisor_district, and analysis_neighborhood fields
- **Strategy**: Match to segments nearby geometry in same district+neighborhood
- **Skip Condition**: Skip if segment already has non-meter parking regulations (meters/cleaning OK)

**Type 2: RPP Areas Only (4 regulations)**
- **Regulation IDs**: 1551, 2303, 2353, 17287
- **Pattern**: No geometry, only RPP area fields (rpparea1, rpparea2, rpparea3)
- **Strategy**: Match using synthetic RPP boundaries
- **Matching Logic**:
  - Try RPP + district + neighborhood first
  - Fallback to RPP only if district/neighborhood empty
- **Skip Condition**: Skip if segment has RPP rules OR non-meter parking regulations

### Synthetic Boundaries Generated

**RPP Area Boundaries:**
- Generated 33 RPP area boundaries from matched regulations
- Stored in `rpp_area_boundaries` MongoDB collection
- 100% geometry coverage, 15.7% overlap rate (expected behavior)
- Created geospatial 2dsphere indexes for efficient queries
- Script: [`generate_rpp_area_boundaries.py`](generate_rpp_area_boundaries.py)

**District Boundaries:**
- Analyzed 34,324 street segments for district data
- Found 12 unique districts (1-11 plus 280 "nan" segments)
- Ready for boundary generation (not yet implemented)
- Script: [`investigate_district_boundaries.py`](investigate_district_boundaries.py)

### Database Optimization

**Indexes Created:**
- Compound index: `supervisor_district_1_analysis_neighborhood_1`
- Individual indexes on `supervisor_district` and `analysis_neighborhood`
- Optimized for fallback matching queries
- Script: [`create_fallback_matching_indexes.py`](create_fallback_matching_indexes.py)

### Implementation Plan

**Centralized Fallback Matching Script:**
1. Query all 7 unmatched regulations
2. Apply Type 1 logic for regulations with geometry
3. Apply Type 2 logic for regulations with RPP areas only
4. Respect skip conditions to avoid conflicts
5. Update street_segments collection with matched regulations
6. Log results for documentation

### References

- **Fallback Strategy:** [`FALLBACK_MATCHING_STRATEGY.md`](FALLBACK_MATCHING_STRATEGY.md)
- **Data Quality Log:** Issue #015 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)
- **Data Quality Issues:** Issue #12 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

---

## PART 7: Data Quality - Empty Regulation Fields

### Definition
Five parking regulation records with empty `regulation` fields, making them unusable for display or enforcement.

**Count:** 5 regulations (0.02% of dataset)
**Status:** 🚨 Data Error - Excluded from Ingestion
**Date:** January 3, 2026

### Affected Regulations

```
Regulation IDs: 3295, 3948, 3561, 3949, 3947
Pattern: All have empty regulation field
Root Cause: Data quality issue in SFMTA source dataset
```

### Impact

**Data Completeness:** Minimal (0.02% of regulations)
**User Experience:** None (cannot display empty regulations anyway)
**System Functionality:** None (filtered out during ingestion)

### Solution

**✅ Exclusion During Ingestion:**
1. Filter out regulations with empty `regulation` field
2. Log excluded regulation IDs for SFMTA reporting
3. Document in data quality issues
4. No user impact since regulations are unusable

### References

- **Data Quality Log:** Issue #014 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)
- **Data Quality Issues:** Issue #11 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

---

## Conclusion

The regulation normalization system now provides:
1. **Complete cap color support** - All 6 colors with proper Curby user eligibility
2. **Special event zone display** - Zone-specific messaging with SFMTA links
3. **Non-DOW ALTERNATE schedules** - 7 patterns with proper interpretation
4. **Schedule priority hierarchy** - TOW > ALTERNATE > OP > PRE+FREE
5. **Centralized normalization** - Single source of truth in regulation_normalizer.py

**Status:** ✅ Core Implementation Complete - Documentation Updates In Progress

---

**Document Version:** 1.0
**Last Updated:** January 1, 2026
**Author:** Regulation Normalization Team
**Related:** regulation_normalizer.py, CNN_MASTER_REFERENCE_ARCHITECTURE.md