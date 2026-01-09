m
# CURBY Architecture Analysis

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

---

## Technology Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **UI Library:** shadcn/ui + Tailwind CSS
- **Maps:** Leaflet + OpenStreetMap
- **State Management:** React hooks (useState, useEffect)
- **Build Tool:** Vite

### Infrastructure
- **Hosting:** Vercel (frontend), MongoDB Atlas (database)
- **CI/CD:** GitHub Actions
- **Monitoring:** MongoDB Atlas monitoring
- **Backup:** Automated daily backups

---

---

## 14. Future Architecture: CNN Master Reference System

### Current Limitation: Unreliable Fuzzy Matching

**Validation Results** (December 2024):
- Fuzzy matching algorithm tested against 113 blockfaces with known CNN IDs
- **Accuracy: 21.4%** (24 correct matches out of 112 parsed records)
- Root cause: Street intersections dataset (`pu5n-qu5c`) only provides ONE cross street, but blockfaces require TWO cross streets (from/to) for unique identification

**Decision**: Abandon fuzzy matching entirely. Use deterministic matching only.

### Proposed Solution: Layered CNN Master Reference with Deterministic Matching

Build a comprehensive CNN reference table through progressive data layering, then match blockfaces using **deterministic matching only**:

#### Layer 1: Foundation - Active Streets (`3psu-pn9h`)
- Establish complete universe of all SF streets
- Ensures 100% street coverage
- Base inventory for all subsequent layers

#### Layer 2: Core Structure - Street Intersections (`pu5n-qu5c`)
- Generate CNN_L and CNN_R for each segment
- Derive from/to streets and segment boundaries
- Extract L/R address ranges from `limits` field
- Order segments using `theorder` field

#### Layer 3: Enrichment - Intersection Permutations (`jfxm-zeee`)
- Provide CNN for each street at every intersection (multiple records per intersection)
- Handle different orderings of intersection names (e.g., "20th & Bryant" vs "Bryant & 20th")
- Enable finding all street segments at a given intersection
- **Note**: Does NOT contain street name variations, abbreviations, or cardinal directions
- **Purpose**: Intersection-to-CNN mapping, not street name normalization

**Matching to Active Streets - REQUIRED FIELDS**:
- **`cnn`**: Links each permutation record to its corresponding active street segment
- **`streets`**: Contains street names for user queries (e.g., "20TH ST & BRYANT ST")
- Both fields are required: CNN for deterministic matching, streets for flexible user queries

#### Layer 4A: Blockface Geometry - Meter-Calibrated Offsets - ✅ IMPLEMENTED & INTEGRATED
- **Implementation Date**: December 30, 2025
- **MongoDB Integration Date**: December 30, 2025
- **Status**: ✅ COMPLETE & PRODUCTION READY
- THREE-PRIORITY blockface integration: deterministic (pep9-66vw + mk27-a5x2) + synthetic (meter-calibrated)
- Calibrated from 34,324 existing blockfaces in MongoDB
- L Side: +5.55m median offset (17,162 samples), R Side: -5.55m median offset (17,162 samples)
- **100% Coverage**: All 34,324 segments have blockface geometries
  - Deterministic: 2,394 segments (7.0%) from pep9-66vw and mk27-a5x2
  - Synthetic: 31,930 segments (93.0%) with meter-calibrated offsets
- Core ingestion updated: [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) STEP 2.5
- MongoDB update script: [`update_synthetic_blockfaces_with_calibration.py`](backend/update_synthetic_blockfaces_with_calibration.py)
- Complete summary: [`BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md`](backend/BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md)

#### Layer 4B: Blockface Spatial Data (`pep9-66vw`) - Optional Enhancement
- Match blockfaces to CNN master reference using **deterministic matching only**
- Use exact text matching: street name + from/to cross streets
- Leverage intersection variations table for known alternatives
- **Discard any blockfaces that cannot be deterministically matched**
- Spatial geometry used for validation, not primary matching
- No fuzzy matching, no probabilistic algorithms

#### Layer 5: Regulations - Parking Rules (Severity-Based Layering)
- Layer all parking regulations onto spatial foundation using **severity-based ordering**
- Link regulations to specific CNN segments and sides
- Maintain regulation history and changes

**Critical Architecture**: Regulations are layered from **least to most severe**:

**Severity Hierarchy**:
1. **Non-metered regulations** (Severity 1 - Least Severe)
   - Time-limited parking, RPP zones, general restrictions
   - Impact: You can park with time/permit limits

2. **Metered parking** (Severity 2)
   - Paid parking with rates and time limits
   - **Internal meter schedule priority**: TOW > ALTERNATE > OP > PRE+FREE
   - **TOW**: No parking at meter during this schedule (meter-specific)
   - **ALTERNATE**: Different meter rules on certain days (e.g., different rates/limits)
   - **OP**: Standard paid meter operation
   - **PRE+FREE**: Prepay and free periods (equal priority, PRE treated as FREE for display)
   - Impact: You can park if you pay (unless meter TOW schedule active)

3. **Street sweeping** (Severity 3 - Most Severe)
   - Complete prohibition during specific times
   - Applies to entire street segment (not just metered areas)
   - Overrides ALL regulations including meter TOW schedules
   - Impact: Absolute restriction, guaranteed tow

**Display Logic**: Always show the **most severe active regulation** to users at any given time.

#### Layer 5B: Street Cleaning Integration - ✅ ANALYZED (December 31, 2025)

**Status**: ✅ Complete Analysis, Ready for Integration
**Dataset**: Street Cleaning Schedules (yhqp-riqs)
**Documentation**: [`backend/STREET_CLEANING_INTEGRATION_GUIDE.md`](backend/STREET_CLEANING_INTEGRATION_GUIDE.md)

