# Data Quality Log

**Purpose:** Track data quality issues discovered during ingestion for internal documentation, reconciliation, triage, and potential LLM training data.

**Manual Override System:** Issues that have been verified and require correction are documented in [`manual_data_overrides.json`](manual_data_overrides.json) and automatically applied during ingestion at STEP 5.4 via [`apply_manual_overrides.py`](apply_manual_overrides.py).

**Last Updated:** January 1, 2026

---

## Log Entry Format

Each entry should include:
- **Date Discovered**
- **Dataset(s) Affected**
- **Issue Type**
- **Severity** (Critical/High/Medium/Low)
- **Count/Percentage**
- **Sample Records**
- **Impact**
- **Workaround/Solution**
- **Status** (Open/Resolved/Monitoring)

---

## Active Issues

### Issue #017: Meter Matching Ignores Odd/Even Parity - ✅ RESOLVED

**Date Discovered:** January 7, 2026
**Date Resolved:** January 7, 2026
**Dataset:** Meter Policies (On-Street Parking Meters)
**Issue Type:** Data Ingestion Logic Error
**Severity:** Critical - Causes duplicate/incorrect meter assignments

**Description:**
The CNN fallback matching logic in `ingest_data_cnn_segments.py` (STEP 4) fails to validate odd/even address parity when matching meters to street segment sides. This causes meters to be incorrectly assigned to BOTH L (odd) and R (even) sides when they should only appear on one side.

**Universal Street Numbering Convention:**
- **L (Left) side** = ODD addresses (1, 3, 5, 7, ...)
- **R (Right) side** = EVEN addresses (2, 4, 6, 8, ...)

**Example of Problem:**
- **Meter:** post_id 720-25020 at address **2502 Washington St** (EVEN)
- **CNN:** 13440000 (Washington St North, 2500-2598)
- **Current Behavior:** Meter appears on BOTH L and R sides ❌
- **Expected Behavior:** Meter should ONLY appear on R side (EVEN) ✅

**Root Cause:**
In `ingest_data_cnn_segments.py` lines 961-964, the CNN fallback matching checks if the meter address falls within the segment range but does NOT validate odd/even parity:

```python
# CURRENT CODE (BUGGY)
if from_num <= meter_address <= to_num:
    matched_segment = segment
    match_method = "cnn_fallback"
    break
```

**Required Fix:**
Add odd/even parity validation before matching:

```python
# FIXED CODE
is_odd = meter_address % 2 == 1
if from_num <= meter_address <= to_num:
    # Validate odd/even parity matches side
    if (side == 'L' and is_odd) or (side == 'R' and not is_odd):
        matched_segment = segment
        match_method = "cnn_fallback"
        break
```

**Impact:**
- ❌ Meters incorrectly duplicated across both sides of street
- ❌ Users see wrong meter information for their side
- ❌ Data integrity compromised for meter assignments
- ⚠️ Affects ALL meters matched via CNN fallback (secondary matching strategy)

**Implementation:**
✅ **Fixed in ingest_data_cnn_segments.py** (January 7, 2026)
- Modified CNN fallback matching logic (lines 939-975)
- Added `is_odd = meter_address % 2 == 1` calculation
- Added parity validation: `if (side == 'L' and is_odd) or (side == 'R' and not is_odd)`
- Prevents meters from being assigned to wrong side

**Impact:**
- ✅ Meters now correctly assigned to single side based on address parity
- ✅ Eliminates duplicate meter assignments across both sides
- ✅ Ensures data integrity for meter-to-segment matching
- ⚠️ Requires re-running ingestion to fix existing duplicates

**Status:** Resolved - Code fix implemented, pending re-ingestion

**Next Steps:**
1. ✅ Document issue in DATA_QUALITY_LOG.md
2. ✅ Implement odd/even validation in `ingest_data_cnn_segments.py`
3. ⏳ Re-run ingestion to fix existing duplicate assignments
4. ⏳ Verify meter 720-25020 only appears on R side after fix

**Reference:**
- Bug Location: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py:961-964)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md:10-28)
- Convention: L=ODD, R=EVEN (universal US standard)

---

### Issue #016: Display Order - Meter Rules Scattered by Time - ✅ RESOLVED

**Date Discovered:** January 7, 2026
**Date Resolved:** January 7, 2026
**Dataset:** Display Logic (generate_interpretation_layer.py)
**Issue Type:** Display Ordering Logic
**Severity:** Medium

**Description:**
The display logic was sorting all rules (non-metered, metered, street cleaning) chronologically by start time. This caused meter schedules to be scattered throughout the list based on their times, breaking up the logical grouping.

**Example of Problem:**
```
2hr limit Weekdays 8am-6pm except permit  (non-metered)
Street Cleaning Tu 12pm-2pm               (street cleaning - 12pm)
24hr Meter M-Sa 9am-6pm                   (meter - 9am)
24hr Meter Su 12pm-6pm                    (meter - 12pm, scattered)
```

**User Requirement:**
Group by **broad type** - once you start displaying meter information, aggregate ALL meter rules together before moving to other types.

**Desired Order:**
```
1. Non-metered regulations (time-limit, RPP, no-parking)
2. ALL meter schedules grouped together
3. Street cleaning (absolute prohibition)
```

**Implementation:**
✅ **Fixed in generate_interpretation_layer.py** (January 7, 2026)
- Modified `_format_rules_display()` method (lines 319-371)
- Added `get_type_group_and_time()` function for type-based grouping
- Sort order: (1) type group, (2) start time within group
- Maintains chronological order within each group

