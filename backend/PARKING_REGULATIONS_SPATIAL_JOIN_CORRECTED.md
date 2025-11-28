# Parking Regulations to CNN L/R - Spatial Join Strategy (CORRECTED)

**Date**: November 28, 2024  
**Dataset**: Parking Regulations (hi6h-neyh)  
**Key Insight**: Regulations can apply to BOTH sides or ONE side

---

## Critical Understanding

**Parking Regulations do NOT have CNN identifiers.**

**Key Logic**:
1. **If BOTH CNN L and CNN R fall clearly within regulation geometry** → Apply to BOTH sides
2. **If only ONE side falls clearly within** → Apply to that side only  
3. **If CNN is at boundary** (ambiguous) → Use Parcel Overlay conflict resolution

---

## Spatial Join Strategy

### Phase 1: Find Candidate Segments

```python
def find_candidate_segments(regulation_geometry):
    """
    Find CNN segments spatially close to the regulation.
    Returns BOTH L and R segments for each CNN.
    """
    
    candidates = db.street_segments.find({
        "centerlineGeometry": {
            "$near": {
                "$geometry": regulation_geometry,
                "$maxDistance": 50  # meters
            }
        }
    })
    
    return list(candidates)
```

### Phase 2: Determine Coverage (BOTH or ONE side)

```python
def determine_regulation_coverage(regulation_geo, cnn_segments):
    """
    Determine if regulation covers BOTH sides or just ONE side.
    
    Logic:
    - Distance < 10m = "CLEAR" (definitely within regulation)
    - Distance 10-50m = "BOUNDARY" (ambiguous, needs resolution)
    - Distance > 50m = Not applicable
    """
    
    reg_shape = shape(regulation_geo)
    
    # Group segments by CNN
    by_cnn = {}
    for seg in cnn_segments:
        cnn = seg["cnn"]
        if cnn not in by_cnn:
            by_cnn[cnn] = {"L": None, "R": None}
        by_cnn[cnn][seg["side"]] = seg
    
    results = []
    
    for cnn, sides in by_cnn.items():
        left_status = None
        right_status = None
        
        # Check LEFT side
        if sides["L"]:
            left_centerline = shape(sides["L"]["centerlineGeometry"])
            left_distance = reg_shape.distance(left_centerline)
            
            if left_distance < 10:  # meters - CLEARLY within
                left_status = ("L", sides["L"], "CLEAR")
            elif left_distance < 50:  # meters - AT BOUNDARY
                left_status = ("L", sides["L"], "BOUNDARY")
        
        # Check RIGHT side
        if sides["R"]:
            right_centerline = shape(sides["R"]["centerlineGeometry"])
            right_distance = reg_shape.distance(right_centerline)
            
            if right_distance < 10:  # meters - CLEARLY within
                right_status = ("R", sides["R"], "CLEAR")
            elif right_distance < 50:  # meters - AT BOUNDARY
                right_status = ("R", sides["R"], "BOUNDARY")
        
        # Add results for this CNN
        if left_status:
            results.append(left_status)
        if right_status:
            results.append(right_status)
    
    return results
```

### Phase 3: Apply Based on Coverage

```python
def apply_regulation_to_segments(regulation, coverage_results):
    """
    Apply regulation based on coverage analysis.
    
    Rules:
    1. BOTH sides CLEAR → Apply to BOTH CNN L and CNN R
    2. ONE side CLEAR, other BOUNDARY → Apply to CLEAR side only
    3. ONE side CLEAR, other not found → Apply to CLEAR side only
    4. BOTH sides BOUNDARY → Use conflict resolution
    5. ONE side BOUNDARY → Use conflict resolution
    """
    
    # Separate by status
    clear_sides = [r for r in coverage_results if r[2] == "CLEAR"]
    boundary_sides = [r for r in coverage_results if r[2] == "BOUNDARY"]
    
    segments_to_update = []
    
    # Case 1: BOTH sides clearly within regulation
    if len(clear_sides) == 2:
        logger.info(
            f"Regulation {regulation['objectid']} applies to BOTH sides "
            f"(CNN {clear_sides[0][1]['cnn']})"
        )
        segments_to_update = [r[1] for r in clear_sides]
    
    # Case 2: ONE side clearly within
    elif len(clear_sides) == 1:
        logger.info(
            f"Regulation {regulation['objectid']} applies to "
            f"{clear_sides[0][0]} side only "
            f"(CNN {clear_sides[0][1]['cnn']})"
        )
        segments_to_update = [clear_sides[0][1]]
    
    # Case 3: No clear sides, only boundary cases
    elif len(boundary_sides) > 0:
        logger.info(
            f"Regulation {regulation['objectid']} at boundary - "
            f"using conflict resolution"
        )
        resolved = await resolve_boundary_conflicts(
            regulation, 
            boundary_sides
        )
        segments_to_update = resolved
    
    return segments_to_update
```