**Key Statistics**:
- Total records: 37,878
- Total CNNs: 12,253
- CNNs with both sides: 10,320 (84.2%)
- CNNs with only one side: 1,933 (15.8%) - **Data Quality Issue**

**Week-of-Month Scheduling**:
- 100% of records use week1-5 binary fields
- Display format: "2nd & 4th Thu" (ordinal numbers)
- Most common: All weeks (62.8%), 2nd & 4th (18.4%), 1st & 3rd (11.6%)

**Holiday Logic** (Simplified - Verified Dec 31, 2025):
- HOLIDAY entry only special when it **contradicts** a day's holidays=1
- Override case: 172 CNN+sides (1.40%) where HOLIDAY=0 overrides days=1
- Otherwise: Use consistent holidays value from days
- SF Holidays: Jan 1, Dec 25, Thanksgiving

**Display Format**:
```
Street Cleaning {days} {time_range} {holiday_clause}
Examples:
- "Street Cleaning 2nd & 4th Thu 8am-10am except holidays"
- "Street Cleaning Every Mon 6am-8am except holidays"
- "Street Cleaning Tu, Th, Su 6am-8am except holidays"
```

**Data Quality Issue**: 15.8% asymmetric coverage (1,933 CNNs missing opposite side)
- Verification list: `street_cleaning_manual_verification.csv`
- Solution: Display only available side, use manual override system
- Reference: Issue #1 in [`backend/DATA_QUALITY_ISSUES.md`](backend/DATA_QUALITY_ISSUES.md)

**Analysis Scripts**:
- [`analyze_street_cleaning_dataset.py`](backend/analyze_street_cleaning_dataset.py)
- [`analyze_week_fields_correct.py`](backend/analyze_week_fields_correct.py)
- [`verify_holiday_consistency.py`](backend/verify_holiday_consistency.py)

### Implementation Benefits

1. **100% Accuracy**: Deterministic matching ensures no false positives
2. **Zero Data Loss for Critical Datasets**: 100% coverage of on-street meters (37,421 meters)
3. **Data Quality Tracking**: Systematic logging in [`backend/DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md)
4. **Complete Foundation**: All SF streets represented in master reference (17,162 CNNs)
5. **Variation Handling**: All street name permutations captured in Layer 3
6. **Maintainability**: Clear data lineage and source tracking
7. **User Trust**: Users can rely on deterministic results

### Migration Path

**Phase 1**: Build CNN master reference tables (Layers 1-3)
**Phase 2**: Integrate spatial geometry (Layer 4)
**Phase 3**: Migrate existing regulations to new structure (Layer 5)
**Phase 4**: Implement hybrid matching algorithm (text + spatial)
**Phase 5**: Validate against current system and deploy

### Expected Outcomes

- **Matching Accuracy**: 100% for matched records (vs current 21.4%)
- **Blockface Coverage**: ✅ 100% with THREE-PRIORITY integration (34,324 segments)
  - Deterministic: 2,394 segments (7.0%) - confidence 1.0
  - Synthetic (meter-calibrated): 31,930 segments (93.0%) - confidence 0.85
- **Meter Coverage**: 100% of on-street meters (99.96% direct CNN + 0.04% fallback)
- **Foundation Coverage**: 100% of SF streets in master reference (17,162 CNNs)
- **Performance**: Sub-50ms queries with proper indexing
- **Data Quality**: Systematic tracking with [`DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md)
- **Maintainability**: Clear data architecture with source tracking

### Special Handling: On-Street Meters

**Critical Requirement**: On-street meters CANNOT be discarded - they represent real parking infrastructure.

**Current Status** (December 2024):
- Total on-street meters: 37,421
- Matchable via CNN: 37,406 (99.96%)
- Require fallback: 15 (0.04%)
- **100% have blockface_id** - provides reliable fallback path

**Multi-Tier Matching Strategy**:
1. **Tier 1** (99.96%): Direct CNN matching
2. **Tier 2**: Blockface ID → Metered Blockfaces → street/address matching
3. **Tier 3**: Spatial proximity using lat/lon coordinates
4. **Tier 4**: Manual override table for known edge cases

**Result**: Zero data loss - all on-street meters represented in system.

**Reference**: See [`backend/ON_STREET_METER_COVERAGE_REPORT.md`](backend/ON_STREET_METER_COVERAGE_REPORT.md)

**Known Data Quality Issue - Stanyan St Mislabeling**:
- 4 meters on Stanyan St (669-00020, 669-00030, 669-00010, 669-00040) cannot match to CNN
- Root cause: 3 CNN segments (12076000, 12077000, 12078000) are incorrectly labeled as "STANYAN BLVD" instead of "STANYAN ST" in SFMTA Active Streets dataset
- There is no Stanyan Blvd in San Francisco - entire street is Stanyan St
- CNN 12076000 contains critical low address ranges (L:2-98 / R:1-99) needed for these meters
- **Solution**: Manual override to normalize "STANYAN BLVD" → "STANYAN ST" during ingestion
- **Reference**: See Issue #005 in [`backend/DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md)