**Impact:**
- ✅ Meter schedules now appear together as a logical group
- ✅ Within-group chronology preserved (Monday-first still works)
- ✅ Clear hierarchy: Non-metered → Meters → Street Cleaning
- ✅ Improved user experience with logical rule grouping

**Status:** Resolved - Display logic updated with broad type grouping

**Reference:**
- Implementation: [`generate_interpretation_layer.py`](generate_interpretation_layer.py:319-371)
- Architecture: Display ordering follows user mental model

---

### Issue #014: Empty Regulation Field in Parking Regulations Dataset - 🚨 DATA ERROR

**Date Discovered:** January 3, 2026
**Dataset:** Parking Regulations (`hi6h-neyh`)
**Issue Type:** Missing Required Field Data
**Severity:** High
**Count:** 5 regulations (0.02% of dataset)

**Description:**
Five parking regulation records have empty `regulation` fields, making them unusable for display or enforcement. The `regulation` field is the primary field containing the parking restriction text that users need to see.

**Affected Regulations:**
```
Regulation IDs: 3295, 3948, 3561, 3949, 3947
Count: 5 out of ~25,000 regulations (0.02%)
Pattern: All have empty regulation field
```

**Impact:**
- Cannot display parking restrictions to users
- Cannot determine restriction type or severity
- Cannot apply these regulations to street segments
- Reduces data completeness by 0.02%

**Root Cause:**
Data quality issue in SFMTA source dataset. These records appear to be incomplete or corrupted entries that should not have been published.

**Workaround:**
✅ **Exclusion During Ingestion** (January 3, 2026)
- Filter out regulations with empty `regulation` field during ingestion
- Log excluded regulation IDs for SFMTA reporting
- Document in data quality issues for future reference
- No user impact since regulations cannot be displayed anyway

**Status:** Documented - Excluded from ingestion, reported to SFMTA

**Reference:**
- Data Quality Issues: Issue #11 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)
- Fallback Matching: [`FALLBACK_MATCHING_STRATEGY.md`](FALLBACK_MATCHING_STRATEGY.md)

---

### Issue #015: Unmatched Parking Regulations - Fallback Matching Strategy - ✅ STRATEGY DEFINED

**Date Discovered:** January 3, 2026
**Dataset:** Parking Regulations (`hi6h-neyh`)
**Issue Type:** Geospatial Matching Failure
**Severity:** Medium
**Count:** 7 regulations (0.03% of dataset)

**Description:**
Seven parking regulations failed to match to street segments using standard geospatial matching. These regulations have valid data but require fallback matching strategies using district boundaries, neighborhood boundaries, or RPP area boundaries.

**Affected Regulations:**

**Type 1: Geometry + District + Neighborhood (3 regulations)**
```
Regulation IDs: 4973, 64, 2191
Pattern: Have geometry, supervisor_district, and analysis_neighborhood
Strategy: Match to segments nearby geometry in same district+neighborhood
Skip Condition: Skip if segment has non-meter parking regulations (meters/cleaning OK)
```

**Type 2: RPP Areas Only (4 regulations)**
```
Regulation IDs: 1551, 2303, 2353, 17287
Pattern: No geometry, only RPP area fields (rpparea1, rpparea2, rpparea3)
Strategy: Match using synthetic RPP boundaries
Matching Logic:
  - Try RPP + district + neighborhood first
  - Fallback to RPP only if district/neighborhood empty
Skip Condition: Skip if segment has RPP rules OR non-meter parking regulations
```

**Implementation Status:**
✅ **Fallback Strategy Defined** (January 3, 2026)
- RPP area boundaries generated (33 boundaries)
- District boundaries ready for generation (11 districts)
- Database indexes created for efficient fallback queries
- Centralized fallback matching script planned
- Documentation: [`FALLBACK_MATCHING_STRATEGY.md`](FALLBACK_MATCHING_STRATEGY.md)

**Impact:**
- 0.03% of regulations not applied to street segments
- Minimal user impact (very small percentage)
- Fallback matching will recover most/all of these regulations
- No safety concerns (regulations are non-critical)

**Workaround:**
✅ **Synthetic Boundary Matching** (In Progress)
1. Generate RPP area boundaries from matched regulations (DONE)
2. Generate district boundaries from street segments (PENDING)
3. Implement centralized fallback matching script (PENDING)
4. Apply different logic for Type 1 vs Type 2 regulations (PENDING)
5. Update documentation with results (PENDING)

**Status:** Strategy Defined - Implementation In Progress

**Reference:**
- Fallback Strategy: [`FALLBACK_MATCHING_STRATEGY.md`](FALLBACK_MATCHING_STRATEGY.md)
- RPP Boundaries: `rpp_area_boundaries` MongoDB collection
- District Analysis: [`investigate_district_boundaries.py`](investigate_district_boundaries.py)
- Data Quality Issues: Issue #12 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

---

### Issue #013: Street Cleaning Dataset Analysis and Integration - ✅ DOCUMENTED

### Issue #013: Street Cleaning Dataset Analysis and Integration - ✅ DOCUMENTED

**Date Discovered:** December 4, 2025
**Date Analyzed:** December 31, 2025
**Dataset:** Street Cleaning Schedules (`yhqp-riqs`)
**Issue Type:** Asymmetric Coverage + HOLIDAY Override Pattern
**Severity:** Critical (Absolute Prohibition - Overrides All Parking Availability)

**Description:**
Comprehensive analysis of street cleaning dataset revealed two key findings:
1. **Asymmetric Coverage**: 15.8% of CNNs have cleaning on only ONE side
2. **HOLIDAY Override Pattern**: 1.40% of CNN+sides use HOLIDAY entries to override holidays=1 settings

**Analysis Results:**

