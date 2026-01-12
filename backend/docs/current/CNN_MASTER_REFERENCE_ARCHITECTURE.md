> ⚠️ **SCHEMA UPDATE (Jan 1, 2026)**: MongoDB schema was optimized to remove redundant display fields. See [`SCHEMA_OPTIMIZATION_NOTE.md`](SCHEMA_OPTIMIZATION_NOTE.md) for details.

# CNN Master Reference Architecture

## Overview
Build a comprehensive CNN reference table by layering multiple SFMTA datasets in a specific order, starting with the foundational street network and progressively adding detail.

## Street Numbering Convention

**Critical Data Standard**: Across all SFMTA datasets containing street address numbers:
- **L (Left) side**: ODD street numbers (1, 3, 5, 7, etc.)
- **R (Right) side**: EVEN street numbers (2, 4, 6, 8, etc.)

This convention applies universally to:
- Street Intersections dataset (`pu5n-qu5c`) - address ranges in `limits` field
- Blockface Geometry dataset (`pep9-66vw`) - `l_from_addr`, `l_to_addr`, `r_from_addr`, `r_to_addr`
- Parking Meters dataset - address assignments
- All other datasets with street address information

**Example**: For a segment of Mission Street between 18th and 19th:
- L side (CNN_L): 2301-2399 Mission St (odd numbers)
- R side (CNN_R): 2300-2398 Mission St (even numbers)

This standard is essential for:
- Validating address range assignments
- Determining which side of the street a specific address is on
- Matching addresses to CNN segments
- Quality assurance during data ingestion

## Data Architecture Layers

### Layer 1: Foundation - Active Streets (3psu-pn9h)
**Purpose**: Establish the complete universe of all streets in San Francisco

**Dataset**: Active Streets (`3psu-pn9h`)
- Contains all active streets in SF
- Provides the base street inventory
- Ensures no streets are missed

**Key Fields**:
- **`street`**: Street name WITHOUT type (e.g., "MISSION", "BRYANT")
- **`street_type`**: Street type only (e.g., "ST", "BLVD", "AVE")
- **`streetname_gc`**: Human-readable full street name (e.g., "Mission St", "Bryant St")
- **`cnn`**: Centerline Network Number - unique identifier
- Status (active/inactive)

**Field Usage Guide for Matching**:
- **For programmatic matching**: Use `street` + `street_type` separately (allows flexible normalization)
- **For display/user queries**: Use `streetname_gc` (human-readable format)
- **For deterministic lookups**: Always use `cnn` as primary key
- **Dataset-specific considerations**:
  - Street Intersections (`pu5n-qu5c`): Uses `streetname` field (equivalent to `street` + `street_type`)
  - Intersection Permutations (`jfxm-zeee`): Uses `streets` field with full names including type
  - Parking Regulations (`hi6h-neyh`): May use various formats - normalize to match Active Streets structure

**Known Data Quality Issues**:
- **Stanyan St Mislabeling**: 3 CNN segments (12076000, 12077000, 12078000) are incorrectly labeled as "STANYAN BLVD" instead of "STANYAN ST"
  - There is no Stanyan Blvd in San Francisco
  - This causes meter matching failures for 4 meters with address ranges 1-99
  - **Workaround**: Apply manual correction during ingestion to normalize "STANYAN BLVD" → "STANYAN ST"
  - **Reference**: See Issue #005 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

### Layer 2: Core Structure - Street Intersections (pu5n-qu5c)
**Purpose**: Generate CNN segments with L/R sides and cross streets

**Dataset**: Street Intersections (`pu5n-qu5c`)
- Fields: `cnn`, `streetname`, `from_st`, `limits`, `theorder`

**Matching Intersections to Active Streets - REQUIRED FIELDS**:
- **`cnn`**: Primary key for deterministic matching to active street segments
- **`streetname`** (or `street`): Secondary identifier for validation and text-based matching
- **Why Both Are Required**:
  - `cnn` provides deterministic matching to street segments (100% accuracy)
  - `streetname` enables validation, user-friendly queries, and cross-referencing
  - Together they ensure complete intersection-to-street mapping with zero ambiguity

**Derived Data**:
- CNN_L (left side CNN)
- CNN_R (right side CNN)
- Street name
- From street (cross street)
- To street (from limits or adjacent segments)
- L side address range
- R side address range
- From CNN (segment start)
- To CNN (segment end)

**Process**:
1. Group by street name
2. Order by `theorder` field
3. Derive segment boundaries from sequential records
4. Extract address ranges from `limits` field
5. Assign L/R CNNs based on segment orientation

### Layer 3: Enrichment - Intersection Permutations (jfxm-zeee)
**Purpose**: Provide CNN mappings for each street at every intersection

**Dataset**: Intersection Permutations (`jfxm-zeee`)
- Contains CNN for EACH street at every intersection
- Handles different orderings of intersection names (e.g., "20th & Bryant" vs "Bryant & 20th")
- Multiple records per intersection (minimum 2, one per street)

**Matching Intersection Permutations to Active Streets - REQUIRED FIELDS**:
- **`cnn`**: Links each permutation record to its corresponding active street segment
- **`streets`**: Contains street names for user queries and validation (e.g., "20TH ST & BRYANT ST")
- **Why Both Are Required**:
  - `cnn` provides the direct link to active street segments in the master reference
  - `streets` enables flexible user queries with different intersection name orderings
  - Each intersection has multiple permutation records (one per street), all requiring CNN matching
  - Without CNN, permutations cannot be linked to the spatial street network

**What it DOES provide**:
- CNN for each street segment at an intersection
- Different permutations of intersection name orderings
- Enables finding all streets at a given intersection

**What it does NOT provide**:
- Street name variations or abbreviations
- Cardinal directions
- Alternative street names or historical names

**Example**: For "20th & Bryant" intersection:
- Record 1: {streets: "20TH ST & BRYANT ST", cnn: "10048000"} ← 20TH ST segment
- Record 2: {streets: "20TH ST & BRYANT ST", cnn: "10049000"} ← BRYANT ST segment
- Record 3: {streets: "BRYANT ST & 20TH ST", cnn: "10048000"} ← Same intersection, different order
- Record 4: {streets: "BRYANT ST & 20TH ST", cnn: "10049000"} ← Same intersection, different order

**Reference**: See [`archive/old_docs/INTERSECTION_DATASETS_COMPLETE_INTEGRATION.md`](../archive/old_docs/INTERSECTION_DATASETS_COMPLETE_INTEGRATION.md) for detailed explanation.

### Historical Note: Fuzzy Matching Abandonment

**Validation Results** (December 2024):
- Fuzzy matching algorithm tested against 113 blockfaces
- **Accuracy: 21.4%** (24 correct out of 112)
- **Root cause:** Street intersections dataset provides only ONE cross street, but blockfaces require TWO for unique identification
- **Decision:** Abandon fuzzy matching entirely. Use deterministic matching only.
- **Reference:** See [`FUZZY_MATCHING_VALIDATION_SUMMARY.md`](../reference/status/FUZZY_MATCHING_VALIDATION_SUMMARY.md)

### Layer 4A: Blockface Geometry - Meter-Calibrated Offsets - ✅ IMPLEMENTED & INTEGRATED

**Implementation Date**: December 30, 2025
**MongoDB Integration Date**: December 30, 2025
**Scripts**:
- [`calibrate_from_existing_blockfaces.py`](calibrate_from_existing_blockfaces.py) - Offset calibration from MongoDB
- [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) - Core ingestion with calibrated offsets (STEP 2.5)
- [`update_synthetic_blockfaces_with_calibration.py`](update_synthetic_blockfaces_with_calibration.py) - MongoDB update script
**Status**: ✅ COMPLETE & PRODUCTION READY

**Purpose**: Generate blockface geometries using THREE-PRIORITY approach with meter-calibrated offsets for synthetic blockfaces

**THREE-PRIORITY Integration Strategy**:
1. **Priority 1**: Deterministic blockfaces from pep9-66vw (general blockface geometry dataset)
2. **Priority 2**: Deterministic blockfaces from mk27-a5x2 (metered blockface geometry dataset)
3. **Priority 3**: Synthetic blockfaces with meter-calibrated offsets (learned from actual meter positions)

**Data Sources**:
- **pep9-66vw** - General blockface geometries (~2,370 segments, 6.9%)
- **mk27-a5x2** - Metered blockface geometries (~24 segments, 0.1%)
- **Meter Calibration** - 34,324 meter samples for offset learning
- **Active Streets** (`3psu-pn9h`) - CNN centerline geometries

**Calibration Process**:
1. **Sample Collection**: Analyzed 34,324 existing blockfaces from MongoDB
2. **Offset Calculation**: Computed perpendicular distance from centerline to blockface edge
3. **Statistical Analysis**: Aggregated by side (L/R) to determine median offsets
4. **Validation**: Verified consistency across samples (std dev ~3m)

**Calibration Results**:
- **Total Samples**: 34,324 blockfaces
- **L Side Offset**: +5.55m median (17,162 samples, std 3.17m)
- **R Side Offset**: -5.55m median (17,162 samples, std 3.53m)
- **Improvement**: 11% more accurate than fixed 5.0m approximation
- **Confidence**: High (consistent medians across large sample size)

**MongoDB Integration Results**:
- **Total Segments**: 34,324 (100% coverage)
- **Deterministic (pep9-66vw)**: 2,370 segments (6.9%) - preserved
- **Deterministic (mk27-a5x2)**: 24 segments (0.1%) - preserved
- **Synthetic (calibrated)**: 31,930 segments (93.0%) - updated with 5.55m offset
- **Update Success Rate**: 100% (0 failures)