**Reference**: See [`backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md) for detailed implementation plan.

---

## 15. Meter Datasets Integration Architecture

### Overview
Three datasets work together to provide complete meter parking information: physical meter locations, base operating schedules, and temporal policy modifications.

**Critical Context**: Metered parking is **Severity Level 2** in the regulation hierarchy, positioned between non-metered regulations (Level 1) and street sweeping (Level 3). Street sweeping overrides all meter schedules including meter TOW schedules.

### Implementation Status

**✅ IMPLEMENTED** (December 30, 2025)
- Full meter integration into CNN Master file completed
- Script: [`backend/generate_cnn_master_with_full_meter_integration.py`](backend/generate_cnn_master_with_full_meter_integration.py)
- Meters + operating schedules + special event flags embedded directly into CNN L/R entries
- Address-based matching (PRIMARY) with CNN fallback for maximum accuracy

### Data Sources

**Primary: Parking Meters (8vzz-qzz9)**
- Physical meter attributes: `post_id`, `cap_color`, location, CNN
- 38,356 meters total (30,797 active On Street meters)
- **Note**: Does NOT contain `parking_space_id`
- **Integration**: ✅ Embedded in CNN Master file

**Base Schedules: Meter Operating Schedules (6cqg-dxku)**
- Permanent/base operating schedules for meters
- 29,371 unique postIDs with 72,365 schedule records
- **No temporal fields** - represents stable baseline schedules
- Fields: `post_id`, `schedule_type`, `days_applied`, `from_time`, `to_time`, `time_limit`, `cap_color`
- **Integration**: ✅ Embedded in CNN Master file
- **Data Quality Issue**: 21.5% of active meters (6,624) lack schedules - see Issue #007 in [`DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md)

**Meter Rate Schedules (fwjv-32uk)** - ✅ IMPLEMENTED (December 31, 2025)
- Hourly parking rates for all meters
- 60,485 rate records for 29,379 unique postIDs
- Fields: `post_id`, `days_applied`, `from_time`, `to_time`, `rate`, `rate_type`, `schedule_priority`
- **Integration**: ✅ Rates applied to base_schedules in CNN Master
- **Data Quality**: Zero rate conflicts detected
- **Coverage**: 109,074 schedules matched (100% of schedules with operating data)
- **Script**: [`apply_meter_rates_to_cnn_master.py`](backend/apply_meter_rates_to_cnn_master.py)
- **Documentation**: [`METER_RATE_APPLICATION_SUMMARY.md`](backend/METER_RATE_APPLICATION_SUMMARY.md)

**Special Event Areas: Special Event Areas (itv4-r6g6)**
- Geospatial boundaries for special event zones (Oracle Park, Chase Center)
- Used to flag meters with dynamic pricing during events
- **Integration**: ✅ Spatial join performed, ~2,400 meters flagged
- **Result**: 7.9% of meters identified as special event meters

**Temporal Modifications: Meter Policies (qq7v-hds4)**
- Time-bounded policy modifications and future rollouts
- 1,545 unique postIDs with 50,000 policy records
- **Critical**: Contains `parkingspaceid`, `startdate`, `enddate`, `revisiondate`
- **Current Status** (Dec 2024): ALL policies are future-dated (start: 2026-01-12, end: 2200-12-31)
- **Integration**: ❌ NOT in CNN Master - stored in separate `meter_policies` collection (dynamic updates)

### Key Findings

**Validation Results** (December 2025):
- ✓ 100% of postIDs in Meter Policies exist in Parking Meters
- ✓ 100% of postIDs in Meter Operating Schedules exist in Parking Meters
- ✓ 100% of postIDs in Meter Rate Schedules exist in Parking Meters (29,379 unique)
- ✓ Meter Policies is a temporal modification system (all currently future-dated)
- ✓ Meter Operating Schedules has no date fields (permanent baseline)
- ✓ Only 84.3% overlap between Policies and Operating Schedules
- ✓ 243 postIDs in Policies have NO base schedules (likely new meters for 2026)
- ✓ Zero rate conflicts in Meter Rate Schedules (no duplicate rates for same schedule)

### Schedule Types (Within Severity Level 2 - Metered Parking)

**Important**: All meter schedules are Severity Level 2, but within metered parking there is a priority order: TOW > ALTERNATE > OP > PRE+FREE (PRE and FREE have equal priority)

1. **TOW**: NO PARKING ALLOWED at meter during this schedule
   - Meter-specific schedule type (not a separate regulation category)
   - Highest priority within meter schedules
   - Still Severity 2 (overridden by street sweeping which is Severity 3)

2. **ALTERNATE**: Different meter rules on certain days
   - Different rates, time limits, or restrictions apply on specific days
   - NOT alternate side parking - means alternate rules/rates
   - Example: Higher rates during special events, different time limits on weekends
   - Still Severity 2 (overridden by street sweeping)

3. **OP (Paid Operation)**: Standard metered parking
   - Has `timelimitminutes` (e.g., 30 minutes)
   - Has `hourlyrate` (varies by time of day)
   - **Has `capcolor`** - vehicle restrictions apply ONLY during OP hours
   - Yellow cap = Commercial vehicles only
   - Red cap = Vehicles with 6+ wheels only
   - Still Severity 2 (overridden by street sweeping)

4. **FREE**: No payment, no time restrictions, **no vehicle restrictions**
   - Cap color field is empty
   - Anyone can park during this window
   - Still Severity 2 (overridden by street sweeping)

5. **PRE (Prepay)**: Users can prepay before enforcement begins
   - **Critical**: Prepaid time includes free time before enforcement
   - Cap color field is empty (no vehicle restrictions)
   - Example: Prepay at 8 AM for 1 hour, meter starts at 9 AM → shows 2 hours paid
   - Still Severity 2 (overridden by street sweeping)

**Regulation Hierarchy Context**:
- Street sweeping (Severity 3) overrides ALL meter schedules (including meter TOW)
- Meter schedules (Severity 2) override non-metered regulations (Severity 1)
- Within meter schedules: TOW > ALTERNATE > OP > PRE+FREE