**1. Asymmetric Coverage (Issue #1 in DATA_QUALITY_ISSUES.md)**
```
Total CNNs in dataset: 12,253
CNNs with BOTH sides: 10,320 (84.2%)
CNNs with ONLY ONE side: 1,933 (15.8%)
Total records: 37,878
```

**Sample Missing Records:**
- CNN 111000 - 01st St (R side present, L side missing)
- CNN 961000 - 19th St (L side present, R side missing) ← Verified on-site
- Pattern: No clear L vs R bias - both sides affected

**2. HOLIDAY Override Pattern (Verified December 31, 2025)**
```
CNN+sides with HOLIDAY override: 172 (1.40%)
Pattern: HOLIDAY entry with holidays=0 overrides days with holidays=1

Distribution:
- 1 day with holidays=1: 138 cases (80.2%)
- 2 days with holidays=1: 29 cases (16.9%)
- 4 days with holidays=1: 5 cases (2.9%)

Most Common Override Days:
- Monday: 79 cases (45.9%)
- Saturday: 59 cases (34.3%)
```

**Example: CNN 6113000 (Geary St at Shannon St)**
```
Side L (South): Tu, Th, Su 6am-8am, holidays=0
Side R (North): M, W, F, Sa 6am-8am
  - Monday has holidays=1 (would clean on holidays)
  - HOLIDAY entry has holidays=0 (overrides Monday)
  - Result: NO cleaning on SF's 3 holidays
```

**3. Week-of-Month Field Structure**
```
Fields: week1, week2, week3, week4, week5 (NOT week1ofmon)
Values: 1 = active, 0 = not active
Usage: 100% of records use week-of-month scheduling

Most Common Patterns:
- All weeks (1st-5th): 62.8%
- 2nd & 4th only: 18.4%
- 1st & 3rd only: 11.6%
- 1st, 3rd, 5th: 5.9%
```

**4. Holiday Field Analysis**
```
holidays=0 (no cleaning on holidays): 92.7%
holidays=1 (cleaning on holidays): 7.3%

SF Holidays (when holidays=0):
- January 1 (New Year's Day)
- December 25 (Christmas Day)
- 4th Thursday of November (Thanksgiving)
```

**Impact:**

**User Safety - CRITICAL:**
- Users parking on 1,933 affected segments won't see street cleaning restrictions
- Risk of parking tickets AND TOWING (street sweeping guarantees tow)
- Street sweeping is absolute prohibition - overrides all parking availability
- Financial impact: Towing fees ($300+) plus parking ticket ($76+)

**Data Completeness:**
- 15.8% asymmetric coverage requires manual verification
- 1.40% HOLIDAY override pattern requires special handling
- Unknown how many other records are missing

**Implementation Status:**

✅ **Analysis Complete** (December 31, 2025)
- Scripts: [`analyze_street_cleaning_dataset.py`](analyze_street_cleaning_dataset.py), [`analyze_week_fields_correct.py`](analyze_week_fields_correct.py), [`analyze_holiday_override_socrata.py`](analyze_holiday_override_socrata.py)
- Documentation: [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)
- Verification List: `street_cleaning_manual_verification.csv` (1,933 streets)
- Analysis Reports: `street_cleaning_analysis_report.json`, `week_analysis_corrected.json`, `holiday_override_analysis.json`

✅ **Display Format Defined**
```
Format: "Street Cleaning {days} {time_range} {holiday_clause}"
Days: M, Tu, W, Th, F, Sa, Su (comma-separated)
Time: "6am-8am", "12pm-2pm" (12-hour format)
Holiday: " except holidays" (when holidays=0 or HOLIDAY override)
Week-of-Month: "2nd & 4th Thu", "Every Mon", "1st, 3rd, 5th Fri"
```

**Examples:**
```
CNN 6113000L: "Street Cleaning Tu, Th, Su 6am-8am except holidays"
CNN 6113000R: "Street Cleaning M, W, F, Sa 6am-8am except holidays"
Standard: "Street Cleaning 2nd & 4th Thu 8am-10am except holidays"
All weeks: "Street Cleaning Every Mon 6am-8am except holidays"
```

**Integration Decisions:**
1. ✅ Display only available sides (no inference for missing data)
2. ✅ Use ordinal numbers for weeks ("2nd & 4th" not "Week 2 & 4")
3. ✅ Show "except holidays" when holidays=0 or HOLIDAY override exists
4. ✅ Integrate now with documented gaps
5. ✅ Log for future SFMTA report

**Workaround:**
✅ **Manual Override System** (Active since December 29, 2025)
- Override File: [`manual_data_overrides.json`](manual_data_overrides.json)
- Application: [`apply_manual_overrides.py`](apply_manual_overrides.py)
- Integration: STEP 5.4 in [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)
- Current: 19th St R 2700-2798 (CNN 961000) verified and applied

**Status:** Documented - Ready for integration with comprehensive analysis and display format specification

**Reference:**
- Complete Guide: [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)
- Data Quality Issues: Issue #1 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)
- Analysis Scripts: [`analyze_street_cleaning_dataset.py`](analyze_street_cleaning_dataset.py), [`analyze_week_fields_correct.py`](analyze_week_fields_correct.py), [`analyze_holiday_override_socrata.py`](analyze_holiday_override_socrata.py)

---

### Issue #012: Meter Rates Not Applied to CNN Master - ✅ RESOLVED

**Date Discovered:** December 31, 2025
**Date Resolved:** December 31, 2025
**Dataset:** Meter Rate Schedule (fwjv-32uk), CNN Master Reference
**Issue Type:** Missing Rate Data
**Severity:** Medium

**Description:**
Meter rates from the SFMTA Meter Rate Schedule dataset (fwjv-32uk) were not applied to the CNN master dataset. All meter schedules in the CNN master had `rate: null`, preventing the display of parking rates to users.

**Implementation Status:**
✅ **Meter Rate Application Completed** (December 31, 2025)
- Script: [`apply_meter_rates_to_cnn_master.py`](apply_meter_rates_to_cnn_master.py)
- Module: [`regulation_normalizer.py`](regulation_normalizer.py) - Single source of truth for all regulation processing
- Documentation: [`METER_RATE_APPLICATION_SUMMARY.md`](METER_RATE_APPLICATION_SUMMARY.md)
- Output: `cnn_master_with_rates.json`

**Results:**
```
Total rate records fetched: 60,485
Unique post_ids: 29,379
Schedules matched: 109,074 (100%)
Schedules unmatched: 0
Rate conflicts found: 0
```

**Matching Logic:**
1. **Primary Match**: post_id + days_applied + from_time + to_time
   - Exact match on all four fields for schedules with specific days/times
2. **Fallback Match**: post_id only (base rate)
   - Used when meter schedule has no days_applied
   - Matches to rate schedule with no days_applied or time fields

**Data Quality Findings:**
- ✅ **Zero Rate Conflicts**: No instances of same post_id + days + time with different rates
- ✅ **Perfect Schedule Matching**: 100% of schedules (109,074) successfully matched to rates
- ⚠️ **11,806 meters not in rate dataset** (21.1%) - consistent with Issue #007 (21.5% lack schedules)

**Impact:**
- ✅ All meter schedules now have rates applied
- ✅ Users can see parking rates for all metered locations
- ✅ Complete rate information for parking planning
- ✅ No data loss during application

**Status:** Resolved - Complete rate application with zero conflicts

**Reference:**
- Complete Summary: [`METER_RATE_APPLICATION_SUMMARY.md`](METER_RATE_APPLICATION_SUMMARY.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)
- Script: [`apply_meter_rates_to_cnn_master.py`](apply_meter_rates_to_cnn_master.py)

### Issue #010: Duration/Time Limit Standardization - ✅ RESOLVED

**Date Discovered:** December 31, 2025
**Date Resolved:** December 31, 2025
**Dataset:** All datasets with time limits (Parking Regulations, Meter Schedules, Meter Policies)
**Issue Type:** Inconsistent Units and Formats
**Severity:** Medium

**Description:**
Time limits and durations were stored and displayed inconsistently across different datasets:
- Some used hours (hrlimit: "2", "0.5", "72")
- Some used minutes (time_limit_minutes: 120, 30, 240)
- Multiple representations (string, integer, float)
- Inconsistent display formats ("2hr limit", "2 hour limit", "120 minutes")

**Implementation Status:**
✅ **Duration Standardization Completed** (December 31, 2025)
- Module: [`regulation_normalizer.py`](regulation_normalizer.py)
- Test Suite: [`test_duration_standardization.py`](test_duration_standardization.py) - 48/48 tests passing
- Integration: Updated all code files using manual duration conversions
- Documentation: [`DURATION_STANDARDIZATION_COMPLETE.md`](DURATION_STANDARDIZATION_COMPLETE.md)

**Standardization Approach:**
```
Canonical Format:
  - Storage: Always integer minutes
  - Display: Pre-computed strings ("2hr", "30min", "No")
  
Dataset Adapters:
  - Parking Regulations (hi6h-neyh): hrlimit in hours
  - Meter Schedules (6cqg-dxku): time_limit_minutes in minutes
  - Meter Policies (qq7v-hds4): timelimitminutes in minutes
  
Special Handling:
  - 72hr RPP: Filtered out (permit-holder only, non-permit users have 2hr limit)
  - Fractional hours: Supported (0.5hr = 30min, 1.5hr = 90min)
```

**Impact:**
- ✅ Consistent duration storage across all datasets (integer minutes)
- ✅ Consistent display format ("hr", "min" singular, no spaces)
- ✅ Pre-computed display strings (zero runtime overhead)
- ✅ 72hr RPP rules filtered at individual rule level
- ✅ Single source of truth for all duration logic
- ✅ Complete test coverage (48 tests)

**Integration Points:**
- Core Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) lines 354-390, 604-631
- Normalization: [`regulation_normalizer.py`](regulation_normalizer.py) lines 537-929
- Deprecated: [`deterministic_parser.py`](deterministic_parser.py) `_parse_duration()` marked deprecated
- Deprecated: [`display_utils.py`](display_utils.py) duration formatting removed