**Benefits**:
- ✅ Complete blockface coverage (100% vs previous ~50-60%)
- ✅ Deterministic geometries preserved where available
- ✅ Synthetic geometries use data-driven offsets (not approximations)
- ✅ 11% accuracy improvement over fixed offset
- ✅ Enables precise spatial queries for parking edges
- ✅ Future ingestions automatically use calibrated offsets

**Implementation in Core Ingestion**:
```python
# In ingest_data_cnn_segments.py, STEP 2.5 (lines 542-556)
def generate_offset_geometry(centerline_geo: Dict, side: str, offset_degrees: float = None):
    """
    Uses calibrated offsets learned from actual meter locations.
    Default: 0.00005584 degrees ≈ 5.55 meters at SF latitude
    """
    if offset_degrees is None:
        offset_degrees = 0.00005584  # Calibrated from 34,324 meter samples
    # ... geometry generation logic
```

**Data Structure**:
```python
{
    'cnn': '123000',
    'side': 'L',
    'blockfaceGeometry': LineString,  # Actual parking edge
    # Metadata tracked internally:
    # - Deterministic: from pep9-66vw or mk27-a5x2 (confidence 1.0)
    # - Synthetic: meter-calibrated offset (confidence 0.85)
}
```

**References**:
- Complete Summary: [`BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md`](BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md)
- Issue Resolution: [`BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md`](BLOCKFACE_GEOMETRY_ISSUE_AND_FIX.md)
- Calibration Data: [`blockface_offset_calibration.json`](blockface_offset_calibration.json)

### Layer 4B: Additional Deterministic Blockface Matching (pep9-66vw) - ❌ SCRAPPED

**Decision Date**: December 31, 2025
**Status**: ❌ NOT IMPLEMENTED - Decision documented

**Original Purpose**: Attempt to match additional blockfaces from pep9-66vw dataset beyond the 2,370 already matched in Layer 4A

**Why Scrapped**:

**Cost/Benefit Analysis**:
- **Current Coverage**: 7.0% deterministic (2,394 segments) + 93.0% synthetic (31,930 segments) = 100% total
- **Potential Improvement**: Could increase deterministic coverage from 7.0% to potentially 15-20%
- **Remaining Gap**: 80-85% would still require synthetic geometries
- **Effort Required**: High (complex matching algorithms, validation, testing, deployment)
- **Impact**: Low (synthetic geometries with meter-calibrated offsets already provide acceptable quality)

**Technical Challenges**:
- pep9-66vw dataset has ~50,000 blockface records
- Only 2,370 (4.7%) could be deterministically matched to CNNs using exact text matching
- Remaining ~47,630 blockfaces lack sufficient metadata for deterministic matching
- Street Intersections dataset only provides ONE cross street, but blockfaces require TWO for unique identification
- No fuzzy matching allowed per architecture (100% accuracy requirement)

**Current Solution is Sufficient**:
- Layer 4A THREE-PRIORITY system provides 100% blockface coverage
- Priority 1: Deterministic from pep9-66vw (2,370 segments, 6.9%)
- Priority 2: Deterministic from mk27-a5x2 (24 segments, 0.1%)
- Priority 3: Synthetic with meter-calibrated offsets (31,930 segments, 93.0%)
- Meter-calibrated offsets are 11% more accurate than fixed offsets
- Quality is acceptable for production use

**Decision**: Do not pursue additional deterministic matching from pep9-66vw. The THREE-PRIORITY system in Layer 4A provides complete coverage with acceptable quality.

**Reference**: See Issue #009 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) for complete blockface geometry integration details.

### Layer 5: Regulations - Parking Availability and Restrictions

**Purpose**: Layer parking regulations onto the spatial foundation to provide complete parking information

**Critical Architecture Decision**: Non-metered and metered parking represent different **types of parking availability** with equal priority. Street sweeping is an **absolute prohibition** that overrides all parking availability types.

**SINGLE SOURCE OF TRUTH**: All regulation parsing, normalization, and display formatting is centralized in [`regulation_normalizer.py`](regulation_normalizer.py). This module provides:
- Day/time/duration parsing and formatting
- Regulation display text generation
- Cap color normalization
- Meter schedule prioritization
- Exception suffix standardization ("except permit", "except government permit")
- Complete display logic for all regulation types

See [`CODE_AUDIT_REGULATION_DISPLAY.md`](CODE_AUDIT_REGULATION_DISPLAY.md) for verification that all production code uses this centralized module.

**Regulation Types**:

1. **Parking Availability Types** (Equal Priority - Can Process in Parallel)
   
   **A. Non-Metered Parking Regulations**
   - Time-limited parking (e.g., 2-hour limit)
   - Residential permit parking (RPP zones)
   - General parking restrictions
   - **Duration Standardization**: All time limits stored as integer minutes, displayed as "2hr", "30min", etc.
   - **Dependencies**: Requires CNNs + Blockfaces + Meter locations (for spatial matching)
   - **Processing**: Can process independently once blockfaces are ready

   **B. Metered Parking**
   - Paid parking with rates and time limits
   - Requires payment but allows parking
   - **Internal meter schedule priority**: TOW > ALTERNATE > OP > PRE+FREE
   - **TOW**: No parking allowed at meter during this time (meter-specific schedule)
   - **ALTERNATE**: Different meter rules on certain days (e.g., different rates/limits)
   - **OP**: Standard paid meter operation
   - **PRE+FREE**: Prepay and free periods (same priority, PRE treated as FREE for display)
   - **Duration Standardization**: Meter time limits stored as integer minutes
   - **Dependencies**: Requires CNNs + Blockfaces + Meter locations
   - **Processing**: Schedules and rates can process asynchronously

2. **Absolute Prohibition** (Overrides All Parking Availability)
   
   **Street Sweeping** - ✅ ANALYZED & DOCUMENTED
   - Complete prohibition during specific times
   - Guaranteed tow if parked during sweeping
   - **Overrides ALL parking availability types** (both non-metered and metered)
   - Applies to entire street segment, not just metered areas
   - **Dependencies**: Requires CNNs only
   - **Processing**: Can process independently
   - **Analysis Date**: December 31, 2024
   - **Status**: Ready for integration

**Data Processing Flow**:
When determining parking legality at a specific time:
1. Check street sweeping - is it currently sweeping time? (absolute prohibition)
2. Check parking availability - what type of parking is available?
   - If metered: Check meter schedules (TOW/ALTERNATE/OP/PRE/FREE)
   - If non-metered: Check time limits, RPP requirements, restrictions
3. Display the most restrictive active condition

**Display Logic**:
Show the **most restrictive active condition** to users:
- If street sweeping is active → Show "Street Sweeping - No Parking" (overrides everything)
- Else if metered location:
  - If meter TOW schedule active → Show "Tow-Away - No Parking" (meter-specific)
  - Else if ALTERNATE schedule → Show alternate meter rules (different rates/limits)
  - Else if OP/FREE/PRE → Show "Metered Parking - $X/hour" or "Free Parking"
- Else if non-metered regulations → Show regulation (e.g., "2-hour parking limit")

**Processing Dependencies**:
```
Phase 1: Foundation (Sequential)
├─ Active Streets → CNNs
├─ Blockface Geometries (Deterministic)
├─ Synthetic Blockfaces (Offset generation)
└─ Meter Physical Locations → Augment blockface info

Phase 2: Regulations (Parallel - Independent)
├─ Non-Metered Regulations (needs: CNNs + Blockfaces + Meter locations)
├─ Meter Rules + Rates (needs: CNNs + Blockfaces + Meter locations, can be async)
└─ Street Cleaning (needs: CNNs only, can be async)
```

**Datasets**:
- **Non-metered regulations**: Time-limited parking, RPP zones, general restrictions
- **Metered parking**: Operating schedules from Meter Policies (OP/FREE/PRE/TOW/ALTERNATE)
- **Street cleaning schedules**: Absolute prohibition (overrides all parking availability) - See Layer 5B below

### Layer 5B: Street Cleaning Integration - ✅ ANALYZED & DOCUMENTED

**Analysis Date**: December 31, 2024
**Dataset**: Street Cleaning Schedules (`yhqp-riqs`)
**Status**: ✅ COMPLETE ANALYSIS - Ready for Integration
**Documentation**: [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)

**Purpose**: Integrate street cleaning schedules as absolute prohibitions that override all parking availability types

**Key Statistics** (December 31, 2025):
- Total records: 37,878
- Total CNNs: 12,253 unique
- CNNs with both sides: 10,320 (84.2%)
- CNNs with only one side: 1,933 (15.8%) - Known data quality issue

**Reference:** See [`STREET_CLEANING_INTEGRATION_GUIDE.md`](../reference/guides/STREET_CLEANING_INTEGRATION_GUIDE.md) for complete integration details.
#### Blockface-Level Street Cleaning Aggregation

**Purpose**: Aggregate multiple street cleaning schedules at the CNN+SIDE (blockface) level for user display

**Aggregation Strategy**:

Street cleaning schedules are aggregated **per blockface side** (CNN+SIDE) by **grouping by common time windows** and aggregating days within those time windows.

**Key Principle**: Group by time window first, then aggregate days within each time window.

**Data Structure**:
```python
{
    'cnn': '6113000',
    'side': 'L',
    'streetCleaningAggregation': {
        'has_cleaning': True,
        'schedules': [
            {
                'days': ['Tu', 'Th', 'Su'],
                'from_time': '6:00 AM',
                'to_time': '8:00 AM',
                'weeks': [1, 2, 4],  # Week-of-month pattern
                'holidays': False  # No cleaning on holidays
            }
        ],
        'display_text': 'Street Cleaning Tu, Th, Su 6am-8am except holidays',
        'display_format': 'aggregated',  # 'aggregated' or 'multiple'
        'schedule_count': 3
    }
}
```

**Aggregation Rules**:

1. **Same Time Window**: If all schedules share the same time window (from_time, to_time)
   - Aggregate days into single display: "Street Cleaning M, W, F 8am-10am"
   - Combine week-of-month patterns if consistent