### Policy-Level Cap Color (Critical Understanding)

**Cap color is policy-specific, not meter-specific:**
- **OP schedules**: Have cap color populated (e.g., "Yellow") for vehicle restrictions
- **FREE/PRE schedules**: Have NO cap color (empty) - no vehicle restrictions

**Example: PostID 218-40030**
- Monday 7:00-12:00 OP: Yellow cap (commercial only during paid hours)
- Monday 12:00-15:00 OP: Yellow cap (commercial only)
- Monday 15:00-18:00 OP: Yellow cap (commercial only)
- Monday 18:00-24:00 FREE: (no cap color - anyone can park)
- Monday 0:00-4:30 FREE: (no cap color - anyone can park)

### Integration Architecture

**Data Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│ CNN Master File (Static - Weekly/Monthly Refresh)          │
│ - Parking Meters (8vzz-qzz9): Physical locations           │
│ - Meter Operating Schedules (6cqg-dxku): Base schedules    │
│ - Does NOT include Meter Policies (temporal)               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ MongoDB Collection: meter_policies (Dynamic - Every 3 days)│
│ - Meter Policies (qq7v-hds4): Temporal modifications       │
│ - Filtered: startdate <= TODAY <= enddate                  │
│ - Currently empty (all policies future-dated until 2026)   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Runtime Query (Conditional)                                 │
│ 1. Query CNN Master (always)                               │
│ 2. IF (area has meters AND user wants metered parking)     │
│    THEN query meter_policies collection                    │
│ 3. Merge active policies with base schedules               │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Strategy:**

**CNN Master File (Static)** - ✅ IMPLEMENTED:
1. ✅ Include Parking Meters (8vzz-qzz9) - physical locations
2. ✅ Include Meter Operating Schedules (6cqg-dxku) - base schedules
3. ✅ Include Special Event Areas (itv4-r6g6) - spatial flagging
4. ❌ Exclude Meter Policies (qq7v-hds4) - temporal modifications (separate collection)
5. Refresh: Weekly or when base data changes

**Matching Strategy** - ✅ IMPLEMENTED:
- **Primary**: Address-based matching (street_num + street_name)
- **Fallback**: CNN-based matching for meters without addresses
- **Result**: 97-98% match rate expected
- **Schedule Priority**: TOW > ALTERNATE > OP > PRE+FREE

**Meter Policies Collection (Dynamic)**:
1. Separate MongoDB collection: `meter_policies`
2. Automated ingestion every 3 days via cron job
3. Filter on ingestion: `startdate <= TODAY <= enddate`
4. Currently returns 0 active policies (all future-dated)
5. Will populate after January 12, 2026

**Runtime Query Logic with Severity-Based Display**:
```python
def get_parking_info(location, user_preferences, current_datetime):
    # Always query CNN Master
    base_data = db.cnn_master.find({"location": {"$near": location}})
    
    # Collect all active regulations with severity
    all_regulations = []
    
    for segment in base_data:
        # Add non-metered regulations (Severity 1)
        for rule in segment.get('rules', []):
            if is_active_at_time(rule, current_datetime):
                all_regulations.append({
                    'type': rule['type'],
                    'severity': get_severity(rule['type']),
                    'data': rule
                })
        
        # Add metered parking if applicable (Severity 2)
        has_meters = segment.get('meters')
        if has_meters and user_preferences.include_metered_parking:
            active_policies = db.meter_policies.find({
                "postid": {"$in": [m['post_id'] for m in segment['meters']]}
            })
            meter_schedule = apply_policy_overrides(segment['meters'], active_policies)
            if meter_schedule:
                all_regulations.append({
                    'type': 'metered',
                    'severity': 2,
                    'data': meter_schedule
                })
    
    # Sort by severity (highest first) and return most severe
    if all_regulations:
        all_regulations.sort(key=lambda x: x['severity'], reverse=True)
        return all_regulations[0]  # Most severe active regulation
    
    return None

def get_severity(regulation_type):
    """Map regulation type to severity level"""
    severity_map = {
        'street-sweeping': 3,      # Most severe - street-level absolute restriction
        'metered': 2,              # Includes TOW/ALTERNATE/OP/PRE+FREE meter schedules
        'time-limit': 1,
        'rpp-zone': 1,
        'parking-regulation': 1    # Least severe
    }
    return severity_map.get(regulation_type, 1)
```

**Benefits**:
- ✅ CNN Master stays static (fast, consistent)
- ✅ Policies updated automatically every 3 days
- ✅ No runtime SFMTA API calls
- ✅ Conditional queries optimize performance
- ✅ Zero cost (MongoDB free tier, Render cron jobs)

**Reference**: See [`backend/METER_POLICIES_INTEGRATION_ARCHITECTURE.md`](backend/METER_POLICIES_INTEGRATION_ARCHITECTURE.md) for complete implementation guide.

---

## 18. Regulation Normalization and Cap Color System

### Overview
Complete standardization of ALL parking regulation parsing, normalization, and display formatting across all SFMTA datasets.

