# Meter Operating Schedules Investigation Summary

**Investigation Date:** December 30, 2025  
**Datasets Analyzed:** 6cqg-dxku, 8vzz-qzz9, itv4-r6g6  
**Status:** Complete

---

## Executive Summary

Investigation of the Meter Operating Schedules dataset (6cqg-dxku) revealed significant findings about meter coverage, data quality, and special event meter distribution. Key findings include 21.5% of active meters lacking operating schedules and 7.9% of all meters located in special event areas requiring dynamic pricing.

---

## Investigation Questions & Answers

### Q1: How many unique postIDs are in Meter Operating Schedules (6cqg-dxku)?

**Answer: 29,371 unique postIDs**

- Total schedule records: 72,365
- Average records per meter: 2.46
- Dataset contains baseline/permanent operating schedules

### Q2: Do all postIDs map to active On Street meters (8vzz-qzz9)?

**Answer: NO - 82.3% map to active meters**

- 24,173 postIDs (82.3%) exist in both datasets
- 5,198 postIDs (17.7%) in schedules do NOT map to active meters
  - Likely historical/inactive meters that have been removed
- 6,624 active meters (21.5%) have NO operating schedule

### Q3: Can meters without schedules be mapped to CNN?

**Answer: YES - 99.9% can be mapped**

- 6,620 meters (99.9%) have valid `street_seg_ctrln_id` (CNN)
- Only 4 meters lack CNN (all on Stanyan St - known data quality issue)
- All CNNs verified to exist in Active Streets dataset

### Q4: Do meters without schedules fall within Special Event areas (itv4-r6g6)?

**Answer: NO - Only 13.4%**

- 889 meters (13.4%) are in Special Event/Evening Meter Areas
- 5,735 meters (86.6%) are regular street meters distributed citywide
- Indicates systematic data gap, not just special event meters

### Q5: How many meters in the ENTIRE dataset fall within Special Event areas?

**Answer: 2,420 meters (7.9% of all active meters)**

Out of 30,797 total active meters:
- **Ballpark area (Oracle Park):** 1,380 meters (57.0% of special area meters)
- **Combined area:** 881 meters (36.4% of special area meters)
- **Arena area (Chase Center):** 159 meters (6.6% of special area meters)

---

## Data Quality Findings

### Issue: Missing Meter Operating Schedules

**Severity:** HIGH  
**Impact:** 6,624 active meters (21.5%) lack operating schedule information

**Breakdown:**
- Meters WITH schedules: 24,173 (78.5%)
- Meters WITHOUT schedules: 6,624 (21.5%)
- Geographic distribution: Citywide (not concentrated in special areas)

**User Impact:**
- Cannot display meter rates, time limits, or operating hours
- Users must physically check meter for information
- Reduces app utility for parking planning

**Recommended Actions:**
1. ✅ Implement user notification for missing schedules
2. ⏭️ Request SFMTA data update for affected meters
3. ⏭️ Investigate orphaned schedules (5,198 postIDs not in active meters)
4. ⏭️ Implement data quality monitoring

---

## Special Event Meter Architecture

### Special Event Policy

**Operating Hours (when events are in effect):**
- Monday-Saturday: 9am-10pm
- Special Event Sundays: 12pm-10pm

**Event Rate:** $12/hour

**Event Rate Hours (vary by event start time):**
| Event Start Time | Rate Hours in Effect |
|-----------------|---------------------|
| Noon - 2:59pm | Noon - 6pm |
| 3pm - 6pm | 3pm - 10pm |
| After 6pm | 6pm - 10pm |

### Implementation in CNN Master File

**Special Event Meter Flag:**
- 2,420 meters flagged based on geospatial boundaries (itv4-r6g6)
- Flag indicates meter subject to special event pricing
- Three area types: Ballpark, Arena, Combined

**Data Structure:**
```python
{
    'post_id': '202-07150',
    'special_event_meter': True,
    'special_event_area': 'Ballpark',  # or 'Arena', 'Combined'
    'base_schedules': [...],  # From 6cqg-dxku
    'special_event_policy': {
        'operating_hours': {
            'mon_sat': '9am-10pm',
            'special_event_sunday': '12pm-10pm'
        },
        'event_rate': '$12/hour',
        'event_schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule'
    }
}
```

---

## CNN Master File Integration

### Meter Data Inclusion

**Static Data (included in CNN Master):**
1. **Parking Meters (8vzz-qzz9):**
   - Physical meter attributes: post_id, cap_color, location, CNN
   - 30,797 active On Street meters

2. **Meter Operating Schedules (6cqg-dxku):**
   - Baseline operating schedules (permanent/stable)
   - 29,371 postIDs with schedules
   - Fields: schedule_type, days_applied, from_time, to_time, time_limit

