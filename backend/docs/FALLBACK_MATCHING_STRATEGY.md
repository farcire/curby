# Fallback Matching Strategy for Unmatched Parking Regulations

**Date:** January 3, 2026
**Status:** ✅ Strategy Defined, Implementation In Progress
**Purpose:** Document the fallback matching strategy for 7 parking regulations that failed standard geospatial matching

---

## Overview

Seven parking regulations (0.03% of dataset) failed to match to street segments using standard geospatial matching. This document defines the fallback matching strategy using synthetic boundaries generated from district, neighborhood, and RPP area data.

---

## Affected Regulations

### Type 1: Geometry + District + Neighborhood (3 regulations)

**Regulation IDs:** 4973, 64, 2191

**Characteristics:**
- Have geometry (point or polygon)
- Have supervisor_district field
- Have analysis_neighborhood field
- Failed standard geospatial matching (likely due to geometry precision issues)

**Matching Strategy:**
1. Query segments nearby geometry (within buffer distance)
2. Filter by same supervisor_district
3. Filter by same analysis_neighborhood
4. Skip if segment already has non-meter parking regulations
   - Meters OK (can coexist)
   - Street cleaning OK (can coexist)
   - Other parking regulations NOT OK (would conflict)

**Skip Condition Logic:**
```python
def should_skip_segment_type1(segment):
    """
    Skip if segment has non-meter parking regulations.
    Meters and street cleaning are OK (can coexist).
    """
    if not segment.get('rules'):
        return False  # No rules, safe to apply
    
    for rule in segment['rules']:
        rule_type = rule.get('type', '')
        # Skip if has parking regulations (not meter, not cleaning)
        if rule_type not in ['meter', 'street_cleaning']:
            return True  # Has conflicting regulation, skip
    
    return False  # Only has meters/cleaning, safe to apply
```

### Type 2: RPP Areas Only (4 regulations)

**Regulation IDs:** 1551, 2303, 2353, 17287

**Characteristics:**
- No geometry field
- Have RPP area fields (rpparea1, rpparea2, rpparea3)
- May have supervisor_district and analysis_neighborhood fields

**Matching Strategy:**
1. **Primary Match:** RPP boundary + district + neighborhood
   - Query segments within RPP area boundary
   - Filter by same supervisor_district (if present)
   - Filter by same analysis_neighborhood (if present)
   
2. **Fallback Match:** RPP boundary only
   - If district or neighborhood is empty/null
   - Query segments within RPP area boundary only

3. **Skip Conditions:**
   - Skip if segment already has RPP rules (would conflict)
   - Skip if segment has non-meter parking regulations (would conflict)
   - Meters OK (can coexist)
   - Street cleaning OK (can coexist)

**Skip Condition Logic:**
```python
def should_skip_segment_type2(segment):
    """
    Skip if segment has RPP rules OR non-meter parking regulations.
    Meters and street cleaning are OK (can coexist).
    """
    if not segment.get('rules'):
        return False  # No rules, safe to apply
    
    for rule in segment['rules']:
        rule_type = rule.get('type', '')
        
        # Skip if has RPP rules (would conflict)
        if rule_type == 'rpp':
            return True
        
        # Skip if has parking regulations (not meter, not cleaning)
        if rule_type not in ['meter', 'street_cleaning']:
            return True
    
    return False  # Only has meters/cleaning, safe to apply
```

---

## Synthetic Boundaries

### RPP Area Boundaries

**Status:** ✅ Generated (January 3, 2026)

**Details:**
- Generated 33 RPP area boundaries from matched regulations
- Stored in `rpp_area_boundaries` MongoDB collection
- 100% geometry coverage
- 15.7% overlap rate (expected behavior - RPP areas can overlap)
- Created geospatial 2dsphere indexes for efficient queries

**Data Structure:**
```json
{
  "_id": ObjectId("..."),
  "rpp_area": "A",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], [lon, lat], ...]]
  },
  "regulation_count": 150,
  "created_at": "2026-01-03T..."
}
```

**Script:** [`generate_rpp_area_boundaries.py`](generate_rpp_area_boundaries.py)

### District Boundaries

**Status:** ⏭️ Ready for Generation

**Details:**
- Analyzed 34,324 street segments
- Found 12 unique districts (1-11 plus 280 "nan" segments)
- 100% geometry coverage (all segments have district field)
- 0% overlap (by design - single-valued field)

**Data Structure (Planned):**
```json
{
  "_id": ObjectId("..."),
  "district": "1",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], [lon, lat], ...]]
  },
  "segment_count": 3120,
  "created_at": "2026-01-03T..."
}
```

**Script:** To be created (copy pattern from `generate_rpp_area_boundaries.py`)

---

## Database Optimization

### Indexes Created

**Status:** ✅ Created (January 3, 2026)

**Compound Index:**
```javascript
db.street_segments.createIndex({
  "supervisor_district": 1,
  "analysis_neighborhood": 1
})
```

**Individual Indexes:**
```javascript
db.street_segments.createIndex({"supervisor_district": 1})
db.street_segments.createIndex({"analysis_neighborhood": 1})
```

**Purpose:**
- Optimize fallback matching queries
- Enable efficient filtering by district + neighborhood
- Support both compound and individual field queries