**Implementation Date**: December 31, 2025
**Module**: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py) - **SINGLE SOURCE OF TRUTH**
**Documentation**: [`backend/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](backend/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md)
**Status**: ✅ COMPLETE & PRODUCTION READY

**Critical Architecture Decision**: ALL regulation parsing, formatting, and display logic is centralized in `regulation_normalizer.py`. This module handles:
- Day/time parsing and formatting for all datasets
- Duration/time limit standardization
- Cap color normalization and aggregation
- Meter schedule prioritization (TOW > ALTERNATE > OP > PRE+FREE)
- Special event zone display formatting
- Non-metered regulation display formatting
- Exception suffix standardization ("except permit", "except government permit")

**Integration Points**:
- Core Ingestion: [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) lines 16-25
- Test Suite: [`test_regulation_display_complete.py`](backend/test_regulation_display_complete.py) - 476 lines, 100% pass rate
- Code Audit: [`CODE_AUDIT_REGULATION_DISPLAY.md`](backend/CODE_AUDIT_REGULATION_DISPLAY.md) - Verified architecture cleanliness

### Special Event Zone Meters (Geospatial)

**Count**: ~2,400 meters (7.9% of total)
**Zones**: Oracle Park, Chase Center, overlap areas
**Identification**: Spatial join with Special Event Areas dataset (itv4-r6g6)

**Display Format**:
```
Line 1: [Zone Name] Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days [duration] [days] [time] ($[rate]/hr)
Line 3: All Other Weekends [duration] [days] [time] ($[rate]/hr) [if multiple schedules]
```

**Examples**:
```
Single schedule:
Line 1: Oracle Park Schedule and Rates may apply. See schedule for details.
Line 2: All Other Days 2hr limit Daily 9am-6pm ($4.00/hr)

Multiple schedules:
Line 1: Chase Center Schedule and Rates may apply. See schedule for details.
Line 2: All Other Weekdays 2hr limit M-F 9am-6pm ($2.50/hr)
Line 3: All Other Weekends 4hr limit Sa-Su 12pm-10pm ($3.00/hr)
```

**SFMTA Schedule URL**: https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule
- Word "schedule" in Line 1 is hyperlinked to this URL

### Non-DOW ALTERNATE Schedules (Condition-Based)

**Count**: 371 schedules (0.51% of total)
**Patterns**: 7 distinct types identified

| Pattern | Count | % | Interpretation |
|---------|-------|---|----------------|
| School Days | 177 | 0.24% | School Days |
| Giants Day | 52 | 0.07% | Giants Day Games |
| Giants Night | 52 | 0.07% | Giants Night Games |
| Performance | 50 | 0.07% | Special Event Periods |
| Posted Events | 19 | 0.03% | Special Event Periods |
| Posted Services | 19 | 0.03% | Service Periods |
| Business Hours | 2 | 0.00% | Business Hours |

**Common Characteristics**:
- `schedule_type: "Alternate"`
- `applied_color_rule: "White - Passenger loading zone"`
- `time_limit: "0 minutes"` (no parking when active)
- Severity 3 (TOW + VIOLATION) when condition active
- Severity 1 (standard meter) when condition inactive

**Display Format**:
```
Line 1: Passenger Loading Zone on [interpretation]
Line 2: All other days [duration] [days] ($[rate]/hr)
```

### Complete Cap Color Legend

**6-Color System** (Revised December 31, 2024):

| Cap Color | Vehicle Type | Curby User Eligible | Display Text |
|-----------|--------------|---------------------|--------------|
| **BLACK** | Motorcycle only | ❌ NO | "Motorcycle only" |
| **BROWN** | Tour Bus only | ❌ NO | "Tour Bus only" |
| **GREY** | General parking | ✅ YES | "General parking" |
| **GREEN** | General parking | ✅ YES | "General parking" |
| **PURPLE** | Boat Trailer only | ❌ NO | "Boat Trailer only" |
| **RED** | Commercial 6+ wheels | ❌ NO | "Commercial Vehicles 6+ wheels" |
| **YELLOW** | Commercial Vehicle | ❌ NO | "Commercial Vehicle" |

**For Curby Users (Standard Cars)**:
- **ELIGIBLE**: GREY, GREEN only
- **INELIGIBLE**: BLACK, BROWN, PURPLE, RED, YELLOW
- **Default Assumption**: Curby users are in standard cars

### Blockface-Level Cap Color Aggregation

Cap colors are aggregated at the CNN+SIDE (blockface) level using majority rule:

- **All meters eligible (GREY/GREEN)** → Block ELIGIBLE for Curby users
- **Majority eligible** → Block ELIGIBLE for Curby users
- **Majority ineligible** → Block INELIGIBLE for Curby users
- **All meters ineligible** → Block INELIGIBLE for Curby users

**Rationale**: Users need to know if they can find ANY parking on a blockface. If majority of meters are restricted, the block is effectively unavailable for Curby users (standard cars).

### Meter Schedule Priority Hierarchy

Within Severity Level 2 (Metered Parking), schedules are prioritized:

```
TOW > ALTERNATE > OP > PRE+FREE
```

**Note**: PRE and FREE have equal priority (lowest). PRE is treated as FREE for display purposes.

**Schedule Types**:
1. **TOW** (Highest Priority) - No parking allowed at meter during this time
2. **ALTERNATE** - Different meter rules on certain days (special events, different rates)
3. **OP** (Paid Operation) - Standard metered parking with rates and time limits
4. **PRE** (Prepay) - Users can prepay before enforcement begins
5. **FREE** (Lowest Priority) - No payment required, no restrictions

### Implementation Points

**Core Module**: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py)
- Part 8: Cap Color Normalization (lines 936-1194)
- Part 9: Meter Schedule Priority (lines 1196-1433)
- Part 10: Special Event Zone Display (lines 1435-1621)

**Integration**: 
- Ingestion: [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) STEP 5.6
- Generation: [`backend/generate_cnn_master_with_full_meter_integration.py`](backend/generate_cnn_master_with_full_meter_integration.py) Step 8

**Data Files**:
- Analysis: [`backend/ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md`](backend/ALTERNATE_SCHEDULES_COMPLETE_ANALYSIS.md)
- Data: [`backend/non_dow_days_applied_patterns.json`](backend/non_dow_days_applied_patterns.json)
- CSV: [`backend/non_dow_days_applied_patterns.csv`](backend/non_dow_days_applied_patterns.csv)

### Benefits

**For Users**:
- ✅ Clear understanding of all applicable rules
- ✅ Zone-specific messaging for special events
- ✅ Know when special restrictions apply
- ✅ Understand vehicle eligibility (cap colors)
- ✅ Can plan parking accordingly

**For System**:
- ✅ Simple implementation (no calendar integration for non-DOW)
- ✅ No external dependencies
- ✅ Complete information display
- ✅ Standardized interpretation overrides
- ✅ Proper severity classification
- ✅ Single source of truth in regulation_normalizer.py

**Reference**: See [`backend/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](backend/REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md) and Issue #011 in [`backend/DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md) for complete details.