2. **Different Time Windows**: If schedules have different time windows
   - Display as separate lines:
     ```
     Street Cleaning M, W 8am-10am except holidays
     Street Cleaning F 12pm-2pm except holidays
     ```

3. **Holiday Override**: Apply HOLIDAY override logic across all schedules
   - If ANY schedule has HOLIDAY override → Apply to all
   - Display "except holidays" suffix when holidays=0

4. **Week-of-Month Aggregation**:
   - All weeks (1-5): "Every [day]"
   - 2nd & 4th: "2nd & 4th [day]"
   - 1st & 3rd: "1st & 3rd [day]"
   - 1st, 3rd, 5th: "1st, 3rd, 5th [day]"

**Display Priority**:
- Most restrictive schedule shown first
- Combine schedules when possible to reduce visual clutter
- Maximum 3 lines for street cleaning display

**Example Aggregations**:

Single time window, multiple days:
```python
Input: [
    {'day': 'M', 'from': '8am', 'to': '10am', 'holidays': 0},
    {'day': 'W', 'from': '8am', 'to': '10am', 'holidays': 0},
    {'day': 'F', 'from': '8am', 'to': '10am', 'holidays': 0}
]
Output: "Street Cleaning M, W, F 8am-10am except holidays"
```

Multiple time windows:
```python
Input: [
    {'day': 'M', 'from': '8am', 'to': '10am', 'holidays': 0},
    {'day': 'Th', 'from': '12pm', 'to': '2pm', 'holidays': 0}
]
Output: 
    Line 1: "Street Cleaning M 8am-10am except holidays"
    Line 2: "Street Cleaning Th 12pm-2pm except holidays"
```

**Integration Point**: [`regulation_normalizer.py`](regulation_normalizer.py) - Street Cleaning Aggregation Module


**Key Findings**:

**1. Dataset Structure**:
- **Total Records**: 37,878
- **Total CNNs**: 12,253
- **Unique Identifier**: CNN + corridor_side (L/R)
- **100% Week-of-Month Scheduling**: All records use week1-5 fields