### Phase 4: Conflict Resolution (Boundary Cases ONLY)

```python
async def resolve_boundary_conflicts(regulation, boundary_sides):
    """
    Use Parcel Overlay to resolve boundary cases.
    
    Only called when CNN is at the edge of regulation geometry
    and we cannot determine which side(s) the regulation applies to.
    """
    
    reg_neighborhood = regulation.get("analysis_neighborhood")
    reg_district = regulation.get("supervisor_district")
    
    resolved_segments = []
    
    for side, segment, status in boundary_sides:
        # Get segment's midpoint
        seg_shape = shape(segment["centerlineGeometry"])
        seg_midpoint = seg_shape.interpolate(0.5, normalized=True)
        
        # Find parcel at this location
        parcel = await db.parcel_overlay.find_one({
            "geometry": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [seg_midpoint.x, seg_midpoint.y]
                    }
                }
            }
        })
        
        if parcel:
            parcel_neighborhood = parcel.get("analysis_neighborhood")
            parcel_district = parcel.get("supervisor_district")
            
            # Match on BOTH neighborhood AND district
            if (parcel_neighborhood == reg_neighborhood and
                parcel_district == reg_district):
                logger.info(
                    f"Boundary resolved: Regulation applies to "
                    f"CNN {segment['cnn']} side {side}"
                )
                resolved_segments.append(segment)
            else:
                logger.info(
                    f"Boundary resolved: Regulation does NOT apply to "
                    f"CNN {segment['cnn']} side {side} "
                    f"(neighborhood/district mismatch)"
                )
    
    return resolved_segments
```

---

## Complete Algorithm

```python
async def map_regulation_to_cnn_segments(regulation):
    """
    Complete algorithm with corrected logic.
    """
    
    reg_geo = regulation.get("geometry")
    if not reg_geo:
        return []
    
    # STEP 1: Find spatially nearby segments
    candidates = find_candidate_segments(reg_geo)
    
    if not candidates:
        logger.warning(
            f"No segments found for regulation {regulation['objectid']}"
        )
        return []
    
    # STEP 2: Determine coverage (CLEAR or BOUNDARY for each side)
    coverage_results = determine_regulation_coverage(reg_geo, candidates)
    
    if not coverage_results:
        logger.warning(
            f"No coverage determined for regulation {regulation['objectid']}"
        )
        return []
    
    # STEP 3: Apply based on coverage
    segments_to_update = await apply_regulation_to_segments(
        regulation,
        coverage_results
    )
    
    # STEP 4: Update segments with regulation
    for segment in segments_to_update:
        await db.street_segments.update_one(
            {"_id": segment["_id"]},
            {
                "$push": {
                    "parkingRegulations": {
                        "objectid": regulation["objectid"],
                        "regulation": regulation["regulation"],
                        "days": regulation.get("days"),
                        "hours": regulation.get("hours"),
                        "timeLimit": regulation.get("hrlimit"),
                        "rppArea": (regulation.get("rpparea1") or 
                                   regulation.get("rpparea2")),
                        "neighborhood": regulation.get("analysis_neighborhood"),
                        "district": regulation.get("supervisor_district")
                    }
                }
            }
        )
        
        logger.info(
            f"Applied regulation {regulation['objectid']} to "
            f"CNN {segment['cnn']} side {segment['side']}"
        )
    
    return segments_to_update
```