---

## 13. Conclusion

### Architecture Strengths

1. **Complete Coverage:** 100% of San Francisco streets represented
2. **Performance:** 70-80% faster than runtime processing
3. **Scalability:** Pre-computed data scales with queries, not complexity
4. **Accuracy:** Multi-point geometric analysis for side determination
5. **Cost-Effective:** $0 AI interpretation cost (free tier)
6. **Maintainable:** Clear separation of concerns, well-documented
7. **Data Quality Resilience:** Manual override system handles SFMTA dataset gaps
8. **Meter Policy Integration:** Policy-level vehicle restrictions with time-based enforcement

### Evolution from Spaghetti to Structure

**Historical Challenges:**
- Multiple incomplete datasets with gaps (e.g., missing street cleaning records)
- Runtime spatial joins causing performance issues
- Inconsistent side determination
- Missing blockface geometries (92.6% coverage gap)
- Ambiguous regulation text requiring manual interpretation
- SFMTA data quality issues requiring manual verification

**Current Solution:**
- CNN-based architecture achieving 100% coverage
- Pre-computed data at ingestion time
- Deterministic geometric algorithms
- Synthetic blockface generation for missing geometries
- AI-powered interpretation with quality assurance
- **Manual override system** for verified data corrections (applied at STEP 5.4)

### Data Flow Summary

```
SFMTA Open Data (10 datasets)
    ↓
Ingestion Pipeline (6 steps, ~30-45 min)
    ↓
MongoDB (34,292 enriched segments)
    ↓
FastAPI (spatial queries with 2dsphere index)
    ↓
Frontend (React + Leaflet)
    ↓
User (real-time parking legality)
```

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total Segments** | 34,292 (2 per CNN) |
| **Coverage** | 100% of SF streets |
| **Database Size** | ~500MB |
| **Query Time** | 20-50ms (500m radius) |
| **Ingestion Time** | 30-45 minutes |
| **AI Cost** | $0 (free tier) |
| **Unique Regulations** | ~500 (from 7,800) |
| **Blockface Coverage** | ✅ 100% (THREE-PRIORITY: 7.0% deterministic + 93.0% meter-calibrated) |
| **Blockface Segments** | 34,324 (2,394 deterministic + 31,930 synthetic) |

### Recommendations for Future Development

#### Priority 1: CNN Master Reference System (Q1 2025)
**Status**: Architecture designed, validation complete (21.4% accuracy with current fuzzy matching)

Implement the layered CNN Master Reference Architecture to achieve 95%+ matching accuracy:
1. Build foundation tables from Active Streets (`3psu-pn9h`)
2. Process Street Intersections (`pu5n-qu5c`) for CNN segments
3. Enrich with Intersection Permutations (`jfxm-zeee`)
4. Integrate spatial geometry from Blockface data (`pep9-66vw`)
5. Migrate regulations to new structure

**Expected Impact**:
- Matching accuracy: 21.4% → 100% (for matched records)
- Blockface coverage: ~70-85% (deterministically matched only)
- Meter coverage: 100% (99.96% direct + 0.04% fallback)
- Eliminates fuzzy matching entirely
- Complete street name variation coverage in master reference
- Enables deterministic CNN lookups with zero false positives
- Systematic data quality tracking for reconciliation and LLM training

