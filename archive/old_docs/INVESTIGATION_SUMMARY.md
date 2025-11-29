# Database Join Investigation - Complete Summary

**Date**: November 27-28, 2024  
**Investigator**: Roo (AI Assistant)  
**Issue**: Parking regulations not joining to blockfaces

---

## Problem Statement

While the system successfully ingested street sweeping schedules (914 rules), parking regulations from dataset `hi6h-neyh` were not being attached to blockfaces (0 rules attached). The user requested investigation into why regulations were not being applied to each side of the street.

---

## Investigation Process

### Phase 1: Initial Analysis
- Examined ingestion code in `ingest_data.py`
- Checked database collections for parking regulations
- Found regulations were being stored but not joined to blockfaces

### Phase 2: Root Cause Discovery
1. **Missing CNN Fields**: Parking regulations lack CNN identifiers (unlike street sweeping)
2. **Function Bug**: Line 324 called `get_side_of_street()` with wrong number of parameters
3. **Field Mapping Error**: Used non-existent field names (`time_limit` vs `hrlimit`)

### Phase 3: Data Coverage Analysis
- Discovered only 7.4% of streets have blockface geometries (148 of 2,007 CNNs)
- Found CNN 1046000 (20th St between York-Bryant) missing blockface data
- Realized 92.6% of streets cannot display regulations under current architecture

### Phase 4: Architecture Evaluation
- Compared synthetic blockface generation vs CNN-based segments
- Analyzed pros/cons of each approach
- Recommended CNN-based architecture for 100% coverage

---

## Technical Fixes Implemented

### Fix 1: Spatial Join for Parking Regulations

**Location**: `backend/ingest_data.py` lines 282-359

**Before**: 
```python
# Tried CNN-based join (doesn't work - regs have no CNN)
for bf in cnn_to_blockfaces_index.get(cnn, []):
    # This never matched
```

**After**:
```python
# Spatial join using geometric distance
for bf in all_blockfaces:
    distance = reg_shape.distance(bf_shape)
    if distance < 0.0005:  # ~50 meters
        reg_side = get_side_of_street(centerline_geo, reg_geo)
        if reg_side == bf_side:
            bf["rules"].append(regulation)
```

### Fix 2: Function Call Correction

**Location**: `backend/ingest_data.py` line 324

**Before**:
```python
reg_side = get_side_of_street(centerline_geo, reg_geo, f"regulation near {bf.get('streetName')}")
```

**After**:
```python
reg_side = get_side_of_street(centerline_geo, reg_geo)
```

### Fix 3: Field Mapping Correction

**Location**: `backend/ingest_data.py` lines 344-354

**Before**:
```python
{
    "timeLimit": row.get("time_limit"),  # doesn't exist
    "permitArea": row.get("rpp_area"),   # doesn't exist
    "description": row.get("street_parking_description")  # doesn't exist
}
```

**After**:
```python
{
    "regulation": row.get("regulation"),
    "timeLimit": row.get("hrlimit"),
    "permitArea": row.get("rpparea1") or row.get("rpparea2"),
    "days": row.get("days"),
    "hours": row.get("hours"),
    "fromTime": row.get("from_time"),
    "toTime": row.get("to_time"),
    "details": row.get("regdetails"),
    "exceptions": row.get("exceptions")
}
```

**Result**: 136 parking regulations successfully attached to 61 blockfaces

---

## Critical Discovery: Data Coverage Gap

### Findings

**Blockface Coverage**:
- Total CNNs in database: 2,007
- CNNs with blockface geometries: 148 (7.4%)
- CNNs WITHOUT blockface geometries: 1,859 (92.6%)

**20th Street Specific**:
- Total CNN segments: 17
- With blockfaces: 1 (CNN 1055000)
- Without blockfaces: 16 (including CNN 1046000)

**User's Test Case**:
- **Expected**: CNN 1046000 (20th between York-Bryant)
- **Actual**: CNN 1055000 (different block, ~911 meters away)
- **Problem**: CNN 1046000 has no blockface geometry

### Verification

Street sweeping data confirms CNN 1046000 exists:
- CNN 1046000, Side L: Tuesday 9-11am
- CNN 1046000, Side R: Thursday 9-11am
- Limits: "York St - Bryant St"

This data exists in `street_cleaning_schedules` collection but cannot be displayed because no blockface geometry exists.

---

## Architecture Decision

### Option A: Synthetic Blockfaces (NOT CHOSEN)

**Concept**: Generate blockface geometries by offsetting centerlines

**Pros**:
- Quick to implement
- Works with existing frontend
- Extends current architecture

**Cons**:
- Inaccurate (offsets are guesses)
- Creates synthetic data
- Computationally expensive
- Misleading to users

### Option B: CNN-Based Street Segments (APPROVED)

**Concept**: Use CNN + Side as primary identifier, not blockface geometry

**Pros**:
- 100% coverage (all 2,007 CNNs × 2 sides = 4,014 segments)
- Uses authoritative SFMTA data
- Matches source data structure
- No synthetic data
- More maintainable

**Cons**:
- Requires refactoring
- Frontend updates needed
- Migration complexity

**Decision**: Approved by user for implementation

---

## Enhanced Parking Regulation Matching Algorithm

### The Challenge

Parking regulations have:
- ✅ Geometry (LineString along curb)
- ❌ No CNN field
- ❌ No side field

Must determine which CNN segment and which side each regulation applies to.

### Solution: Multi-Point Sampling