---

## Visual Examples

### Example 1: Regulation Covers BOTH Sides

```
Regulation Geometry (wide coverage)
═══════════════════════════════════════════════════════
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel (Mission, District 9)      │
        └────────────────────────────────────┘
                         ↓
              Centerline (CNN 1046000)
              ═══════════════════════════
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel (Mission, District 9)      │
        └────────────────────────────────────┘

Analysis:
- LEFT centerline distance: 8m (CLEAR)
- RIGHT centerline distance: 8m (CLEAR)
- Result: Apply to BOTH CNN 1046000-L AND CNN 1046000-R
```

### Example 2: Regulation Covers ONE Side Only

```
Regulation Geometry (narrow, one side)
─────────────────────────────
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel (Mission, District 9)      │
        └────────────────────────────────────┘
                         ↓
              Centerline (CNN 1046000)
              ═══════════════════════════
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel (Mission, District 9)      │
        └────────────────────────────────────┘

Analysis:
- LEFT centerline distance: 5m (CLEAR)
- RIGHT centerline distance: 45m (too far)
- Result: Apply to CNN 1046000-L ONLY
```

### Example 3: Boundary Case (Needs Resolution)

```
Regulation Geometry (at edge)
                    ─────────────────────
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel A (Mission, District 9)    │
        └────────────────────────────────────┘
                         ↓
              Centerline (CNN 1046000)
              ═══════════════════════════
                         ↓
        ┌────────────────────────────────────┐
        │  Parcel B (SOMA, District 6)       │
        └────────────────────────────────────┘

Analysis:
- LEFT centerline distance: 15m (BOUNDARY)
- RIGHT centerline distance: 15m (BOUNDARY)
- Regulation: Mission, District 9
- Parcel A (left): Mission, District 9 ✓ MATCH
- Parcel B (right): SOMA, District 6 ✗ NO MATCH
- Result: Apply to CNN 1046000-L ONLY (via conflict resolution)
```

---

## Key Differences from Previous Understanding

### ❌ INCORRECT (Previous)
```python
# Always determine ONE side using cross-product
side = determine_side_using_cross_product(regulation, centerline)
# Apply to that side only
```

### ✅ CORRECT (Updated)
```python
# Check if regulation covers BOTH sides
if both_sides_clear:
    # Apply to BOTH CNN L and CNN R
    apply_to_both_sides()
elif one_side_clear:
    # Apply to that side only
    apply_to_one_side()
else:
    # Use conflict resolution for boundary cases
    resolve_using_parcel_overlay()
```

---

## Implementation Checklist

- [ ] Update spatial join logic to check BOTH sides
- [ ] Implement distance-based coverage determination
- [ ] Add "CLEAR" vs "BOUNDARY" classification
- [ ] Apply to BOTH sides when both are clear
- [ ] Use Parcel Overlay ONLY for boundary cases
- [ ] Log which sides regulations are applied to
- [ ] Test with regulations that span full street width
- [ ] Test with regulations on one side only
- [ ] Test boundary cases with conflict resolution

---

## Success Metrics

### Coverage Distribution
```python
# Expected distribution:
- BOTH sides: ~60% of regulations (wide coverage)
- ONE side: ~30% of regulations (narrow coverage)
- BOUNDARY resolved: ~10% of regulations (edge cases)
```

### Validation
```python
# Sample 100 regulations
# Manually verify:
# - Regulations spanning full street → Applied to both sides ✓
# - Regulations on one side → Applied to that side only ✓
# - Boundary cases → Correctly resolved ✓
```

---

## Conclusion

**Corrected Understanding**:

1. ✅ Regulations can apply to **BOTH CNN L and CNN R** (when both sides are clearly within)
2. ✅ Regulations can apply to **ONE side only** (when only one side is clearly within)
3. ✅ **Conflict resolution** is ONLY for boundary cases (when ambiguous)
4. ✅ Use **distance thresholds** to determine "clear" vs "boundary"

This provides more accurate regulation assignments and reduces unnecessary conflict resolution.

---

**Last Updated**: November 28, 2024  
**Status**: Corrected Strategy, Ready for Implementation