**Script:** [`create_fallback_matching_indexes.py`](create_fallback_matching_indexes.py)

---

## Implementation Plan

### Centralized Fallback Matching Script

**Script Name:** `apply_fallback_matching.py`

**Steps:**
1. Query all 7 unmatched regulations from parking_regulations collection
2. Separate into Type 1 (3 regs) and Type 2 (4 regs)
3. For Type 1 regulations:
   - Query segments nearby geometry in same district+neighborhood
   - Apply skip condition logic
   - Update matching segments with regulation
4. For Type 2 regulations:
   - Query segments using RPP boundary + district + neighborhood
   - Fallback to RPP boundary only if district/neighborhood empty
   - Apply skip condition logic
   - Update matching segments with regulation
5. Log results:
   - Number of segments matched per regulation
   - Number of segments skipped per regulation
   - Total segments updated
6. Update documentation with results

**Pseudocode:**
```python
def apply_fallback_matching():
    # Get unmatched regulations
    type1_regs = get_regulations([4973, 64, 2191])
    type2_regs = get_regulations([1551, 2303, 2353, 17287])
    
    # Process Type 1
    for reg in type1_regs:
        segments = query_segments_nearby(
            geometry=reg['geometry'],
            district=reg['supervisor_district'],
            neighborhood=reg['analysis_neighborhood'],
            buffer_meters=50
        )
        
        matched = 0
        skipped = 0
        for seg in segments:
            if should_skip_segment_type1(seg):
                skipped += 1
                continue
            
            apply_regulation_to_segment(seg, reg)
            matched += 1
        
        log_result(reg['id'], matched, skipped)
    
    # Process Type 2
    for reg in type2_regs:
        # Try primary match first
        if reg.get('supervisor_district') and reg.get('analysis_neighborhood'):
            segments = query_segments_in_rpp_boundary(
                rpp_areas=reg['rpp_areas'],
                district=reg['supervisor_district'],
                neighborhood=reg['analysis_neighborhood']
            )
        else:
            # Fallback to RPP only
            segments = query_segments_in_rpp_boundary(
                rpp_areas=reg['rpp_areas']
            )
        
        matched = 0
        skipped = 0
        for seg in segments:
            if should_skip_segment_type2(seg):
                skipped += 1
                continue
            
            apply_regulation_to_segment(seg, reg)
            matched += 1
        
        log_result(reg['id'], matched, skipped)
```

---

## Data Quality Issues

### Issue #1: Empty Regulation Fields

**Regulation IDs:** 3295, 3948, 3561, 3949, 3947

**Problem:** Empty `regulation` field (primary display field)

**Solution:** Filter out during ingestion, report to SFMTA

**Impact:** 0.02% of regulations, no user impact (unusable anyway)

**Status:** ✅ Documented and excluded

**Reference:** Issue #11 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

---

## Expected Results

### Success Metrics

**Type 1 Regulations:**
- Expected match rate: 80-100% (geometry + district + neighborhood is specific)
- Expected skip rate: 0-20% (most segments won't have conflicting regulations)

**Type 2 Regulations:**
- Expected match rate: 50-80% (RPP areas are broader)
- Expected skip rate: 20-50% (RPP areas may have existing RPP rules)

**Overall:**
- Expected to recover 5-7 of the 7 unmatched regulations
- Minimal conflicts due to skip condition logic
- No user-facing errors or data corruption

### Validation

After implementation:
1. Verify all 7 regulations were processed
2. Check match counts are reasonable
3. Verify no duplicate regulations on segments
4. Confirm skip conditions worked correctly
5. Update documentation with actual results

---

## References

### Documentation
- **Data Quality Log:** Issue #015 in [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)
- **Data Quality Issues:** Issue #12 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)
- **Regulation Normalization:** Part 6 in [`REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md`](REGULATION_NORMALIZATION_COMPLETE_SUMMARY.md)

### Scripts
- **RPP Boundaries:** [`generate_rpp_area_boundaries.py`](generate_rpp_area_boundaries.py)
- **District Analysis:** [`investigate_district_boundaries.py`](investigate_district_boundaries.py)
- **Database Indexes:** [`create_fallback_matching_indexes.py`](create_fallback_matching_indexes.py)
- **Fallback Matching:** `apply_fallback_matching.py` (to be created)

### MongoDB Collections
- **RPP Boundaries:** `rpp_area_boundaries` (33 boundaries)
- **District Boundaries:** `district_boundaries` (to be created, 11 boundaries)
- **Street Segments:** `street_segments` (34,324 segments)
- **Parking Regulations:** `parking_regulations` (~25,000 regulations)

---

## Timeline

- ✅ **January 3, 2026:** Strategy defined, documentation created
- ✅ **January 3, 2026:** RPP boundaries generated
- ✅ **January 3, 2026:** Database indexes created
- ⏭️ **Next:** Generate district boundaries
- ⏭️ **Next:** Implement centralized fallback matching script
- ⏭️ **Next:** Run fallback matching and validate results
- ⏭️ **Next:** Update documentation with actual results

---

**Document Version:** 1.0
**Last Updated:** January 3, 2026
**Author:** Data Quality Team
**Status:** Strategy Defined, Implementation In Progress