3. **Special Event Meter Flags:**
   - Derived from geospatial analysis (itv4-r6g6)
   - 2,420 meters flagged
   - Area type classification (Ballpark/Arena/Combined)

**Dynamic Data (separate collection):**
- **Meter Policies (qq7v-hds4):**
  - Temporal policy modifications
  - Updated every 3 days via cron job
  - Filtered for active policies (startdate <= TODAY <= enddate)
  - Currently all future-dated (start: 2026-01-12)

### Schedule Types and Priority Logic

**CRITICAL: Schedule Priority in Meter Operating Schedules (6cqg-dxku)**

The Meter Operating Schedules dataset contains multiple schedule types with a strict priority hierarchy:

**Schedule Types:**
- **TOW**: Tow-away periods - NO PARKING ALLOWED
- **ALTERNATE**: Alternate side parking or special restrictions
- **OP (Paid Operation)**: Standard metered parking with time limits, rates, and vehicle restrictions
- **FREE**: No payment, no restrictions, no cap color
- **PRE (Prepay)**: Prepay allowed (includes free time before enforcement)

**Priority Hierarchy:**
```
TOW > ALTERNATE > OP/FREE/PRE
```

**Priority Rules:**

1. **TOW periods ALWAYS trump all other schedules**
   - When TOW is in effect, parking is PROHIBITED regardless of other schedules
   - Example: If OP schedule says parking allowed 9am-6pm, but TOW is 2pm-4pm → NO PARKING 2pm-4pm
   - TOW overrides everything including special event rates

2. **ALTERNATE schedules trump base operating schedules (OP/FREE/PRE)**
   - Alternate side parking or special restrictions override normal operations
   - Example: If OP schedule allows parking, but ALTERNATE restricts it → ALTERNATE wins
   - ALTERNATE does NOT override TOW

3. **Base schedules (OP/FREE/PRE) apply when no TOW or ALTERNATE in effect**
   - Normal metered operation during these periods
   - Multiple OP schedules can exist for different times/rates
   - Lowest priority in the hierarchy

**Implementation Logic:**
```python
def get_effective_schedule(post_id, datetime):
    """
    Determine effective schedule for a meter at a given time.
    CRITICAL: TOW > ALTERNATE > OP/FREE/PRE
    """
    schedules = get_all_schedules(post_id, datetime)
    
    # Priority 1: Check for TOW first - HIGHEST PRIORITY
    tow_schedule = [s for s in schedules if s.schedule_type == 'TOW']
    if tow_schedule and is_time_in_schedule(datetime, tow_schedule[0]):
        return {
            'type': 'TOW',
            'status': 'NO_PARKING',
            'message': 'Tow-away zone - No parking allowed',
            'schedule': tow_schedule[0]
        }
    
    # Priority 2: Check for ALTERNATE - SECOND PRIORITY
    alt_schedule = [s for s in schedules if s.schedule_type == 'ALTERNATE']
    if alt_schedule and is_time_in_schedule(datetime, alt_schedule[0]):
        return {
            'type': 'ALTERNATE',
            'status': 'RESTRICTED',
            'message': 'Special restrictions apply',
            'schedule': alt_schedule[0]
        }
    
    # Priority 3: Return base schedule (OP/FREE/PRE) - LOWEST PRIORITY
    base_schedules = [s for s in schedules
                     if s.schedule_type in ['OP', 'FREE', 'PRE']]
    return get_applicable_base_schedule(datetime, base_schedules)
```

**User Display Logic:**
```python
def display_meter_status(post_id, datetime):
    """
    Display meter status respecting schedule priority.
    """
    effective = get_effective_schedule(post_id, datetime)
    
    if effective['type'] == 'TOW':
        return "🚫 NO PARKING - Tow-Away Zone"
    elif effective['type'] == 'ALTERNATE':
        return f"⚠️ {effective['message']}"
    elif effective['type'] == 'OP':
        return f"💵 Meter Rules Apply: ${effective['schedule'].rate}/hour - {effective['schedule'].time_limit} limit"
    elif effective['type'] == 'PRE':
        return f"💳 Meter Rules Apply: Prepay Available - {effective['schedule'].time_limit} limit"
    elif effective['type'] == 'FREE':
        return "✅ Free Parking - No Meter Rules Apply"
```

**Documentation Requirements:**
- All meter schedule queries MUST respect this priority hierarchy
- TOW and ALTERNATE schedules MUST be checked before displaying base schedules
- User interface MUST clearly indicate when TOW or ALTERNATE restrictions are in effect
- API responses MUST include schedule type and priority level

### Data Flow

