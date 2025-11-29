# Architecture Comparison: Synthetic Blockfaces vs CNN-Based Segments

## Current Situation

**Data Available**:
- ✅ Street Sweeping: Has CNN + Side (complete coverage)
- ✅ Meters: Have CNN (can determine side from location)
- ⚠️ Parking Regulations: Only have geometry (need spatial matching)
- ❌ Blockface Geometries: Only 7.4% coverage from pep9-66vw

**Current System**: Requires blockface geometry to display ANY data

---

## Option 1: Generate Synthetic Blockfaces

### Concept
For each CNN, generate left/right blockface geometries by offsetting the centerline.

### Implementation
```python
def create_synthetic_blockfaces(cnn, centerline_geometry):
    """Offset centerline to create blockfaces"""
    centerline = shape(centerline_geometry)
    
    # Create parallel lines offset by ~10 meters
    left_blockface = centerline.parallel_offset(0.0001, 'left')
    right_blockface = centerline.parallel_offset(0.0001, 'right')
    
    return {
        "left": {"cnn": cnn, "side": "L", "geometry": left_blockface},
        "right": {"cnn": cnn, "side": "R", "geometry": right_blockface}
    }
```

### Pros ✅
1. **Minimal Code Changes**: Extends existing blockface-based system
2. **100% Coverage**: Every CNN gets blockfaces
3. **Frontend Compatible**: No changes needed to UI/API
4. **Spatial Join Works**: Can use existing spatial matching logic
5. **Gradual Improvement**: Can replace synthetic with real geometries later
6. **Visualization**: Can show approximate curb locations on map

### Cons ❌
1. **Synthetic = Inaccurate**: Offsets don't match real curb positions
2. **Arbitrary Offset**: 10 meters is a guess (streets vary in width)
3. **Computational Overhead**: Creating/storing 4,000+ synthetic geometries
4. **Misleading**: May show regulations in wrong physical location
5. **Data Quality Issues**: Hard to distinguish real vs synthetic data
6. **Maintenance**: Must regenerate when centerlines update

### Data Model
```javascript
Blockface {
    cnn: "1046000"
    side: "L" | "R"
    streetName: "20TH ST"
    geometry: LineString  // SYNTHETIC offset from centerline
    isSynthetic: true     // Flag for debugging
    rules: [...]
    schedules: [...]
}
```

---

## Option 2: CNN-Based Street Segments (RECOMMENDED)

### Concept
Use CNN + Side as the primary identifier, not blockface geometry.

### Implementation
```python
def create_street_segment(cnn, side, street_metadata):
    """Create segment from CNN metadata"""
    return {
        "cnn": cnn,
        "side": side,  # L or R
        "streetName": street_metadata["streetName"],
        "centerlineGeometry": street_metadata["centerlineGeometry"],
        "blockfaceGeometry": None,  # Optional, from pep9 if available
        "rules": [],
        "schedules": []
    }

# Match street sweeping: Direct CNN + side match
# Match meters: Direct CNN match, infer side from location
# Match parking regs: Spatial match to centerline, then determine side
```

### Pros ✅
1. **Authoritative Data**: Uses official CNN IDs from SFMTA
2. **100% Coverage**: Every CNN automatically included
3. **Matches Source Structure**: Street sweeping already uses CNN + side
4. **Simpler Logic**: Direct matching for most rules
5. **No Synthetic Data**: All geometries are real
6. **Accurate**: Regulations mapped to correct CNN segment
7. **Future-Proof**: Works with or without blockface geometries
8. **Performance**: Less geometric computation

### Cons ❌
1. **Data Model Change**: Requires refactoring
2. **Frontend Updates**: API responses change structure
3. **Migration Needed**: Convert existing blockfaces to segments
4. **Visualization Challenge**: Must show centerline instead of curb
5. **Parking Reg Matching**: Still needs spatial matching + side determination

### Data Model
```javascript
StreetSegment {
    cnn: "1046000"
    side: "L" | "R"
    streetName: "20TH ST"
    fromStreet: "YORK ST"      // From street sweeping limits
    toStreet: "BRYANT ST"       // From street sweeping limits
    centerlineGeometry: LineString  // REAL geometry
    blockfaceGeometry: LineString | null  // Optional from pep9
    rules: [
        {type: "street-sweeping", day: "Tues", hours: "9-11", source: "CNN"}
        {type: "parking-regulation", hours: "8-18", source: "spatial"}
    ]
    schedules: [...]
}
```

---

## Detailed Comparison

### Data Accuracy

| Aspect | Synthetic Blockfaces | CNN Segments |
|--------|---------------------|--------------|
| Street Sweeping | ✅ Accurate (from CNN) | ✅ Accurate (from CNN) |
| Meters | ✅ Accurate (from CNN) | ✅ Accurate (from CNN) |
| Parking Regulations | ⚠️ Approximate (spatial + synthetic geom) | ✅ Accurate (spatial + centerline) |
| Physical Location | ❌ Offset is guessed | ✅ Centerline is authoritative |

### Coverage

| Aspect | Synthetic Blockfaces | CNN Segments |
|--------|---------------------|--------------|
| CNNs Covered | ✅ 100% (2,007) | ✅ 100% (2,007) |
| Sides per CNN | ✅ 2 (L & R) | ✅ 2 (L & R) |
| Real Geometries | ⚠️ 7.4% real, 92.6% synthetic | ✅ 100% real (centerlines) |

### Implementation Complexity