```python
def match_regulation_to_segment(regulation_geo, centerline_geo, segment_side):
    """
    1. Check distance to centerline (<50m)
    2. Sample 3 points along regulation line (25%, 50%, 75%)
    3. For each point, calculate which side of centerline
    4. Use majority vote to determine side
    5. Match if sides align
    """
    sample_points = [0.25, 0.5, 0.75]
    side_votes = {"L": 0, "R": 0}
    
    for position in sample_points:
        point = reg_line.interpolate(position, normalized=True)
        cross_product = calculate_side(point, centerline)
        side_votes["L" if cross_product > 0 else "R"] += 1
    
    determined_side = "L" if side_votes["L"] > side_votes["R"] else "R"
    return determined_side == segment_side
```

### Why Multi-Point?

- Single point can be affected by road curves, GPS errors
- Multiple points provide robust determination
- Handles irregular street geometries
- Reduces false positives

---

## Implementation Plan

### Phase 1: Core Data Model (1-2 days)
- Create `StreetSegment` model in `models.py`
- Generate segments for all CNNs (L & R sides)
- Migrate existing blockface geometries to segments

### Phase 2: Rule Matching (2-3 days)
- **Street Sweeping**: Direct CNN + side match (EASY)
- **Parking Regulations**: Multi-point spatial + side (COMPLEX)
- **Meters**: CNN + location inference (MEDIUM)

### Phase 3: Testing & Validation (1 day)
- Validate CNN 1046000 shows correct data
- Verify 100% coverage achieved
- Sample validation of regulation accuracy

### Phase 4: API & Frontend Updates (2-3 days)
- Update API endpoints for segments
- Modify frontend components
- Update map visualization

**Total Timeline**: 5-7 days

---

## Expected Results

### After Migration

**Coverage**:
- ✅ 4,014 street segments (2,007 CNNs × 2 sides)
- ✅ 100% coverage vs current 7.4%

**CNN 1046000 Specifically**:
- ✅ Side L: Tuesday 9-11am sweeping + parking regulations
- ✅ Side R: Thursday 9-11am sweeping + parking regulations
- ✅ FromStreet: "YORK ST", ToStreet: "BRYANT ST"

**Rule Distribution**:
- ✅ >1,800 street sweeping rules (direct CNN match)
- ✅ 400-600 parking regulations (spatial + side match)
- ✅ 5,790 meters properly distributed

---

## Documents Created

### Investigation & Analysis
1. `GEOSPATIAL_JOIN_ANALYSIS.md` - Technical analysis of join issues
2. `FIX_SUMMARY.md` - Summary of technical fixes
3. `SPATIAL_JOIN_FIX_SUMMARY.md` - Spatial join implementation details
4. `TESTING_GUIDE.md` - Testing procedures
5. `INVESTIGATION_FINDINGS.md` - Detailed findings (draft)

### Architecture & Planning
6. `ARCHITECTURE_COMPARISON.md` - Synthetic vs CNN comparison
7. `CNN_SEGMENT_IMPLEMENTATION_PLAN.md` - Complete implementation guide
8. `README.md` - Backend overview and status

### Testing & Validation
9. `check_missing_blockfaces.py` - Identify missing geometries
10. `verify_cnn_mappings.py` - Validate CNN mappings
11. `show_blockface_details.py` - Display blockface data
12. `test_parking_regs.py` - Test parking regulation matching
13. `investigate_20th_street.py` - Analyze 20th Street data
14. `analyze_20th_street_block.py` - Block-level analysis

### Results & Logs
15. `missing_blockfaces.txt` - Coverage analysis results
16. `blockface_details_final.txt` - Detailed blockface data
17. `20th_street_analysis.txt` - 20th Street findings
18. `bryant_florida_analysis.txt` - Intersection analysis
19. `parking_regs_results.txt` - Regulation distribution

---

## Key Metrics

### Before Fixes
- Parking regulations attached: **0**
- Coverage: 7.4% of CNNs have blockfaces
- CNN 1046000: No data available

### After Technical Fixes
- Parking regulations attached: **136**
- Coverage: Still 7.4% (architecture limited)
- CNN 1046000: Still no data (no blockface)

### After CNN Segment Migration (Expected)
- Parking regulations: **400-600** (across all segments)
- Coverage: **100%** (all 4,014 segments)
- CNN 1046000: **Complete data** with correct regulations

---

## Lessons Learned

1. **Architectural Assumptions**: System was designed assuming complete blockface data, but source only provides 7.4% coverage

2. **Data Source Dependencies**: Relying on single incomplete dataset (pep9-66vw) created coverage gaps

3. **Many-to-One Relationships**: Multiple CNN segments per street name requires careful mapping

4. **Spatial Matching Complexity**: Determining which side of street requires robust multi-point algorithms

5. **Source Data Structure**: SFMTA organizes data by CNN + side; our system should match this structure

---

## Next Steps

### Immediate (Day 1)
1. ✅ Create comprehensive documentation
2. ⏳ Commit all documents to GitHub
3. ⏳ Backup current database
4. ⏳ Begin Phase 1 implementation

### Short-term (Week 1)
- Implement StreetSegment model
- Create segment generation logic
- Test with CNN 1046000
- Validate coverage

### Medium-term (Week 2)
- API updates
- Frontend migration
- End-to-end testing
- Production deployment

---

## Conclusion

The investigation successfully identified and fixed technical bugs preventing parking regulation joins, but more importantly, revealed a fundamental architectural limitation: only 7.4% of streets have the blockface geometries required by the current system.

The approved solution—migrating to CNN-based street segments—will provide 100% coverage by using authoritative CNN identifiers and centerline geometries that are available for all streets. This matches how SFMTA organizes their data and enables accurate regulation mapping to specific blocks (e.g., "20th St between York and Bryant").

All technical groundwork is complete, comprehensive documentation created, and implementation plan approved. Ready to proceed with database backup and Phase 1 implementation.