```
CNN Master File (Static - Weekly/Monthly Refresh)
├── Parking Meters (8vzz-qzz9)
├── Meter Operating Schedules (6cqg-dxku)
└── Special Event Flags (derived from itv4-r6g6)
        ↓
MongoDB Collection: meter_policies (Dynamic - Every 3 days)
├── Meter Policies (qq7v-hds4)
└── Filtered: startdate <= TODAY <= enddate
        ↓
Runtime Query (Conditional)
├── Always: Query CNN Master
├── If meters present: Query meter_policies
└── Merge active policies with base schedules
```

---

## User Notifications

### For Meters Without Schedules (6,624 meters)

```
⚠️ METER SCHEDULE UNAVAILABLE

Operating schedule information is not available in our database 
for this meter location.

Please check the physical meter for:
- Parking rates
- Time limits
- Days and hours of operation
- Payment methods accepted

Meter ID: [POST_ID]
Location: [STREET_NUM] [STREET_NAME]
```

### For Special Event Meters (2,420 meters)

```
ℹ️ SPECIAL EVENT METER

When special events are in effect, this meter operates:
• Monday-Saturday: 9am-10pm at $12/hour
• Special Event Sundays: 12pm-10pm at $12/hour

Check current special event schedule:
https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule

Meter ID: [POST_ID]
Area: [Ballpark/Arena/Combined]
```

---

## Investigation Scripts

### Analysis Scripts Created

1. **[`investigate_meter_schedules_comprehensive.py`](investigate_meter_schedules_comprehensive.py)**
   - Main analysis of meter operating schedules
   - Compares schedules to active meters
   - Identifies coverage gaps

2. **[`check_meters_without_schedules_cnn.py`](check_meters_without_schedules_cnn.py)**
   - Verifies CNN mapping for meters without schedules
   - Validates CNNs exist in Active Streets dataset
   - Result: 99.9% have valid CNN

3. **[`check_meters_in_special_event_areas.py`](check_meters_in_special_event_areas.py)**
   - Geospatial analysis of meters without schedules
   - Checks if meters fall within itv4-r6g6 boundaries
   - Result: Only 13.4% in special areas

4. **[`check_all_meters_in_special_areas.py`](check_all_meters_in_special_areas.py)**
   - Analyzes ALL active meters against special event areas
   - Identifies 2,420 meters requiring special event flag
   - Provides breakdown by area type

---

## Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Unique postIDs in Schedules** | 29,371 | ℹ️ Baseline |
| **Active On Street Meters** | 30,797 | ℹ️ Baseline |
| **Schedule Coverage** | 78.5% | ⚠️ Needs Improvement |
| **CNN Mapping (no schedule)** | 99.9% | ✅ Excellent |
| **Special Event Meters** | 2,420 (7.9%) | ℹ️ Flagged |
| **Meters Without Schedules** | 6,624 (21.5%) | ⚠️ Data Gap |

---

## Recommendations

### Immediate (Week 1)
1. ✅ Document findings (DONE)
2. ✅ Implement special event meter flagging in CNN Master
3. ⏭️ Add user notifications for missing schedules
4. ⏭️ Display special event policy information

### Short-term (1-3 months)
1. ⏭️ Request SFMTA data update for 6,624 meters without schedules
2. ⏭️ Investigate 5,198 orphaned schedule postIDs
3. ⏭️ Implement data quality monitoring dashboard
4. ⏭️ Track schedule coverage over time

### Long-term (3-6 months)
1. ⏭️ Establish data refresh cadence with SFMTA
2. ⏭️ Create automated alerts for coverage drops
3. ⏭️ Build data quality dashboard
4. ⏭️ Implement user feedback mechanism for data corrections

---

## Related Documentation

- [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Issue #4: Missing Meter Operating Schedules
- [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) - Issue #007: Meter Schedule Coverage Gap
- [`CNN_MASTER_FILE_DESIGN.md`](CNN_MASTER_FILE_DESIGN.md) - Phase 2: Meter Integration
- [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Layer 5A: Meter Datasets
- [`CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`](../CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md) - Section 15: Meter Datasets Integration

---

## Conclusion

The investigation revealed a significant data quality issue affecting 21.5% of active meters, but also confirmed that 99.9% of these meters can still be mapped to the street network via CNN. The identification of 2,420 special event meters enables proper handling of dynamic pricing and extended operating hours for Oracle Park and Chase Center events.

**Key Takeaway:** While meter operating schedule coverage has gaps, the system can gracefully handle missing data through user notifications and maintain full spatial coverage through CNN mapping.

---

**Document Version:** 1.0  
**Last Updated:** December 30, 2025  
**Investigation Lead:** System Analysis  
**Status:** Complete - Ready for Implementation