**Status:** Resolved - Complete duration standardization with centralized parsing and formatting

**Reference:**
- Complete Summary: [`DURATION_STANDARDIZATION_COMPLETE.md`](DURATION_STANDARDIZATION_COMPLETE.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)
- Test Suite: [`test_duration_standardization.py`](test_duration_standardization.py)

### Issue #011: ALTERNATE Schedule and Cap Color Standardization - ✅ RESOLVED

**Date Discovered:** December 31, 2025
**Date Resolved:** December 31, 2025
**Dataset:** Meter Operating Schedules (6cqg-dxku), Special Event Areas (itv4-r6g6), Parking Meters (8vzz-qzz9)
**Issue Type:** Incomplete Documentation and Display Logic
**Severity:** Medium

**Description:**
The system lacked comprehensive documentation and standardized display logic for:
1. Special event zone meters (Oracle Park, Chase Center) - ~2,400 meters (7.9%)
2. Non-day-of-week ALTERNATE schedules - 371 schedules (0.51%)
3. Complete cap color legend - Previously simplified to 2 colors, actually 6 colors
4. Curby user eligibility rules for cap colors

**Implementation Status:**
✅ **Regulation Normalization Completed** (December 31, 2025)
- Module: [`regulation_normalizer.py`](regulation_normalizer.py)
- Documentation: [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md)
- Analysis: [`ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md`](ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md)