**Reference**: [`backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md)

#### Priority 2: Performance & Scalability
1. **Real-Time Updates:** Implement webhook listeners for SFMTA data changes
2. **Caching Layer:** Add Redis for frequently accessed segments
3. **Mobile Optimization:** Reduce payload size with field projection

#### Priority 3: Feature Enhancements
1. **Historical Tracking:** Store regulation changes over time
2. **Predictive Analytics:** ML models for parking availability
3. **User Feedback Loop:** Crowdsource data quality improvements

#### Priority 4: Expansion
1. **Multi-City Expansion:** Generalize architecture for other cities using CNN Master Reference pattern

---

## 16. Day/Time Normalization System

### Overview
Centralized day/time parsing and formatting system that handles all SFMTA dataset variations with consistent output formats.

**Implementation Date**: December 31, 2025
**Module**: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py)
**Documentation**: [`backend/DAY_TIME_NORMALIZATION_GUIDE.md`](backend/DAY_TIME_NORMALIZATION_GUIDE.md)

---

## 17. Duration/Time Limit Standardization System

### Overview
Centralized duration parsing and formatting system that standardizes all parking time limits across SFMTA datasets.

**Implementation Date**: December 31, 2025
**Module**: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py)
**Documentation**: [`backend/DURATION_STANDARDIZATION_COMPLETE.md`](backend/DURATION_STANDARDIZATION_COMPLETE.md)
**Status**: ✅ COMPLETE & PRODUCTION READY

### Key Features

**Single Source of Truth**:
- All duration parsing logic centralized in `regulation_normalizer.py`
- Consistent behavior across all datasets
- Pre-computed display strings at ingestion time

**Dataset-Specific Adapters**:
- Parking Regulations (`hi6h-neyh`): `hrlimit` field - hours as string/float ("2", "0.5", "72")
- Meter Schedules (`6cqg-dxku`): `time_limit_minutes` field - integer minutes (120, 30, 240)
- Meter Policies (`qq7v-hds4`): `timelimitminutes` field - integer minutes (120, 30, 240)

**Canonical Format**:
```python
{
  "canonical": {
    "duration_minutes": 120,      # Always integer minutes
    "has_limit": true,            # Boolean flag
    "is_rpp_72hr": false          # Special flag for 72hr RPP filtering
  },
  "display": {
    "duration": "2hr",            # Short format
    "duration_long": "2 hour limit"  # Verbose format
  }
}
```

**Display Format Rules**:
- **< 60 minutes**: Show minutes (e.g., "30min", "45min")
- **≥ 60 minutes**: Show hours (e.g., "1hr", "2hr", "2.5hr")
- **No limit**: "No" (short) or "No time limit" (long)
- **Units**: Singular ("hr", "min"), no spaces
- **Fractional hours**: Supported (0.5hr = 30min, 1.5hr = 90min)

### 72-Hour RPP Special Handling

**Rule**: 72-hour limits apply to RPP permit holders only
**Implementation**: Filter out at individual rule level during ingestion
- Non-permit users have 2-hour limit in RPP areas
- Filtering happens in [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) lines 354-390
- Segments with 72hr RPP rules keep other rules (not filtered at segment level)
- `is_rpp_72hr` flag set to `true` for tracking

### Integration Points

**Core Ingestion** ([`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)):
- Lines 354-390: Parking regulation matching with duration parsing
- Pre-computes `durationMinutes`, `hasLimit`, `displayDuration`, `displayDurationLong`

**Normalization Module** ([`regulation_normalizer.py`](backend/regulation_normalizer.py)):
- Lines 537-632: `DurationParser` class with dataset adapters
- Lines 639-715: `DurationFormatter` class with display rules
- Lines 722-861: `normalize_regulation()` function
- Lines 887-929: Convenience functions (`parse_duration()`, `format_duration()`)

**Deprecated Modules**:
- [`deterministic_parser.py`](backend/deterministic_parser.py): `_parse_duration()` marked deprecated
- [`display_utils.py`](backend/display_utils.py): Duration formatting removed

**Test Coverage** ([`test_duration_standardization.py`](backend/test_duration_standardization.py)):
- 48 tests covering all parsing, formatting, and integration scenarios
- 100% pass rate

### Benefits

1. **Consistency**: Same parsing logic across all datasets
2. **Performance**: Pre-computed display strings (no runtime formatting)
3. **Maintainability**: Single point of change for duration logic
4. **User Safety**: 72hr RPP rules filtered to prevent confusion
5. **Accuracy**: Handles fractional hours and edge cases correctly
6. **UX**: Consistent abbreviations across frontend

**Reference**: See [`backend/DURATION_STANDARDIZATION_COMPLETE.md`](backend/DURATION_STANDARDIZATION_COMPLETE.md) for complete implementation details.

### Key Features

**Single Source of Truth**:
- All day/time parsing logic centralized in one module
- Consistent behavior across all datasets
- Pre-computed display strings at ingestion time

**Dataset-Specific Adapters**:
- Street Cleaning (`yhqp-riqs`): `weekday` field - "Th", "Mon", "TUES"
- Parking Regulations (`hi6h-neyh`): `days` field - "MON-FRI", "DAILY", "SCHOOL DAYS"
- Meter Schedules (`6cqg-dxku`): `days_applied` field - "Mo-Su", "Mo-Fr"
- Manual Overrides: `weekday` field - "Thursday", "Monday-Friday"

**Canonical Format**:
```python
{
  "canonical": {
    "days": [0, 1, 2, 3, 4],  # 0=Monday, 6=Sunday
    "time_start": 480,         # Minutes from midnight
    "time_end": 600
  },
  "display": {
    "days": "Weekdays",        # Smart overrides: Daily, Weekdays, Weekends
    "time": "8:00 AM-10:00 AM"
  }
}
```

**Smart Day Overrides**:
- "Daily" (all 7 days)
- "Weekdays" (Mon-Fri)
- "Weekends" (Sat-Sun)
- "School Days" (Mon-Fri with school context)
- Minimal abbreviations: M, Tu, W, Th, F, Sa, Su (1-2 letters)

### Integration Points