**2. Asymmetric Coverage (Issue #1)**:
```
CNNs with BOTH sides: 10,320 (84.2%)
CNNs with ONLY ONE side: 1,933 (15.8%)
```
- **Impact**: CRITICAL - Users won't see restrictions for missing side
- **Solution**: Display only available sides, document incompleteness
- **Verification List**: `street_cleaning_manual_verification.csv`

**3. HOLIDAY Override Pattern (Verified)**:
```
CNN+sides with HOLIDAY override: 172 (1.40%)
Pattern: HOLIDAY entry with holidays=0 overrides days with holidays=1
```
- **Example**: CNN 6113000R has Monday with holidays=1, but HOLIDAY entry with holidays=0 overrides it
- **Result**: NO cleaning on SF's 3 official holidays (Jan 1, Dec 25, Thanksgiving)

**4. Week-of-Month Patterns**:
```
All weeks (1st-5th): 62.8%
2nd & 4th only: 18.4%
1st & 3rd only: 11.6%
1st, 3rd, 5th: 5.9%
```

**5. Holiday Field**:
```
holidays=0 (no cleaning on holidays): 92.7%
holidays=1 (cleaning on holidays): 7.3%
```

**Field Structure**:
```python
{
    'cnn': '6113000',
    'corridor_side': 'L',  # L (Left) or R (Right)
    'fullname': 'Tuesday',  # Day name or "HOLIDAY"
    'weekday': 'Tues',
    'fromhour': 6,  # 0-23
    'tohour': 8,    # 0-23
    'week1': '1',   # 1=active, 0=not active
    'week2': '1',
    'week3': '0',
    'week4': '1',
    'week5': '0',
    'holidays': '0'  # 0=no cleaning on holidays, 1=cleaning occurs
}
```

**Display Format Specification**:

**Template**: `"Street Cleaning {days} {time_range} {holiday_clause}"`

**Components**:
- **Days**: M, Tu, W, Th, F, Sa, Su (comma-separated, no "and")
- **Time Range**: "6am-8am", "12pm-2pm" (12-hour format)
- **Holiday Clause**: " except holidays" (when holidays=0 or HOLIDAY override)
- **Week-of-Month**: "2nd & 4th Thu", "Every Mon", "1st, 3rd, 5th Fri"

**Examples**:
```
CNN 6113000L: "Street Cleaning Tu, Th, Su 6am-8am except holidays"
CNN 6113000R: "Street Cleaning M, W, F, Sa 6am-8am except holidays"
Standard: "Street Cleaning 2nd & 4th Thu 8am-10am except holidays"
All weeks: "Street Cleaning Every Mon 6am-8am except holidays"
```

**Holiday Display Logic**:
```python
def should_skip_holidays(cnn_side_records):
    """
    Determine if 'except holidays' should be shown.
    
    Logic Priority:
    1. If HOLIDAY entry exists → Use HOLIDAY entry's holidays field (special case, 1.40%)
    2. If NO HOLIDAY entry → Use individual day's holidays field (standard case, 98.6%)
    """
    # Check for HOLIDAY entry first (special case)
    has_confirmation = any(
        r.get("fullname") == "HOLIDAY" and str(r.get("holidays")) == "1"
        for r in cnn_side_records
    )
    if has_confirmation:
        return False  # HOLIDAY entry says cleaning occurs on holidays
    
    has_override = any(
        r.get("fullname") == "HOLIDAY" and str(r.get("holidays")) == "0"
        for r in cnn_side_records
    )
    if has_override:
        return True  # HOLIDAY entry says no cleaning on holidays (overrides any holidays=1)
    
    # No HOLIDAY entry (standard case) - use individual day's holidays field
    regular_days = [r for r in cnn_side_records if r.get("fullname") != "HOLIDAY"]
    if regular_days:
        # Most common: all days have same holidays value
        all_skip = all(str(r.get("holidays", "1")) == "0" for r in regular_days)
        all_clean = all(str(r.get("holidays", "1")) == "1" for r in regular_days)
        
        if all_skip:
            return True  # All days have holidays=0
        elif all_clean:
#### Blockface-Level Non-Metered Regulation Aggregation

**Purpose**: Aggregate multiple non-metered parking regulations at the CNN+SIDE (blockface) level for user display

**Aggregation Strategy**:

When a blockface has multiple non-metered regulations (time limits, RPP zones, restrictions), they must be aggregated and prioritized for clear user display.

**Data Structure**:
```python
{
    'cnn': '783420',
    'side': 'R',
    'nonMeteredRegulationAggregation': {
        'has_regulations': True,
        'regulations': [
            {
                'type': 'time-limit',
                'duration_minutes': 120,
                'days': ['M', 'Tu', 'W', 'Th', 'F'],
                'from_time': '8:00 AM',
                'to_time': '6:00 PM',
                'has_rpp_exception': True,
                'display_text': '2hr limit Weekdays 8am-6pm except permit'
            },
            {
                'type': 'no-parking',
                'days': ['Sa', 'Su'],
                'from_time': '3:00 AM',
                'to_time': '6:00 AM',
                'display_text': 'No Parking Sa-Su 3am-6am'
            }
        ],
        'primary_regulation': '2hr limit Weekdays 8am-6pm except permit',
        'regulation_count': 2,
        'has_rpp': True,
        'rpp_areas': ['W']
    }
}
```

**Aggregation Rules**:

1. **Priority Order** (Most to Least Restrictive):
   - No Parking (absolute prohibition)
   - Government Permit only
   - Time-limited with RPP exception
   - Time-limited without RPP
   - No oversized vehicles (informational)

2. **Display Strategy**:
   - **Primary Regulation**: Most restrictive active regulation shown first
   - **Secondary Regulations**: Additional regulations shown below
   - **Maximum Display**: 3 regulation lines per blockface

3. **Time Window Overlap Handling**:
   - If regulations have overlapping time windows → Show most restrictive
   - If regulations have non-overlapping windows → Show all (up to 3)
   - Example:
     ```
     2hr limit Weekdays 8am-6pm except permit
     No Parking Sa-Su 3am-6am
     ```

4. **RPP Exception Consolidation**:
   - If multiple regulations have same RPP exception → Consolidate suffix
   - Use standardized suffix: "except permit" (not "for non-permit holders")
   - Government permits use: "except government permit"

5. **Regulation Type Filtering**:
   - **SKIP**: "Paid + Permit" and "Pay or Permit" (meter data handles these)
   - **INCLUDE**: All other regulation types
   - **INFORMATIONAL**: "No oversized vehicles" (doesn't affect standard car eligibility)

**Display Priority Examples**:

Single time-limited regulation with RPP:
```python
Input: [
    {'type': 'time-limit', 'duration': 120, 'days': 'M-F', 'time': '8am-6pm', 'rpp': True}
]
Output: "2hr limit Weekdays 8am-6pm except permit"
```

Multiple regulations (different time windows):
```python
Input: [
    {'type': 'time-limit', 'duration': 120, 'days': 'M-F', 'time': '8am-6pm', 'rpp': True},
    {'type': 'no-parking', 'days': 'Sa-Su', 'time': '3am-6am'}
]
Output:
    Line 1: "2hr limit Weekdays 8am-6pm except permit"
    Line 2: "No Parking Sa-Su 3am-6am"
```

Overlapping regulations (show most restrictive):
```python
Input: [
    {'type': 'time-limit', 'duration': 120, 'days': 'M-F', 'time': '8am-6pm'},
    {'type': 'no-parking', 'days': 'M-F', 'time': '8am-10am'}  # Overlaps
]
Output:
    Line 1: "No Parking M-F 8am-10am"  # More restrictive
    Line 2: "2hr limit M-F 10am-6pm"   # Adjusted time window
```

**Eligibility Impact**:

Regulations are classified by their impact on parking eligibility for default Curby users (standard car, no permits):

- **BLOCKS PARKING**: No Parking, Government Permit only
- **ALLOWS WITH LIMIT**: Time-limited parking (with or without RPP)
- **INFORMATIONAL ONLY**: No oversized vehicles

**Data Quality Considerations**:

1. **72-Hour RPP Rules**: Filtered out at individual rule level (permit-holder only)
   - Non-permit users have 2-hour limit in RPP areas
   - Filtering happens during ingestion, not at segment level
   - See Issue #010 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

2. **Paid/Permit Duplicates**: Skipped to avoid duplication with meter data
   - "Pay or Permit" (58 records, 0.7%)
   - "Paid + Permit" (3 records, 0.0%)
   - See [`NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md`](NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md)

3. **Manual Overrides**: Applied at STEP 5.4 before regulation aggregation
   - See [`MANUAL_DATA_OVERRIDES_GUIDE.md`](MANUAL_DATA_OVERRIDES_GUIDE.md)
   - See [`manual_data_overrides.json`](manual_data_overrides.json)

**Integration Points**:
- Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.3
- Normalization: [`regulation_normalizer.py`](regulation_normalizer.py) - Non-Metered Regulation Module
- Display: Pre-computed `display_text` field for each regulation
- Test Coverage: [`test_regulation_display_complete.py`](test_regulation_display_complete.py) - 40+ tests

**Benefits**:
- ✅ Clear priority-based display
- ✅ Handles overlapping time windows
- ✅ Consolidates RPP exceptions
- ✅ Filters meter-related duplicates
- ✅ Maximum 3 lines per blockface (reduces clutter)
- ✅ Pre-computed for performance
- ✅ Single source of truth in regulation_normalizer.py

**Reference**:
- Complete Guide: [`NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md`](NON_METERED_REGULATION_COMPLETE_DISPLAY_GUIDE.md)
- Implementation: [`REGULATION_DISPLAY_FINAL_IMPLEMENTATION.md`](REGULATION_DISPLAY_FINAL_IMPLEMENTATION.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) - Layer 5

            return False  # All days have holidays=1
        else:
            # Mixed values (rare) - use first day's value
            return str(regular_days[0].get("holidays", "1")) == "0"
    
    return True  # Default
```

**Integration Strategy**:

**Phase 1: Data Extraction**
```python
def extract_street_cleaning(cnn, side, records):
    """Extract street cleaning for CNN+side."""
    # 1. Filter records for this CNN+side (exclude HOLIDAY from display)
    day_records = [r for r in records
                   if r.get("cnn") == cnn
                   and r.get("corridor_side") == side
                   and r.get("fullname") != "HOLIDAY"]
    
    # 2. Check for HOLIDAY override
    has_override = check_holiday_override(cnn, side, records)
    
    # 3. Extract week-of-month fields
    weeks_active = []
    for week_num in range(1, 6):
        if str(day_records[0].get(f"week{week_num}", '0')) == '1':
            weeks_active.append(week_num)
    
    # 4. Format display
    return format_street_cleaning_display(day_records, weeks_active, has_override)
```

**Phase 2: CNN Master Integration**
```python
def add_street_cleaning_to_cnn_master(cnn_master, street_cleaning_records):
    """Add street cleaning to CNN master dataset."""
    for cnn_side_key, cnn_data in cnn_master.items():
        cnn = cnn_data["cnn"]
        side = cnn_data["side"]
        
        # Get street cleaning display
        display = extract_street_cleaning(cnn, side, street_cleaning_records)
        
        if display:
            cnn_data["street_cleaning"] = {
                "display": display,
                "source": "yhqp-riqs",
                "last_updated": datetime.now().isoformat()
            }
```

**Data Quality Considerations**:

**1. Asymmetric Coverage (15.8%)**:
- **Issue**: 1,933 CNNs have cleaning on only ONE side
- **Impact**: Users won't see restrictions for missing side
- **Solution**: Display only available sides, document in DATA_QUALITY_ISSUES.md
- **Manual Overrides**: Use manual_data_overrides.json for verified corrections

**2. HOLIDAY Override Pattern (1.40%)**:
- **Issue**: 172 CNN+sides use HOLIDAY entries to override holidays=1
- **Impact**: Must check for HOLIDAY entry before determining holiday behavior
- **Solution**: Implement HOLIDAY override logic in display formatting

**3. SF Official Holidays**:
- January 1 (New Year's Day)
- December 25 (Christmas Day)
- 4th Thursday of November (Thanksgiving)

**Benefits**:
- ✅ Complete field structure documented
- ✅ Display format standardized
- ✅ HOLIDAY override pattern understood
- ✅ Week-of-month formatting specified
- ✅ Data quality issues documented
- ✅ Integration strategy defined
- ✅ Ready for implementation

**References**:
- Complete Guide: [`STREET_CLEANING_INTEGRATION_GUIDE.md`](STREET_CLEANING_INTEGRATION_GUIDE.md)
- Data Quality: Issue #1 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)
- Data Quality Log: Issue #013 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)
- Analysis Scripts: [`analyze_street_cleaning_dataset.py`](analyze_street_cleaning_dataset.py), [`analyze_week_fields_correct.py`](analyze_week_fields_correct.py), [`analyze_holiday_override_socrata.py`](analyze_holiday_override_socrata.py)

### Layer 5A: Meter Datasets Integration - ✅ IMPLEMENTED

**Implementation Date**: December 30, 2025
**Script**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6
**Status**: ✅ COMPLETE

**Meter Rate Application**: December 31, 2025
**Script**: [`apply_meter_rates_to_cnn_master.py`](apply_meter_rates_to_cnn_master.py)
**Status**: ✅ RATES APPLIED

**Purpose**: Integrate physical meter locations with base operating schedules and temporal policy modifications

**Four-Dataset Architecture**:

**1. Primary: Parking Meters (8vzz-qzz9)** - ✅ IMPLEMENTED
- Physical meter attributes: `post_id`, `cap_color`, location, CNN
- 38,356 meters total (30,797 active On Street meters)
- **Note**: Does NOT contain `parking_space_id`
- **Inclusion**: ✅ Included in CNN Master (static)
- **Integration**: Address-based matching (PRIMARY) with CNN fallback

**2. Base Schedules: Meter Operating Schedules (6cqg-dxku)** - ✅ IMPLEMENTED
- Permanent/baseline operating schedules
- 29,371 unique postIDs with 72,365 schedule records
- **No temporal fields** - represents stable baseline
- Fields: `post_id`, `schedule_type`, `days_applied`, `from_time`, `to_time`, `time_limit`, `cap_color`
- **Inclusion**: ✅ Included in CNN Master (static)
- **Data Quality**: 21.5% of meters (6,624) lack schedules - handled gracefully
- **Schedule Priority**: TOW > ALTERNATE > OP > PRE+FREE (PRE and FREE have equal priority)
- **Mixed Period Handling**: When user duration spans multiple meter states, validate each period's overlap against that period's time limit. PRE consolidated with FREE for display.

**3. Special Event Areas: Special Event Areas (itv4-r6g6)** - ✅ IMPLEMENTED
- Geospatial boundaries for special event zones (Oracle Park, Chase Center)
- Used to flag meters with dynamic pricing during events
- **Inclusion**: ✅ Spatial join performed
- **Result**: ~2,400 meters flagged (7.9% of total)

**4. Meter Rate Schedules (fwjv-32uk)** - ✅ IMPLEMENTED
- Hourly parking rates for all meters
- 60,485 rate records for 29,379 unique postIDs
- Fields: `post_id`, `days_applied`, `from_time`, `to_time`, `rate`, `rate_type`, `schedule_priority`
- **Inclusion**: ✅ Rates applied to base_schedules in CNN Master (December 31, 2024)
- **Data Quality**: Zero rate conflicts detected (same post_id + days + time with different rates)
- **Coverage**: 109,074 schedules matched (100% of schedules with operating data)

**5. Temporal Modifications: Meter Policies (qq7v-hds4)** - ⏭️ PENDING
- Time-bounded policy modifications and future rollouts
- 1,545 unique postIDs with 50,000 policy records
- **Temporal fields**: `startdate`, `enddate`, `revisiondate`
- **Current Status** (Dec 2024): ALL policies future-dated (start: 2026-01-12, end: 2200-12-31)
- **Inclusion**: ❌ Excluded from CNN Master, store in separate `meter_policies` collection
- **Implementation**: Phase 5 (automated cron job)

**Key Findings from Validation**:
- ✓ 100% of Meter Policies postIDs exist in Parking Meters
- ✓ 100% of Meter Operating Schedules postIDs exist in Parking Meters
- ✓ 100% of Meter Rate Schedules postIDs exist in Parking Meters (29,379 unique)
- ✓ Only 84.3% overlap between Policies and Operating Schedules
- ✓ 243 postIDs in Policies have NO base schedules (likely new meters for 2026)
- ✓ Meter Policies is confirmed as temporal modification system
- ✓ All current policies are future-dated (inactive until Jan 12, 2026)
- ✓ Zero rate conflicts in Meter Rate Schedules (no duplicate rates for same schedule)

**Integration Strategy** - ✅ IMPLEMENTED:

**CNN Master File (Static)**:
```python
def integrate_meters_into_cnn_master():
    """
    ✅ IMPLEMENTED: Include meters and base schedules in CNN Master.
    Exclude temporal policies (separate collection).
    
    Implementation: ingest_data_cnn_segments.py STEP 5.6
    Rate Application: apply_meter_rates_to_cnn_master.py (applied to MongoDB)
    """
    # 1. Load Parking Meters
    meters = fetch_parking_meters()  # 8vzz-qzz9
    
    # 2. Load Base Operating Schedules
    base_schedules = fetch_meter_operating_schedules()  # 6cqg-dxku
    
    # 3. Load Meter Rate Schedules
    rate_schedules = fetch_meter_rate_schedules()  # fwjv-32uk
    
    # 4. Load Special Event Areas
    special_event_areas = fetch_special_event_areas()  # itv4-r6g6
    
    # 5. Match meters to CNN L/R entries (ADDRESS-BASED PRIMARY)
    for meter in meters:
        # Primary: Address-based matching
        cnn_lr_entry = match_meter_by_address(
            meter.street_num,
            meter.street_name
        )
        
        # Fallback: CNN-based matching
        if not cnn_lr_entry:
            cnn_lr_entry = match_meter_by_cnn(meter.cnn)
        
        # 6. Get base schedules for this postID
        schedules = base_schedules.get(meter.post_id, [])
        
        # 7. Apply rates to schedules
        for schedule in schedules:
            rate = match_rate_to_schedule(
                schedule,
                rate_schedules.get(meter.post_id, [])
            )
            if rate:
                schedule['rate'] = rate
        
        # 8. Apply schedule priority hierarchy
        prioritized = prioritize_schedules(schedules)  # TOW > ALTERNATE > OP/FREE/PRE
        
        # 9. Check if in special event area
        is_special_event = check_special_event_area(
            meter.location,
            special_event_areas
        )
        
        # 10. Attach to CNN entry
        cnn_lr_entry.meters.append({
            'post_id': meter.post_id,
            'cap_color': meter.cap_color,
            'location': meter.location,
            'is_special_event': is_special_event,
            'base_schedules': prioritized  # From 6cqg-dxku with rates from fwjv-32uk
        })
    
    # DO NOT include Meter Policies here - separate collection (Phase 5)
```

**Meter Policies Collection (Dynamic)**:
```python
def ingest_meter_policies_cron():
    """
    Separate automated ingestion every 3 days.
    Filters for active policies only.
    """
    all_policies = fetch_meter_policies()  # qq7v-hds4
    
    # Filter for active policies
    today = datetime.now().date()
    active_policies = [p for p in all_policies
                      if p.startdate <= today <= p.enddate]
    
    # Store in separate collection
    db.meter_policies.replace_many(active_policies)
    
    # Currently returns 0 policies (all future-dated)
```

**Runtime Query (Conditional)**:
```python
def get_parking_info(location, user_preferences):
    # 1. Always query street_segments collection
    base_data = db.street_segments.find({"location": {"$near": location}})
    
    # 2. Conditional: Only query policies if needed
    has_meters = any(d.get('meter_post_id') for d in base_data)
    user_wants_metered = user_preferences.include_metered_parking
    
    if has_meters and user_wants_metered:
        # Query meter_policies collection
        meter_post_ids = [d['meter_post_id'] for d in base_data]
        active_policies = db.meter_policies.find({
            "postid": {"$in": meter_post_ids}
        })
        
        # Apply policy overrides to base schedules
        final_data = apply_policy_overrides(base_data, active_policies)
    else:
        final_data = base_data
    
    return final_data
```

**Schedule Types** (from both Operating Schedules and Policies):
- **FREE**: No payment, no restrictions, no cap color
- **PRE**: Prepay allowed (includes free time before enforcement)
- **OP**: Paid operation with time limits, rates, and vehicle restrictions

### Cap Color Normalization and Vehicle Restrictions - ✅ IMPLEMENTED

**Implementation Date**: December 31, 2024
**Module**: [`regulation_normalizer.py`](regulation_normalizer.py) - Part 8: Cap Color Normalization
**Status**: ✅ COMPLETE & PRODUCTION READY

**Complete 6-Color Legend (Revised Dec 31, 2024)**:

| Cap Color | Vehicle Type | Curby User Eligible | Display Text |
|-----------|--------------|---------------------|--------------|
| **BLACK** | Motorcycle only | ❌ NO | "Motorcycle only" |
| **BROWN** | Tour Bus only | ❌ NO | "Tour Bus only" |
| **GREY** | General parking | ✅ YES | "General parking" |
| **GREEN** | General parking | ✅ YES | "General parking" |
| **PURPLE** | Boat Trailer only | ❌ NO | "Boat Trailer only" |
| **RED** | Commercial Vehicles 6+ wheels | ❌ NO | "Commercial Vehicles 6+ wheels" |
| **YELLOW** | Commercial Vehicle | ❌ NO | "Commercial Vehicle" |

**For Curby Users (Standard Cars)**:
- **ELIGIBLE**: GREY, GREEN only
- **INELIGIBLE**: BLACK, BROWN, PURPLE, RED, YELLOW
- **Default Assumption**: Curby users are in standard cars

**Blockface-Level Aggregation (Majority Rule)**:

Cap colors are aggregated at the CNN+SIDE (blockface) level:

- **All meters eligible (GREY/GREEN)** → Block ELIGIBLE for Curby users
- **Majority eligible** → Block ELIGIBLE for Curby users
- **Majority ineligible** → Block INELIGIBLE for Curby users
- **All meters ineligible** → Block INELIGIBLE for Curby users

**Rationale**: Users need to know if they can find ANY parking on a blockface. If majority of meters are restricted, the block is effectively unavailable for Curby users (standard cars).

**Data Structure**:
```python
{
    'cap_color': 'GREY',  # Raw value from dataset
    'cap_color_normalized': {
        'canonical': {
            'color': 'GREY',
            'restriction': 'GENERAL',
            'is_restricted': False,
            'vehicle_type': 'Standard vehicles'
        },
        'display': {
            'restriction_text': 'General parking',
            'user_eligible': True
        }
    }
}
```

**Blockface Aggregation Result**:
```python
{
    'capColorAggregation': {
        'is_restricted': True,
        'restriction_type': 'COMMERCIAL',
        'eligible_meter_count': 2,
        'ineligible_meter_count': 8,
        'meter_count': 10,
        'majority_rule': 'MAJORITY_INELIGIBLE',
        'eligible_for_curby_user': False,
        'restriction_breakdown': {'COMMERCIAL': 5, 'MOTORCYCLE': 3},
        'display_text': 'Majority (8/10) restricted',
        'display_restriction': 'COMMERCIAL'
    }
}
```

**Integration Points**:
- Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6
- Normalization: [`regulation_normalizer.py`](regulation_normalizer.py) lines 932-1100

**Benefits**:
- ✅ Simplified logic (YELLOW and RED both = Commercial)
- ✅ Blockface-level view for parking eligibility
- ✅ Majority rule maximizes user opportunities
- ✅ Standardized display text across all interfaces
- ✅ Single source of truth in regulation_normalizer.py

### TOW and ALTERNATE Schedule Handling - ✅ IMPLEMENTED

**Implementation Date**: December 31, 2025
**Module**: [`regulation_normalizer.py`](regulation_normalizer.py) - Part 9: Meter Schedule Priority
**Status**: ✅ COMPLETE & PRODUCTION READY

**Schedule Priority Hierarchy**:
```
TOW > ALTERNATE > OP > PRE+FREE
```

Note: PRE and FREE have the same priority level (lowest). PRE is treated as FREE for display purposes.

**TOW Schedule Rules (Blockface-Level)**:

1. **All meters have TOW** → Check for overlap with user duration
   - If ANY TOW schedule overlaps user's parking time → Block INELIGIBLE
   - Rationale: No parking available anywhere on block

2. **Majority have TOW** → Use majority rule
   - If majority in TOW during user's time → Block INELIGIBLE
   - Rationale: Most meters unavailable

3. **Mixed (some TOW, some operating)** → Use majority rule
   - If majority are operating → Block ELIGIBLE
   - Rationale: User can likely find an operating meter

**ALTERNATE Schedule Definition**:
- Different meter rules on certain days (NOT alternate side parking)
- Examples:
  - Higher rates during special events ($12/hour vs $4/hour)
  - Different time limits on weekends (4hr vs 2hr)
  - Different restrictions on specific days
- Priority: Higher than OP but lower than TOW

**Data Structure**:
```python
{
    'schedules': [
        {
            'schedule_type': 'TOW',
            'days_applied': 'Thu',
            'from_time': '14:00:00',
            'to_time': '16:00:00',
            'time_limit': None,
            'rate': None,
            'cap_color': None
        },
        {
            'schedule_type': 'ALTERNATE',
            'days_applied': 'Su',
            'from_time': '12:00:00',
            'to_time': '22:00:00',
            'time_limit': 240,
            'rate': '12.00',
            'cap_color': 'GREEN'
        },
        {
            'schedule_type': 'OP',
            'days_applied': 'Mon-Sat',
            'from_time': '09:00:00',
            'to_time': '18:00:00',
            'time_limit': 120,
            'rate': '4.00',
            'cap_color': 'GREEN'
        }
    ]
}
```

**Blockface TOW Aggregation**:
```python
{
    'towScheduleAggregation': {
        'has_tow': True,
        'all_have_tow': False,
        'tow_schedules': [...],  # All TOW schedules for overlap checking
        'meters_with_tow': 3,
        'meters_without_tow': 7,
        'majority_rule': 'OPERATING',
        'blockface_rule': 'MAJORITY_OPERATING',
        'display_text': 'Majority (7/10) are operating'
    }
}
```

**Integration Points**:
- Schedule Prioritization: [`regulation_normalizer.py`](regulation_normalizer.py) `prioritize_meter_schedules()`
- TOW Aggregation: [`regulation_normalizer.py`](regulation_normalizer.py) `aggregate_blockface_tow_schedules()`
- Ingestion: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6

**Benefits**:
- ✅ Schedules always sorted by priority
- ✅ TOW preempts all other meter schedules
- ✅ ALTERNATE schedules properly handled (special event rates, etc.)
- ✅ Blockface-level TOW aggregation with majority rule
- ✅ Time overlap detection for user duration checking

**Benefits**:
- ✅ CNN Master stays static (consistency, performance)
- ✅ Policies updated automatically every 3 days
- ✅ No runtime SFMTA API calls
- ✅ Conditional queries optimize performance
- ✅ Zero cost (MongoDB free tier, Render cron jobs)
- ✅ Ready for Jan 2026 when policies activate

**Reference**: See [`METER_POLICIES_INTEGRATION_ARCHITECTURE.md`](METER_POLICIES_INTEGRATION_ARCHITECTURE.md) for complete implementation guide.

### ALTERNATE Schedules - Non-Day-of-Week Patterns - ✅ ANALYZED

**Analysis Date**: December 31, 2025
**Status**: ✅ COMPLETE ANALYSIS
**Total Patterns**: 7 non-day-of-week patterns identified (371 schedules, 0.51% of total)

**Purpose**: Document special ALTERNATE schedule patterns that activate under specific conditions (events, school days, business hours) rather than standard day-of-week patterns.

#### All Non-Day-of-Week ALTERNATE Patterns

| Pattern | Count | Interpretation | Display Format |
|---------|-------|----------------|----------------|
| **School Days** | 177 (0.24%) | School Days | "Passenger Loading Zone on School Days" |
| **Giants Day** | 52 (0.07%) | Giants Day Games | "Passenger Loading Zone on Giants Day Games" |
| **Giants Night** | 52 (0.07%) | Giants Night Games | "Passenger Loading Zone on Giants Night Games" |
| **Performance** | 50 (0.07%) | Special Event Periods | "Passenger Loading Zone on Special Event Periods" |
| **Posted Events** | 19 (0.03%) | Special Event Periods | "Passenger Loading Zone on Special Event Periods" |
| **Posted Services** | 19 (0.03%) | Service Periods | "Passenger Loading Zone on Service Periods" |
| **Business Hours** | 2 (0.00%) | Business Hours | "Passenger Loading Zone on Business Hours" |

#### Common Characteristics

**ALL 371 non-DOW ALTERNATE schedules share:**
- `schedule_type: "Alternate"`
- `applied_color_rule: "White - Passenger loading zone"`
- `time_limit: "0 minutes"` (no parking allowed)
- `active_meter_status: "M - Active meter installed"`
- **Absolute prohibition** (TOW + VIOLATION) when condition is active

#### Key Implementation Rules

1. **Applied Color Rule Timing**:
   - `applied_color_rule` ONLY applies when `days_applied` condition is met
   - When condition NOT active → Use base Operating Schedule (standard meter operation)
   - When condition IS active → Use ALTERNATE schedule (passenger loading zone)

2. **Two-Line Display Format**:
   ```
   Line 1: Passenger Loading Zone on [interpretation]
   Line 2: All other days [duration] [day range] ($[rate]/hr)
   ```

3. **Example Display**:
   ```
   Line 1: Passenger Loading Zone on School Days
   Line 2: All other days 2hr limit M-F ($2.50/hr)
   ```

4. **No Special Calendar Integration Needed**:
   - System displays both rules to users
   - Users understand when special condition applies
   - No need to determine if event is currently active

#### Data Structure

```python
{
  "post_id": "223-33390",
  "street_and_block": "23RD ST 3300",
  "schedules": [
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
  ]
}
```

#### Interpretation Mapping

```python
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

#### Restriction Level When Active vs Inactive

**When ALTERNATE Condition Active** (e.g., during School Days):
- **Restriction**: Absolute prohibition (TOW + VIOLATION)
- **Type**: Passenger Loading Zone only
- **Consequence**: Vehicle towed if parked
- **Display**: "Passenger Loading Zone on [interpretation]"

**When ALTERNATE Condition Inactive** (e.g., not School Days):
- **Restriction**: Standard metered parking availability
- **Type**: Paid parking with time limits
- **Consequence**: Parking ticket if unpaid
- **Display**: Base Operating Schedule (e.g., "2hr limit M-F ($2.50/hr)")

#### Benefits

- ✅ Clear two-line display format for users
- ✅ No complex calendar integration required
- ✅ Users see all applicable rules
- ✅ Proper restriction classification (absolute prohibition when active, parking availability when inactive)
- ✅ Standardized interpretation overrides
- ✅ Complete coverage of all non-DOW patterns

### Special Event Zone Display Formatting - ✅ IMPLEMENTED

**Implementation Date**: December 31, 2025
**Module**: [`regulation_normalizer.py`](regulation_normalizer.py) - Part 10: Special Event Zone Formatting
**Status**: ✅ COMPLETE & PRODUCTION READY

**Purpose**: Provide specialized display formatting for meters in Oracle Park and Chase Center special event zones with dynamic pricing during events.

#### Zone Definitions

**Three Geospatial Zones**:

1. **Oracle Park Zone** (~1,200 meters)
   - Geospatial boundary from Special Event Areas dataset (itv4-r6g6)
   - Dynamic pricing during Giants games and events
   - Display: "Oracle Park Special Event Zone"

2. **Chase Center Zone** (~1,200 meters)
   - Geospatial boundary from Special Event Areas dataset (itv4-r6g6)
   - Dynamic pricing during Warriors games and concerts
   - Display: "Chase Center Special Event Zone"

3. **Overlap Zone** (meters in BOTH zones)
   - Rare but possible near zone boundaries
   - Display: "Oracle Park & Chase Center Special Event Zone"

**Total Coverage**: ~2,400 meters (7.9% of all on-street meters)

#### Display Format

**Multi-Line Format for Special Event Zones**:

**Line 1**: `[Zone Name] Schedule and Rates may apply. See schedule for details.`
- Word "schedule" is hyperlinked to SFMTA URL
- Oracle Park only: "Oracle Park Schedule and Rates may apply..."
- Chase Center only: "Chase Center Schedule and Rates may apply..."
- Both zones (overlap): "Special Event Schedule and Rates may apply..."

**Line 2**:
- Single schedule (all 7 days): `All Other Days [duration] [days] [time] ($[rate]/hr)`
- Multiple schedules: `All Other Weekdays [duration] [days] [time] ($[rate]/hr)`

**Line 3** (if multiple schedules):
- `All Other Weekends [duration] [days] [time] ($[rate]/hr)`

**Examples**:

Single schedule covering all days:
```
Line 1: Oracle Park Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days 2hr limit Daily 9am-6pm ($4.00/hr)
```

Multiple schedules (Weekdays + Weekends):
```
Line 1: Chase Center Schedule and Rates may apply. See schedule for details.
Line 2: All Other Weekdays 2hr limit M-F 9am-6pm ($2.50/hr)
Line 3: All Other Weekends 4hr limit Sa-Su 12pm-10pm ($3.00/hr)
```

Overlap zone with single schedule:
```
Line 1: Special Event Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days 2hr limit Daily 9am-6pm ($3.00/hr)
```

#### SFMTA Schedule URL

**Link**: https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule

The word "schedule" in Line 1 is hyperlinked to this URL, directing users to:
- Current event dates and times
- Dynamic pricing rates during events
- Base rates when no events active

#### Implementation Logic

```python
class SpecialEventZoneFormatter:
    """Format display for special event zone meters."""
    
    SFMTA_SCHEDULE_URL = 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule'
    
    def format_special_event_display(self,
                                     in_ballpark_zone: bool,
                                     in_arena_zone: bool,
                                     base_schedules: List[Dict]) -> Dict:
        """
        Format multi-line display for meters in special event zones.
        
        Args:
            in_ballpark_zone: True if meter is in Oracle Park zone
            in_arena_zone: True if meter is in Chase Center zone
            base_schedules: List of base operating schedule dicts
        
        Returns:
            {
                'line1': 'Oracle Park Schedule and Rates may apply. See schedule for details.',
                'line2': 'All Other Weekdays 2hr limit M-F 9am-6pm ($2.50/hr)',
                'line3': 'All Other Weekends 4hr limit Sa-Su 12pm-10pm ($3.00/hr)',  # Optional
                'schedule_url': 'https://www.sfmta.com/...',
                'has_special_event': True
            }
        """
        # Determine zone name
        if in_ballpark_zone and in_arena_zone:
            zone_name = "Special Event"
        elif in_ballpark_zone:
            zone_name = "Oracle Park"
        else:
            zone_name = "Chase Center"
        
        # Build Line 1
        line1 = f"{zone_name} Schedule and Rates may apply. See schedule for details."
        
        # Build Line 2 and Line 3 from schedules
        # Single schedule: "All Other Days [schedule]"
        # Multiple schedules: "All Other Weekdays [schedule]" + "All Other Weekends [schedule]"
        line2, line3 = self._format_base_schedule_lines(base_schedules)
        
        return {
            'line1': line1,
            'line2': line2,
            'line3': line3,
            'schedule_url': self.SFMTA_SCHEDULE_URL,
            'has_special_event': True
        }
```

#### Data Structure

```python
{
    'post_id': '123-45678',
    'cap_color': 'GREEN',
    'in_ballpark_zone': True,  # Geospatial flag for Oracle Park
    'in_arena_zone': False,    # Geospatial flag for Chase Center
    'special_event_display': {
        'line1': 'Oracle Park Schedule and Rates may apply. See schedule for details.',
        'line2': 'All Other Weekdays 2hr limit M-F 9am-6pm ($2.50/hr)',
        'line3': 'All Other Weekends 4hr limit Sa-Su 12pm-10pm ($3.00/hr)',
        'schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule',
        'has_special_event': True
    },
    'base_schedules': [
        {
            'days': [0,1,2,3,4],  # M-F
            'duration_minutes': 120,
            'from_time': '9:00 AM',
            'to_time': '6:00 PM',
            'rate': '2.50'
        },
        {
            'days': [5,6],  # Sa-Su
            'duration_minutes': 240,
            'from_time': '12:00 PM',
            'to_time': '10:00 PM',
            'rate': '3.00'
        }
    ]
}
```

#### Integration Points

- **Geospatial Flagging**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6
- **Display Formatting**: [`regulation_normalizer.py`](regulation_normalizer.py) lines 1442-1556
- **Ingestion**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.6

#### Key Design Decisions

1. **No Calendar Integration**: System does NOT determine if event is currently active
   - Users see zone designation and are directed to SFMTA schedule
   - Avoids complex event calendar maintenance
   - SFMTA maintains authoritative event schedule

2. **Geospatial Only**: Zone membership determined by spatial join
   - Not based on schedule fields (those are for non-DOW ALTERNATE patterns)
   - Special Event Areas dataset (itv4-r6g6) provides boundaries

3. **Base Schedules Preserved**: Special event display is ADDITIONAL information
   - Base meter schedules still present in data
   - Users can see both zone designation and standard rates

4. **Two-Line Format**: Consistent with non-DOW ALTERNATE display pattern
   - Line 1: Special condition (zone designation)
   - Line 2: Additional information (SFMTA schedule reference)

#### Benefits

- ✅ Clear zone identification for users
- ✅ No complex event calendar maintenance
- ✅ SFMTA maintains authoritative schedule
- ✅ Consistent two-line display format
- ✅ Geospatial accuracy (spatial join)
- ✅ Handles overlap zones correctly

**Reference**: See [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md) for complete implementation details.

**Reference**: See [`ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md`](ALTERNATE_SCHEDULE_ANALYSIS_SUMMARY.md) for complete analysis and [`non_dow_days_applied_patterns.json`](non_dow_days_applied_patterns.json) for detailed data.

### Regulation Severity & Display Logic

**Critical Architecture**: Regulations are layered from **least to most severe**:

**Severity Hierarchy**:
1. **Non-metered regulations** (Severity 1 - Least Severe)
   - Time-limited parking, RPP zones, general restrictions
   - Impact: You can park with time/permit limits

2. **Metered parking** (Severity 2)
   - Paid parking with rates and time limits
   - **Internal meter schedule priority**: TOW > ALTERNATE > OP > PRE+FREE
   - Impact: You can park if you pay (unless meter TOW active)

3. **Street sweeping** (Severity 3 - Most Severe)
   - Complete prohibition during specific times
   - Overrides ALL regulations including meter TOW
   - Impact: Absolute restriction, guaranteed tow

**Display Logic**: Always show the **most severe active regulation** to users.

**Reference:** See [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md) for complete normalization logic.

## Implementation Plan

### Phase 1: Build Foundation Table
```sql
CREATE TABLE cnn_master_reference (
    -- Primary identifiers
    cnn_segment_id VARCHAR PRIMARY KEY,
    cnn_l VARCHAR,
    cnn_r VARCHAR,
    
    -- Street information
    street_name VARCHAR NOT NULL,
    street_type VARCHAR,
    from_street VARCHAR,
    to_street VARCHAR,
    
    -- Address ranges
    l_from_addr INTEGER,
    l_to_addr INTEGER,
    r_from_addr INTEGER,
    r_to_addr INTEGER,
    
    -- Segment boundaries
    from_cnn VARCHAR,
    to_cnn VARCHAR,
    
    -- Ordering
    segment_order INTEGER,
    
    -- Metadata
    source_dataset VARCHAR,
    confidence_score FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Phase 2: Build Intersection Variations Table
```sql
CREATE TABLE intersection_variations (
    variation_id VARCHAR PRIMARY KEY,
    cnn_segment_id VARCHAR REFERENCES cnn_master_reference(cnn_segment_id),
    
    -- Variations
    street_name_variation VARCHAR,
    from_street_variation VARCHAR,
    to_street_variation VARCHAR,
    
    -- Source
    source_dataset VARCHAR,
    variation_type VARCHAR, -- 'abbreviation', 'alternate', 'historical'
    
    UNIQUE(street_name_variation, from_street_variation, to_street_variation)
);
```

### Phase 3: Add Spatial Layer
```sql
CREATE TABLE cnn_geometry (
    geometry_id VARCHAR PRIMARY KEY,
    cnn_segment_id VARCHAR REFERENCES cnn_master_reference(cnn_segment_id),
    
    -- Geometry
    geometry GEOMETRY(LineString, 4326),
    
    -- Spatial attributes
    length_meters FLOAT,
    orientation_degrees FLOAT,
    
    -- Blockface attributes
    blockface_id VARCHAR,
    globalid VARCHAR,
    
    -- Source
    source_dataset VARCHAR
);
```

### Phase 4: Layer Regulations
```sql
CREATE TABLE cnn_regulations (
    regulation_id VARCHAR PRIMARY KEY,
    cnn_segment_id VARCHAR REFERENCES cnn_master_reference(cnn_segment_id),
    side CHAR(1), -- 'L' or 'R'
    
    -- Regulation details
    regulation_type VARCHAR,
    regulation_text TEXT,
    schedule JSONB,
    
    -- Spatial extent
    from_position FLOAT, -- 0.0 to 1.0 along segment
    to_position FLOAT,
    
    -- Source
    source_dataset VARCHAR,
    source_record_id VARCHAR
);
```

## Data Processing Pipeline

### Step 1: Ingest Active Streets
```python
def ingest_active_streets():
    """
    Load all active streets from 3psu-pn9h
    Creates base street inventory
    """
    # Fetch from Socrata
    # Insert into staging table
    # Validate completeness
```

### Step 2: Process Street Intersections
```python
def process_street_intersections():
    """
    Process pu5n-qu5c to generate CNN segments
    Derives L/R CNNs, address ranges, segment boundaries
    """
    # Group by street name
    # Order by theorder
    # Derive segment boundaries
    # Extract address ranges from limits
    # Assign L/R CNNs
    # Insert into cnn_master_reference
```

### Step 3: Enrich with Intersection Permutations
```python
def enrich_intersection_permutations():
    """
    Process jfxm-zeee to capture all variations
    Links variations to master reference
    """
    # Fetch intersection permutations
    # Match to existing CNN segments
    # Store variations in intersection_variations
    # Update confidence scores
```

### Step 4: Add Spatial Geometry (Deterministic Matching)
```python
def add_spatial_geometry():
    """
    Process pep9-66vw to add geometries using DETERMINISTIC matching only.
    Discard any blockfaces that cannot be matched with 100% certainty.
    """
    blockfaces = fetch_blockface_geometries()
    
    matched_count = 0
    discarded_count = 0
    discarded_records = []
    
    for blockface in blockfaces:
        # Extract street metadata from blockface
        street_name = blockface.get('street_name')
        from_street = blockface.get('from_street')
        to_street = blockface.get('to_street')
        
        # Attempt deterministic match to CNN master reference
        cnn_match = match_blockface_deterministic(
            street_name=street_name,
            from_street=from_street,
            to_street=to_street
        )
        
        if cnn_match:
            # Store geometry for matched CNN segment
            store_geometry(cnn_match.cnn_segment_id, blockface.geometry)
            matched_count += 1
        else:
            # No deterministic match - discard this blockface
            discarded_records.append({
                'globalid': blockface.globalid,
                'street_name': street_name,
                'from_street': from_street,
                'to_street': to_street,
                'reason': 'No deterministic match to CNN master reference'
            })
            discarded_count += 1
    
    # Log results
    log_geometry_integration(
        matched=matched_count,
        discarded=discarded_count,
        discarded_records=discarded_records
    )
    
    # Return statistics
    return {
        'matched': matched_count,
        'discarded': discarded_count,
        'match_rate': matched_count / (matched_count + discarded_count)
    }

def match_blockface_deterministic(street_name, from_street, to_street):
    """
    Deterministic matching for blockfaces to CNN master reference.
    Returns match only if 100% certain, otherwise None.
    """
    # Normalize street names using exact rules
    normalized_street = normalize_street_name(street_name)
    normalized_from = normalize_street_name(from_street)
    normalized_to = normalize_street_name(to_street)
    
    # Query for exact match
    exact_match = query_cnn_master_reference(
        street=normalized_street,
        from_st=normalized_from,
        to_st=normalized_to
    )
    
    if exact_match:
        return exact_match
    
    # Check known variations
    variation_match = query_intersection_variations(
        street=normalized_street,
        from_st=normalized_from,
        to_st=normalized_to
    )
    
    if variation_match and variation_match.is_unambiguous():
        return variation_match
    
    # No deterministic match - return None (blockface will be discarded)
    return None
```

### Step 5: Layer Regulations
```python
def layer_regulations():
    """
    Add parking regulations from various sources
    Links to CNN segments with spatial extent
    """
    # Process each regulation dataset
    # Match to CNN segments
    # Store in cnn_regulations
```

## Matching Algorithms

### For Blockface Integration (Layer 4): Deterministic Only

When matching blockface records to the CNN master reference, we use **deterministic matching only**:

```python
def match_blockface_to_cnn(street_name, from_street, to_street):
    """
    Deterministic matching for blockface integration.
    Returns match only if 100% certain, otherwise None.
    Unmatched blockfaces are discarded.
    """
    # Exact text matching with known variations
    # No fuzzy matching, no probabilistic matching
    # See Step 4 implementation above
```

### For User Queries (Runtime): Flexible Matching

When users query for parking information, we can use more flexible approaches since the CNN master reference is already established:

```python
def match_user_location_to_cnn(lat, lon, street_name=None):
    """
    Match user location to CNN segment for parking lookup.
    Can use spatial proximity since master reference is trusted.
    """
    # 1. Spatial query to find nearby CNN segments
    nearby_segments = query_nearby_cnn_segments(lat, lon, radius=50m)
    
    # 2. If street name provided, filter by street
    if street_name:
        nearby_segments = filter_by_street(nearby_segments, street_name)
    
    # 3. Return closest segment
    return nearest_segment(nearby_segments, lat, lon)
```

**Key Distinction**:
- **Data Integration (Layer 4)**: Deterministic only, discard uncertain matches
- **User Queries (Runtime)**: Can use spatial proximity since foundation is trusted

## Benefits of This Architecture

1. **Completeness**: Starts with complete street inventory (17,162 CNNs)
2. **Accuracy**: Multiple data sources provide validation
3. **Flexibility**: Supports deterministic text matching with spatial fallbacks
4. **Scalability**: Layered approach allows incremental updates
5. **Maintainability**: Clear separation of concerns
6. **Traceability**: Source tracking for all data
7. **Zero Data Loss**: Fallback strategies ensure 100% coverage for critical datasets (e.g., on-street meters)
8. **Data Quality Tracking**: Systematic logging of issues for reconciliation and LLM training
9. **Manual Override System**: Verified corrections for SFMTA dataset gaps (applied at STEP 5.4)

## Special Case: On-Street Parking Meters

### Critical Requirement
**On-street meters CANNOT be discarded** - they represent real parking infrastructure that must be in the system.

### Current Coverage (December 2024)
- **Total On-Street Meters**: 37,421
- **Matchable via CNN**: 37,406 (99.96%)
- **Require Fallback**: 15 (0.04%)

### Meter Matching Strategy

```python
def match_meter_comprehensive(meter):
    """
    Multi-tier matching ensuring 100% coverage of on-street meters.
    """
    # Tier 1: Direct CNN match (99.96% of meters)
    if meter.has_valid_cnn():
        return match_by_cnn(meter.cnn, meter.blockface_id)
    
    # Tier 2: Blockface ID lookup (100% of meters have this)
    metered_bf = lookup_metered_blockface(meter.blockface_id)
    if metered_bf:
        cnn = find_cnn_by_street_and_address(
            metered_bf.street_name,
            metered_bf.from_addr,
            metered_bf.to_addr
        )
        if cnn:
            return match_by_cnn(cnn, meter.blockface_id)
    
    # Tier 3: Spatial proximity (all meters have lat/lon)
    nearest = find_nearest_segment(
        meter.longitude,
        meter.latitude,
        meter.street_name  # Validate
    )
    if nearest:
        log_data_quality_issue("meter_spatial_fallback", meter)
        return nearest
    
    # Tier 4: Manual override table
    if meter.post_id in manual_overrides:
        log_data_quality_issue("meter_manual_override", meter)
        return manual_overrides[meter.post_id]
    
    # Should never reach here for on-street meters
    raise CriticalDataError(f"Cannot match on-street meter: {meter.post_id}")
```

### Key Findings
1. **100% of on-street meters have `blockface_id`** - reliable fallback path
2. **99.96% have valid CNNs** - excellent data quality
3. **15 meters need fallback** - manageable edge cases
4. **Zero data loss** - all meters represented in system

**Reference**: See [`backend/ON_STREET_METER_COVERAGE_REPORT.md`](ON_STREET_METER_COVERAGE_REPORT.md) for detailed analysis.

---

## Manual Override System

### Purpose
Handle verified data corrections for missing or incorrect SFMTA data that cannot be resolved through automated matching.

### Implementation
- **Override File**: [`manual_data_overrides.json`](manual_data_overrides.json) - Stores verified corrections
- **Application Module**: [`apply_manual_overrides.py`](apply_manual_overrides.py) - Applies corrections during ingestion
- **Integration Point**: STEP 5.4 in [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py:794)
- **Traceability**: All overrides marked with `"source": "manual_override"` and verification dates

### Current Overrides

#### Override #1: Missing Street Cleaning - 19th St R 2700-2798
**Issue**: Street cleaning schedule missing from SFMTA dataset despite physical verification
- **Location**: 19th Street, Right (North) side, 2700-2798
- **CNN**: 961000 (same CNN serves both L and R sides)
- **Schedule**: Thursday 12:00 AM - 6:00 AM
- **Verified**: December 4, 2025 (on-site inspection)
- **Pattern**: CNN has L side data but R side missing
- **Documentation**: See Issue #006 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

### Override Process
1. **Discovery**: Data gap identified during ingestion or user report
2. **Verification**: Physical on-site inspection to confirm actual conditions
3. **Documentation**: Add to [`manual_data_overrides.json`](manual_data_overrides.json) with verification details
4. **Logging**: Record in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) and [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)
5. **Application**: Automatically applied during every ingestion at STEP 5.4
6. **Traceability**: All overridden data marked in database for transparency

### Design Principles
- **Verification Required**: All overrides must be physically verified before addition
- **Full Documentation**: Include verification date, verifier, and reason
- **Traceability**: Mark all overridden data with source attribution
- **Accountability**: Track who verified and when
- **Transparency**: Users can see which data came from manual overrides

---

## Duration/Time Limit Standardization - ✅ IMPLEMENTED

**Implementation Date**: December 31, 2025
**Module**: [`regulation_normalizer.py`](regulation_normalizer.py)
**Status**: ✅ COMPLETE & PRODUCTION READY

### Overview

All parking time limits and durations are now standardized across all SFMTA datasets using a centralized parsing and formatting system.

### Canonical Format

**Storage**: Always integer minutes
```python
{
    "duration_minutes": 120,      # Always integer, always minutes
    "has_limit": true,            # Boolean flag
    "is_rpp_72hr": false          # Special flag for 72hr RPP filtering
}
```

**Display**: Pre-computed human-readable strings
```python
{
    "duration": "2hr",            # Singular units, no spaces
    "duration_long": "2 hour limit"  # Verbose version
}
```

### Dataset-Specific Handling

**Parking Regulations (hi6h-neyh)**:
- Field: `hrlimit` (hours as string or float)
- Examples: "2", "0.5", "72"
- Special case: 72hr RPP filtered out (permit-holder only)

**Meter Schedules (6cqg-dxku)**:
- Field: `time_limit_minutes` (integer minutes)
- Examples: 120, 30, 240

**Meter Policies (qq7v-hds4)**:
- Field: `timelimitminutes` (integer minutes)
- Examples: 120, 30, 240

### Display Format Rules

- **< 60 minutes**: Show minutes (e.g., "30min", "45min")
- **≥ 60 minutes**: Show hours (e.g., "1hr", "2hr", "2.5hr")
- **No limit**: "No" (short) or "No time limit" (long)
- **Units**: Singular ("hr", "min"), no spaces

### 72-Hour RPP Special Handling

**Rule**: 72-hour limits apply to RPP permit holders only
**Implementation**: Filter out at individual rule level during ingestion
- Non-permit users have 2-hour limit in RPP areas
- Filtering happens in [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) lines 354-390
- Segments with 72hr RPP rules keep other rules (not filtered at segment level)

### Integration Points

**Core Ingestion** ([`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)):
- Lines 354-390: Parking regulation matching with duration parsing
- Pre-computes `durationMinutes`, `hasLimit`, `displayDuration`, `displayDurationLong`

**Normalization Module** ([`regulation_normalizer.py`](regulation_normalizer.py)):
- Lines 537-632: `DurationParser` class
- Lines 639-715: `DurationFormatter` class
- Lines 722-861: `normalize_regulation()` function
- Lines 887-929: Convenience functions

**Test Coverage** ([`test_duration_standardization.py`](test_duration_standardization.py)):
- 48 tests covering all parsing, formatting, and integration scenarios
- 100% pass rate

### Benefits

✅ **Consistency**: Single source of truth for all duration logic
✅ **Performance**: Pre-computed display strings (no runtime formatting)
✅ **Accuracy**: Handles fractional hours (0.5hr = 30min)
✅ **User Safety**: 72hr RPP rules filtered to prevent confusion
✅ **Maintainability**: Centralized logic, easy to update

**Reference**: See [`DURATION_STANDARDIZATION_COMPLETE.md`](DURATION_STANDARDIZATION_COMPLETE.md) for complete implementation details.

---

## Data Quality Tracking

### Systematic Logging
All data quality issues discovered during ingestion are logged in [`backend/DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md) for:

1. **Internal Documentation**: Track issues across ingestion cycles
2. **Reconciliation**: Identify patterns and systemic problems
3. **Triage**: Prioritize fixes based on severity and frequency
4. **LLM Training**: Export issues as training data for validation models

### Log Entry Format
```json
{
  "issue_id": "001",
  "date": "2024-12-29",
  "dataset": "parking_meters",
  "type": "missing_required_field",
  "severity": "low",
  "count": 14,
  "percentage": 0.04,
  "sample_records": [...],
  "workaround": "use_blockface_id_fallback",
  "status": "open"
}
```

### Benefits
- **Historical Tracking**: See trends over time
- **Automated Checks**: Integrate into ingestion pipeline
- **LLM Training**: Build domain-specific validation models
- **Documentation**: Never forget edge cases between ingestions

---

## Next Steps

1. **Explore datasets**: Examine schemas of all three foundation datasets ✓
2. **Design ETL pipeline**: Build data ingestion and processing scripts
3. **Create database schema**: Implement tables and indexes
4. **Build matching algorithms**: Implement deterministic matching with fallbacks ✓
5. **Validate results**: Test against known CNN IDs ✓
6. **Document API**: Create clear interface for CNN lookups
7. **Implement data quality logging**: Integrate into ingestion pipeline
8. **Create manual override system**: Handle known edge cases

## Success Metrics

- **Coverage**: % of SF streets in master reference (Target: 100%)
- **Accuracy**: % of correct CNN matches in validation (Target: 100% for matched records)
- **Completeness**: % of segments with all required fields (Target: 100% for critical fields)
- **Variation Coverage**: # of street name variations captured (Target: All known variations)
- **Meter Coverage**: % of on-street meters matched (Target: 100%, Current: 99.96% direct + 0.04% fallback)
- **Data Quality**: # of issues logged per ingestion (Target: Trend downward)
- **Blockface Coverage**: % of blockfaces deterministically matched (Expected: 70-85%)