**Findings:**

**1. Special Event Zone Meters (Geospatial)**
- Count: ~2,400 meters (7.9% of total)
- Zones: Oracle Park, Chase Center, overlap areas
- Identification: Spatial join with Special Event Areas dataset (itv4-r6g6)
- Display Format:
  ```
  Line 1: [Zone Name] Schedule and Rates may apply. See schedule for details.
  Line 2: All Other Days [duration] [days] [time] ($[rate]/hr)
  Line 3: All Other Weekends [duration] [days] [time] ($[rate]/hr) [if multiple schedules]
  ```
- SFMTA URL: https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule

**2. Non-DOW ALTERNATE Schedules (Condition-Based)**
- Count: 371 schedules (0.51% of total)
- Patterns: 7 distinct types
  * School Days: 177 (0.24%)
  * Giants Day: 52 (0.07%)
  * Giants Night: 52 (0.07%)
  * Performance: 50 (0.07%)
  * Posted Events: 19 (0.03%)
  * Posted Services: 19 (0.03%)
  * Business Hours: 2 (0.00%)
- Common characteristics:
  * `schedule_type: "Alternate"`
  * `applied_color_rule: "White - Passenger loading zone"`
  * `time_limit: "0 minutes"` (no parking when active)
  * Severity 3 (TOW + VIOLATION) when condition active
- Display Format:
  ```
  Line 1: Passenger Loading Zone on [interpretation]
  Line 2: All other days [duration] [days] ($[rate]/hr)
  ```

**3. Complete Cap Color Legend**
- Previously: Simplified to 2 colors (YELLOW/RED vs others)
- Actually: 6 distinct colors with specific vehicle restrictions

| Cap Color | Vehicle Type | Curby User Eligible |
|-----------|--------------|---------------------|
| BLACK | Motorcycle only | ❌ NO |
| BROWN | Tour Bus only | ❌ NO |
| GREY | General parking | ✅ YES |
| GREEN | General parking | ✅ YES |
| PURPLE | Boat Trailer only | ❌ NO |
| RED | Commercial 6+ wheels | ❌ NO |
| YELLOW | Commercial Vehicle | ❌ NO |

**For Curby Users (Standard Cars):**
- ELIGIBLE: GREY, GREEN only
- INELIGIBLE: BLACK, BROWN, PURPLE, RED, YELLOW
- Default Assumption: Curby users are in standard cars

**4. Blockface-Level Aggregation**
- Cap colors aggregated at CNN+SIDE (blockface) level
- Majority rule: If majority of meters are eligible → Block eligible
- Rationale: Users need to know if they can find ANY parking on a blockface

**Impact:**
- ✅ Complete documentation of all ALTERNATE schedule patterns
- ✅ Standardized display format for special event zones
- ✅ Complete 6-color cap color legend with proper vehicle classifications
- ✅ Clear Curby user eligibility rules (GREY/GREEN only)
- ✅ Proper restriction classification (absolute prohibition when active, parking availability when inactive)
- ✅ Single source of truth in regulation_normalizer.py
- ✅ No calendar integration needed (users see all rules)

**Integration Points:**
- Core Implementation: [`regulation_normalizer.py`](regulation_normalizer.py)
  * Part 8: Cap Color Normalization (lines 936-1194)
  * Part 9: Meter Schedule Priority (lines 1196-1433)
  * Part 10: Special Event Zone Display (lines 1435-1621)
- Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6

**Status:** Resolved - Complete regulation normalization with standardized display logic

**Reference:**
- Complete Summary: [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md)
- ALTERNATE Analysis: [`ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md`](ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)
- Data Files: [`non_dow_days_applied_patterns.json`](non_dow_days_applied_patterns.json), [`non_dow_days_applied_patterns.csv`](non_dow_days_applied_patterns.csv)

---

---

### Issue #009: Blockface Geometry Integration - ✅ RESOLVED
**Date Discovered:** December 30, 2025
**Date Resolved:** December 30, 2025
**Dataset:** MongoDB Existing Blockfaces + Active Streets + pep9-66vw + mk27-a5x2
**Issue Type:** Missing Blockface Geometries
**Severity:** Medium
**Count:** 100% coverage achieved (34,324 segments)

**Description:**
Previously, the system lacked complete blockface geometry coverage, with only ~50-60% of CNN entries having blockface edge geometries. This limited the ability to accurately visualize parking edges and validate meter placements.

**Implementation Status:**
✅ **THREE-PRIORITY Blockface Integration Completed** (December 30, 2025)
- Calibration Analysis: [`calibrate_from_existing_blockfaces.py`](calibrate_from_existing_blockfaces.py)
- MongoDB Update: [`update_synthetic_blockfaces_with_calibration.py`](update_synthetic_blockfaces_with_calibration.py)
- Core Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 2.5
- Analyzed 34,324 existing blockfaces from MongoDB to learn offset patterns
- Updated 31,930 synthetic blockfaces with calibrated offsets
- Preserved 2,394 deterministic blockfaces from source datasets

**THREE-PRIORITY Integration:**
```
Priority 1: Deterministic from pep9-66vw
  - 2,370 segments (6.9%)
  - Confidence: 1.0 (surveyed geometries)

Priority 2: Deterministic from mk27-a5x2
  - 24 segments (0.1%)
  - Confidence: 1.0 (validated geometries)

Priority 3: Synthetic with Meter Calibration
  - 31,930 segments (93.0%)
  - Confidence: 0.85 (data-driven offsets)
  - L Side: +5.55m median (17,162 samples, std 3.17m)
  - R Side: -5.55m median (17,162 samples, std 3.53m)
```