**Core Ingestion** ([`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)):
- Lines 354-390: Parking regulation matching
- Lines 604-631: Street sweeping matching
- Pre-computes `displayDays` and `displayTime` fields

**Manual Overrides** ([`apply_manual_overrides.py`](backend/apply_manual_overrides.py)):
- Lines 80-110: Override application
- Generates display strings at override time

**Deprecated Modules**:
- [`deterministic_parser.py`](backend/deterministic_parser.py): `_parse_days()`, `parse_time_to_minutes()` marked deprecated
- [`display_utils.py`](backend/display_utils.py): Day/time functions removed, only street/address formatting remains

### Benefits

1. **Consistency**: Same parsing logic across all datasets
2. **Performance**: Pre-computed display strings (no runtime formatting)
3. **Maintainability**: Single point of change for day/time logic
4. **UX**: Consistent abbreviations and smart overrides across frontend

**Reference**: See [`backend/DAY_TIME_NORMALIZATION_GUIDE.md`](backend/DAY_TIME_NORMALIZATION_GUIDE.md) for complete implementation details.

---

## Appendix A: File Structure

### Backend Core Files
```
backend/
├── main.py                          # FastAPI application & API endpoints
├── models.py                        # Pydantic data models
├── ingest_data_cnn_segments.py      # Main ingestion pipeline (applies overrides at STEP 5.4)
├── regulation_normalizer.py         # Day/time normalization (centralized)
├── display_utils.py                 # Street/address formatting only
├── deterministic_parser.py          # DEPRECATED: Use regulation_normalizer instead
├── restriction_interpreter.py       # AI Worker (LLM interpretation)
├── restriction_judge.py             # AI Judge (quality assurance)
├── apply_manual_overrides.py        # Manual data corrections system
└── manual_data_overrides.json       # Known data quality fixes (verified corrections)
```

### Frontend Core Files
```
frontend/src/
├── utils/
│   ├── sfmtaDataFetcher.ts         # API client & data transformation
│   ├── ruleEngine.ts               # Legality evaluation logic
│   ├── ruleFormatter.ts            # Display formatting
│   └── rppEvaluator.ts             # RPP zone logic
├── components/
│   ├── MapView.tsx                 # Leaflet map component
│   ├── BlockfaceDetail.tsx         # Segment detail modal
│   ├── ParkingNavigator.tsx        # Main UI container
│   └── TimeControls.tsx            # Duration picker
└── types/
    └── parking.ts                  # TypeScript interfaces
```

### Documentation Files
```
├── CURBY_ARCHITECTURE_ANALYSIS.md   # This document
├── Backend-dev-plan.md              # Development history
├── DOCUMENTATION_SUMMARY.md         # Quick reference
├── backend/README.md                # Backend setup guide
├── frontend/README.md               # Frontend setup guide
└── backend/DATA_ARCHITECTURE_UPDATED.md  # Data model details
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **CNN** | Centerline Network Number - unique identifier for street segments |
| **Blockface** | One side of a street segment between two intersections |
| **GlobalID** | Unique identifier in blockface geometry dataset (GUID format) |
| **2dsphere** | MongoDB geospatial index type for spherical geometry |
| **Cross-product** | Vector operation used to determine left/right side |
| **RPP** | Residential Permit Parking zone |
| **SFMTA** | San Francisco Municipal Transportation Agency |
| **Socrata** | Open data platform used by SFMTA |
| **Worker-Judge** | Two-stage LLM pipeline for quality assurance |
| **Synthetic Blockface** | Generated geometry from centerline offset |

---

## Appendix C: Related Documentation

### Architecture & Design
- [`backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md`](backend/CNN_MASTER_REFERENCE_ARCHITECTURE.md) - **NEW**: Layered CNN reference system design
- [`backend/FUZZY_MATCHING_VALIDATION_SUMMARY.md`](backend/FUZZY_MATCHING_VALIDATION_SUMMARY.md) - **NEW**: Validation results and analysis
- [`backend/ON_STREET_METER_COVERAGE_REPORT.md`](backend/ON_STREET_METER_COVERAGE_REPORT.md) - **NEW**: Meter matching analysis (99.96% coverage)
- [`backend/DATA_QUALITY_LOG.md`](backend/DATA_QUALITY_LOG.md) - **NEW**: Data quality tracking system
- [`backend/DAY_TIME_NORMALIZATION_GUIDE.md`](backend/DAY_TIME_NORMALIZATION_GUIDE.md) - **NEW**: Centralized day/time parsing system
- [`backend/DATA_ARCHITECTURE_UPDATED.md`](backend/DATA_ARCHITECTURE_UPDATED.md) - Current data model
- [`CURBY_ENHANCEMENT_PLAN_FINAL.md`](CURBY_ENHANCEMENT_PLAN_FINAL.md) - Future enhancements
- [`backend/PARKING_REGULATION_INTERPRETATION_SYSTEM.md`](backend/PARKING_REGULATION_INTERPRETATION_SYSTEM.md) - AI system design

### Implementation Guides
- [`backend/README.md`](backend/README.md) - Backend setup & API docs
- [`frontend/README.md`](frontend/README.md) - Frontend setup & development
- [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md) - Production deployment

### Data Quality
- [`backend/DATA_QUALITY_ISSUES.md`](backend/DATA_QUALITY_ISSUES.md) - Known issues & workarounds
- [`GEOMETRY_FIX_SUMMARY.md`](GEOMETRY_FIX_SUMMARY.md) - Geometry correction process

### Performance & Optimization
- [`backend/BENCHMARK_LOG.md`](backend/BENCHMARK_LOG.md) - Performance benchmarks
- [`backend/COST_OPTIMIZATION_REPORT.md`](backend/COST_OPTIMIZATION_REPORT.md) - LLM cost analysis
- [`GEMINI_FREE_TIER_STRATEGY.md`](GEMINI_FREE_TIER_STRATEGY.md) - AI cost optimization

### Historical Context
- [`archive/old_docs/`](archive/old_docs/) - Evolution of architecture decisions
- [`Backend-dev-plan.md`](Backend-dev-plan.md) - Development timeline
- [`DOCUMENTATION_SUMMARY.md`](DOCUMENTATION_SUMMARY.md) - Quick reference guide

---

**Document Version:** 1.0
**Last Updated:** January 1, 2026
**Author:** Architecture Analysis
**Status:** Complete