| Task | Synthetic Blockfaces | CNN Segments |
|------|---------------------|--------------|
| Backend Changes | 🟡 Medium (generate geometries) | 🔴 High (refactor data model) |
| Frontend Changes | 🟢 None | 🟡 Medium (new API structure) |
| Migration | 🟢 None (extends current) | 🔴 High (convert existing data) |
| Testing | 🟡 Medium (validate offsets) | 🔴 High (validate all joins) |

### Performance

| Metric | Synthetic Blockfaces | CNN Segments |
|--------|---------------------|--------------|
| Storage | ❌ 2x geometries (real + synthetic) | ✅ 1x geometries (centerlines only) |
| Query Speed | ⚠️ Slower (more spatial queries) | ✅ Faster (CNN-based indexes) |
| Ingestion Time | ❌ Slower (generate 4,000 geometries) | ✅ Faster (no generation) |

### Maintainability

| Aspect | Synthetic Blockfaces | CNN Segments |
|--------|---------------------|--------------|
| Code Complexity | 🟡 Medium | 🟢 Low (simpler logic) |
| Data Quality | ❌ Mixed (real + synthetic) | ✅ All authoritative |
| Debugging | ❌ Harder (which is synthetic?) | ✅ Easier (clear data lineage) |
| Updates | ❌ Must regenerate synthetics | ✅ Just update source data |

---

## Recommended Solution: CNN-Based Segments

### Why This is Better

1. **Matches SFMTA Data Structure**: 
   - Street sweeping uses CNN + side
   - This is how SF organizes street data
   - We're working WITH the system, not against it

2. **Higher Accuracy**:
   - Uses authoritative CNN identifiers
   - No guessed/approximated geometries
   - Regulations mapped to correct street segments

3. **Better for Users**:
   - "20th St between York and Bryant" = CNN 1046000
   - More precise than "somewhere near this approximate curb"

4. **Simpler Long-Term**:
   - One data structure
   - Clear data provenance
   - Easier to debug and maintain

### Migration Path

**Phase 1: Parallel Implementation** (1-2 days)
- Create `StreetSegment` model alongside `Blockface`
- Implement CNN-based matching
- Test with existing data

**Phase 2: Data Migration** (1 day)
- Convert existing blockfaces to segments
- Populate segments for all CNNs
- Verify data integrity

**Phase 3: Frontend Update** (2-3 days)
- Update API to return segments
- Modify map visualization for centerlines
- Update UI components

**Phase 4: Cleanup** (1 day)
- Remove old blockface code
- Update documentation
- Performance optimization

**Total: ~5-7 days**

### Implementation Priorities

```python
# Priority 1: Core Data Structure
class StreetSegment:
    cnn: str              # Primary key + side
    side: str             # L or R
    streetName: str
    fromStreet: str       # From limits in street sweeping
    toStreet: str         # From limits in street sweeping
    centerlineGeometry: LineString
    
# Priority 2: Direct Matching (Easy)
def match_street_sweeping(segment):
    """Direct CNN + side match"""
    return db.sweeping.find({"cnn": segment.cnn, "side": segment.side})

def match_meters(segment):
    """CNN match, determine side from location"""
    meters = db.meters.find({"cnn": segment.cnn})
    return [m for m in meters if on_correct_side(m, segment)]

# Priority 3: Spatial Matching (Complex)
def match_parking_regulations(segment):
    """
    1. Find regs near centerline (<50m)
    2. Determine which side they're on
    3. Match to segment.side
    """
    nearby = db.regs.find({
        "$near": {
            "$geometry": segment.centerlineGeometry,
            "$maxDistance": 50
        }
    })
    return [r for r in nearby if determine_side(r, segment) == segment.side]
```

---

## Specific Answers to Your Questions

### "We will need some means to map left or right side of each street"

**CNN Segment Approach**: ✅ Better
- Use `get_side_of_street()` function (already working)
- For sweeping: Side is in the data (`cnnrightleft` field)
- For regulations: Calculate from centerline + regulation geometry
- For meters: Calculate from centerline + meter location

**Synthetic Blockface Approach**: ⚠️ Works but less accurate
- Same side determination
- But based on synthetic offset geometry, not real positions

### "Attach street cleaning, parking reg, and meter rules to each side"

**CNN Segment Approach**: ✅ Better
```python
segment = {
    "cnn": "1046000",
    "side": "L",
    "rules": [
        # Direct CNN match
        {"type": "sweeping", "day": "Tues", "hours": "9-11"},
        # Spatial + side match
        {"type": "parking", "limit": "1hr", "hours": "8-18"},
        # CNN + location match
        {"type": "meter", "postId": "12345"}
    ]
}
```

**Synthetic Blockface Approach**: ⚠️ Works but roundabout
- Same matching logic
- But requires synthetic geometry intermediary
- Less direct, more complex

---

## Final Recommendation

**Use CNN-Based Street Segments** because:

1. ✅ **More Accurate**: Uses authoritative CNN + side from SFMTA
2. ✅ **Better Data Quality**: All real geometries, no synthetics
3. ✅ **Matches Source**: How SFMTA structures their data
4. ✅ **Simpler**: Direct matching for most rules
5. ✅ **Future-Proof**: Works with or without blockface geometries
6. ✅ **Better UX**: Users can understand "20th between York-Bryant" better than "offset curb approximation"

The upfront work (~5-7 days) is worth it for a cleaner, more maintainable system built on authoritative data rather than synthetic approximations.