**MongoDB Update Results:**
```
Total Segments: 34,324
Deterministic Preserved: 2,394 (7.0%)
Synthetic Updated: 31,930 (93.0%)
Update Success Rate: 100% (0 failures)
Calibration Source: 34,324 meter samples
```

**Impact:**
- ✅ Complete blockface coverage (100% vs previous ~50-60%)
- ✅ Deterministic geometries preserved where available
- ✅ Synthetic geometries use meter-calibrated offsets (11% more accurate)
- ✅ Accurate parking edge visualization
- ✅ Meter placement validation enabled
- ✅ Improved spatial query accuracy
- ✅ Future ingestions automatically use calibrated offsets

**Data Structure:**
Each CNN segment now includes:
```json
{
  "cnn": "123000",
  "side": "L",
  "blockfaceGeometry": {
    "type": "LineString",
    "coordinates": [[lon, lat], ...]
  }
  // Metadata tracked internally:
  // - Deterministic: from pep9-66vw or mk27-a5x2 (confidence 1.0)
  // - Synthetic: meter-calibrated offset (confidence 0.85)
}
```

**Architectural Decision - Layer 4B Scrapped:**
**Date:** December 31, 2025
**Decision:** Do NOT pursue additional deterministic blockface matching from pep9-66vw

**Rationale:**
- Current THREE-PRIORITY system provides 100% coverage with acceptable quality
- Potential improvement: Only 8-13% more deterministic coverage (from 7% to 15-20%)
- Remaining 80-85% would still require synthetic geometries
- High effort, low impact - synthetic geometries already provide production-quality results
- Meter-calibrated offsets are 11% more accurate than fixed offsets

**Status:** Resolved - 100% blockface geometry coverage with optimal THREE-PRIORITY integration. Layer 4B (additional deterministic matching) scrapped per cost/benefit analysis.

**Reference:**
- Complete Summary: [`BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md`](BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md)
- Issue Resolution: [`BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md`](BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Layer 4B section
- Calibration Data: [`blockface_offset_calibration.json`](blockface_offset_calibration.json)

---

### Issue #007: Missing Meter Operating Schedules
**Date Discovered:** December 30, 2025
**Date Implemented:** December 30, 2025
**Dataset:** Meter Operating Schedules (`6cqg-dxku`)
**Issue Type:** Missing Data Records
**Severity:** High
**Count:** 6,624 out of 30,797 active meters (21.5%)

**Description:**
21.5% of active On Street parking meters lack operating schedule information in the Meter Operating Schedules dataset (6cqg-dxku). This prevents the application from displaying meter rates, time limits, and operating hours for affected locations.

**Implementation Status:**
✅ **Full Meter Integration Completed** (December 30, 2025)
- Script: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6
- Meters embedded directly into MongoDB street_segments collection with base operating schedules
- Address-based matching (PRIMARY) with CNN fallback
- Special event meters flagged (~2,400 meters near Oracle Park/Chase Center)
- Schedule priority hierarchy: TOW > ALTERNATE > OP/FREE/PRE

**Affected Meters:**
```
Total Active On Street Meters: 30,797
Meters WITH schedules: 24,173 (78.5%)
Meters WITHOUT schedules: 6,624 (21.5%)

Geographic Distribution: Citywide (not concentrated in special areas)
- Only 13.4% (889 meters) are in Special Event areas
- 86.6% (5,735 meters) are regular street meters throughout SF
```

**Pattern Identified:**
- NOT limited to special event areas (only 13.4% in special zones)
- Distributed throughout San Francisco
- 99.9% of affected meters have valid CNN mapping
- Suggests systematic data collection or maintenance gap

**Impact:**
- Users cannot see meter operating schedules, rates, or time limits
- Must physically check meter for information
- Reduces app utility for parking planning
- May lead to confusion about meter operation

**Additional Finding - Orphaned Schedules:**
- 5,198 postIDs (17.7%) in schedules do NOT map to active meters
- Likely historical/inactive meters that have been removed
- Indicates need for schedule dataset cleanup

**Workaround:**
✅ **User Notification Implemented** (December 30, 2025)
- Display clear message when meter schedule unavailable
- Direct users to check physical meter
- Provide meter PostID and location for reference
- CNN-based street regulations still available

✅ **System Integration** (December 30, 2025)
- Meters without schedules still included in MongoDB street_segments collection
- Physical meter location and attributes available
- System gracefully handles missing schedule data
- Users can see meter exists even without schedule details

**User Notification Template:**
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

**Status:** Mitigated - Full meter integration implemented with graceful handling of missing schedules

**Reference:**
- Investigation: [`METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md`](METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md)
- Implementation: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6

---

### Issue #006: Missing Street Cleaning Schedule - 19th St R Side
**Date Discovered:** December 4, 2025
**Dataset:** Street Cleaning Schedules (`yhqp-riqs`)
**Issue Type:** Missing Data Record
**Severity:** Critical (Absolute Prohibition - Overrides All Parking Availability)
**Count:** 1 confirmed case (unknown total)

**Description:**
Street cleaning schedule is missing for 19th Street Right (North) side, address range 2700-2798, despite physical street signs confirming the schedule exists. The same CNN (961000) has data for the Left (South) side but the Right side record is absent from the SFMTA dataset.

**Affected Segment:**
```
Street: 19TH ST
Side: R (Right/North)
Address Range: 2700-2798
CNN: 961000
Schedule: Thursday 12:00 AM - 6:00 AM (verified on-site)
Cardinal Direction: North
```

**Pattern Identified:**
- CNN 961000 has L side data ✓ (Friday 12AM-6AM, South side)
- CNN 961000 R side data is MISSING ✗ (Thursday 12AM-6AM, North side)
- Suggests potential systematic issue with right-side data collection

**Impact:**
- **CRITICAL**: Street sweeping is an absolute prohibition that overrides all parking availability
- Users parking on this segment won't see the absolute parking prohibition
- Risk of parking tickets AND TOWING (street sweeping guarantees tow)
- Display logic will show incorrect "most restrictive" condition (may show metered or time-limited parking instead of sweeping)
- Financial impact: Towing fees ($300+) plus parking ticket ($76+)
- Undermines user trust in app accuracy
- Unknown how many other segments are affected

**Regulation Architecture Context:**
Street sweeping is an absolute prohibition that overrides all parking availability types:
- Metered parking (including meter TOW, ALTERNATE, OP/FREE/PRE schedules)
- Non-metered regulations (time-limited, RPP)

**Key Distinction:**
- Meter TOW schedules are meter-specific (apply only to metered spaces)
- Street sweeping is street-level (applies to entire segment)
- Street sweeping overrides even meter TOW schedules

Missing this data means users may see lower severity regulations but miss the absolute street-level restriction.

**Workaround:**
✅ **Manual Override Implemented** (December 29, 2025)
- Added to [`manual_data_overrides.json`](manual_data_overrides.json) as override ID `19th-st-r-2700-2798`
- Verified on-site: December 4, 2025
- Applied automatically during ingestion at STEP 5.4
- Marked with `"source": "manual_override"` for traceability

**Status:** Mitigated - Manual override active, monitoring for similar cases

---

### Issue #005: Stanyan St Incorrectly Labeled as Stanyan Blvd
**Date Discovered:** December 29, 2025
**Dataset:** Active Streets (`3psu-pn9h`)
**Issue Type:** Incorrect Street Type Classification
**Severity:** High
**Count:** 3 CNN segments (out of 27 total Stanyan segments)

**Description:**
Three CNN segments on Stanyan St are incorrectly labeled with street type "BLVD" instead of "ST" in the SFMTA Active Streets dataset. There is no "Stanyan Blvd" in San Francisco - the entire street is "Stanyan St". This causes meter matching failures because parking meters reference "STANYAN ST" but these segments are labeled "STANYAN BLVD".

**Affected CNNs:**
```
CNN 12076000: L:2-98 / R:1-99 (GEARY BLVD to ANZA ST)
  - Labeled as: STANYAN BLVD
  - Should be: STANYAN ST
  - CRITICAL: Contains low address ranges (1-99) needed for meter matching

CNN 12077000: L:100-148 / R:101-147 (ANZA ST to LONE MOUNTAIN TER)
  - Labeled as: STANYAN BLVD
  - Should be: STANYAN ST

CNN 12078000: L:150-198 / R:149-199 (LONE MOUNTAIN TER to TURK BLVD)
  - Labeled as: STANYAN BLVD
  - Should be: STANYAN ST
```

**Impact:**
- **4 parking meters cannot match to CNN** (meters 669-00020, 669-00030, 669-00010, 669-00040)
- Meters reference blockface ranges 2-70 (L) and 3-99 (R) on "STANYAN ST"
- Matching algorithm searches for "STANYAN ST" but these segments are labeled "STANYAN BLVD"
- CNN 12076000 contains the critical low address ranges (1-99) needed for these meters
- Reduces meter matching success rate from 99.99% to 99.96%

**Root Cause:**
Data error in SFMTA Active Streets dataset. The `st_type` field is incorrectly set to "BLVD" for these three segments, while the remaining 24 Stanyan segments are correctly labeled as "ST".

**Workaround:**
1. Add manual override in [`manual_data_overrides.json`](manual_data_overrides.json) to correct street type
2. Update matching algorithm to normalize "STANYAN BLVD" → "STANYAN ST"
3. Apply correction during data ingestion

**Solution:**
- Document in manual overrides system
- Apply correction during CNN Master Reference build (Layer 1)
- Report to SFMTA for upstream correction

**Status:** Open - Documented, workaround implemented

---

### Issue #001: Missing CNN in On-Street Meters
**Date Discovered:** December 29, 2025
**Dataset:** Parking Meters (`8vzz-qzz9`)  
**Issue Type:** Missing Required Field  
**Severity:** Low  
**Count:** 14 out of 37,421 on-street meters (0.04%)

**Description:**
14 on-street parking meters have NULL values in the `street_seg_ctrln_id` (CNN) field, preventing direct matching to the Active Streets backbone.

**Sample Records:**
```
Post ID: 491-06001, Street: INDIANA ST 601, CNN: NULL, Blockface: 491061
Post ID: 331-04009, Street: BRYANT ST, CNN: NULL, Blockface: 331041
Post ID: 669-00020, Street: STANYAN ST, CNN: NULL, Blockface: 669002
Post ID: 551-00006, Street: LAPU-LAPU ST 6, CNN: NULL, Blockface: 551002
Post ID: 669-00030, Street: STANYAN ST, CNN: NULL, Blockface: 669001
```

**Impact:**
- Cannot use primary CNN-based matching
- Requires fallback to blockface_id or spatial matching
- Minimal impact (0.04% of meters)

**Workaround:**
1. Use `blockface_id` to lookup in Metered Blockfaces dataset
2. Match via street name + address range
3. Fallback to spatial proximity if needed

**Status:** Open - Monitoring for future data updates

---

### Issue #002: Invalid CNN Value in Meters
**Date Discovered:** December 29, 2025
**Dataset:** Parking Meters (`8vzz-qzz9`)  
**Issue Type:** Invalid Data Value  
**Severity:** Low  
**Count:** 1 meter (0.003%)

**Description:**
One meter has CNN value of "0" which does not exist in Active Streets dataset.

**Sample Records:**
```
Post ID: 000-00000, Street: NULL, Street #: 0, CNN: 0, Blockface: 0
```

**Impact:**
- Appears to be a test/placeholder record
- Does not represent real parking infrastructure
- May need to be filtered out during ingestion

**Workaround:**
Filter out records where `post_id` = "000-00000" or CNN = "0"

**Status:** Open - Needs investigation if this is a valid meter

---

### Issue #003: Fuzzy Matching Unreliability for Blockfaces
**Date Discovered:** December 28, 2025
**Dataset:** Blockface Geometry (`pep9-66vw`)  
**Issue Type:** Matching Algorithm Limitation  
**Severity:** High  
**Count:** 79% of blockfaces cannot be reliably matched

**Description:**
Fuzzy matching algorithm for blockfaces to CNN segments achieves only 21.4% accuracy when tested against ground truth (113 blockfaces with known CNNs).

**Root Cause:**
Street Intersections dataset (`pu5n-qu5c`) only provides ONE cross street (`from_st`), but blockfaces require TWO cross streets (from/to) for unique identification.

**Impact:**
- Cannot reliably match blockfaces without CNN IDs using text-based fuzzy matching
- 78.6% false positive rate is unacceptable for production

**Solution:**
Abandon fuzzy matching. Use deterministic matching only:
1. Build CNN Master Reference from Active Streets + Street Intersections + Intersection Permutations
2. Match blockfaces using exact text matching (street name + from/to streets)
3. Discard blockfaces that cannot be deterministically matched
4. Accept 70-85% blockface coverage with 100% accuracy over 100% coverage with 21% accuracy

**Status:** Resolved - Architecture redesigned (see CNN_MASTER_REFERENCE_ARCHITECTURE.md)

---

## Resolved Issues

### Issue #004: Meter Matching Method Ambiguity
**Date Discovered:** December 29, 2025
**Date Resolved:** December 29, 2025
**Dataset:** Parking Meters (`8vzz-qzz9`)  
**Issue Type:** Implementation Clarity  
**Severity:** Medium

**Description:**
Initial implementation had ambiguous fallback logic for meters without blockface_id. Unclear if system would discard unmatchable meters.

**Resolution:**
Clarified that:
1. 100% of on-street meters have `blockface_id` (no meters lack this field)
2. System uses blockface_id as primary matching key
3. CNN is used for validation and side determination
4. No on-street meters are discarded

**Status:** Resolved

---

## Data Quality Metrics Dashboard

### Current Ingestion (December 2025)

| Dataset | Total Records | Issues Found | Issue Rate | Status |
|---------|--------------|--------------|------------|--------|
| Active Streets | 17,162 CNNs | 0 | 0% | ✓ Clean |
| Parking Meters (On-Street) | 37,421 | 15 | 0.04% | ⚠ Minor Issues |
| Parking Meters (Off-Street) | 935 | N/A | N/A | Not Analyzed |
| Blockface Geometry | ~50,000 | TBD | TBD | Needs Analysis |
| Metered Blockfaces | 3,131 | 0 | 0% | ✓ Clean |
| Street Intersections | ~100,000 | 0 | 0% | ✓ Clean |

### Historical Trends

*To be populated with each ingestion cycle*

---

## Data Quality Checklist for Each Ingestion

Use this checklist when running data ingestion:

- [ ] **Active Streets:** Verify all CNNs are unique and non-null
- [ ] **Parking Meters:** Check for NULL CNNs in on-street meters
- [ ] **Parking Meters:** Verify all on-street meters have blockface_id
- [ ] **Parking Meters:** Check for invalid CNN values (e.g., "0")
- [ ] **Blockface Geometry:** Count records with/without CNN IDs
- [ ] **Metered Blockfaces:** Verify blockface_id uniqueness
- [ ] **Cross-Dataset:** Validate CNN references exist in Active Streets
- [ ] **Cross-Dataset:** Check blockface_id references between datasets
- [ ] **Spatial Data:** Verify all geometries are valid (no NULL coordinates)
- [ ] **Matching Results:** Log match rates for each dataset
- [ ] **Unmatched Records:** Export list of unmatched records for review

---

## LLM Training Data Considerations

Data quality issues logged here can be valuable for:

1. **Training Examples:** Show LLM how to handle missing/invalid data
2. **Edge Cases:** Document unusual patterns in parking data
3. **Validation Logic:** Train LLM to identify data quality issues
4. **Reconciliation Patterns:** Teach LLM how to resolve conflicts
5. **Domain Knowledge:** Build understanding of SF parking data quirks

**Export Format for LLM Training:**
```json
{
  "issue_id": "001",
  "type": "missing_required_field",
  "dataset": "parking_meters",
  "field": "street_seg_ctrln_id",
  "severity": "low",
  "sample_records": [...],
  "resolution_strategy": "use_blockface_id_fallback",
  "success_rate": 1.0
}
```

---

## Future Enhancements

1. **Automated Logging:** Integrate data quality checks into ingestion pipeline
2. **Trend Analysis:** Track issue rates over time to identify degradation
3. **Alerting:** Notify when issue rates exceed thresholds
4. **Visualization:** Dashboard showing data quality metrics
5. **Export Tools:** Generate reports for stakeholders
6. **LLM Integration:** Use logged issues to train data validation models

---

## Notes

- This log should be updated with each data ingestion cycle
- Keep historical entries for trend analysis
- Use issue numbers for cross-referencing in code comments
- Export to JSON periodically for LLM training data
- Review quarterly to identify systemic patterns