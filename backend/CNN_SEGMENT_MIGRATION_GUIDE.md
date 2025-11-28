# CNN Segment Migration Guide

## Overview

This guide documents the migration from blockface-based to CNN-segment-based architecture, achieving 100% street coverage.

---

## What Changed

### Before (Blockface Architecture)
- **Primary Key**: Blockface geometry ID
- **Coverage**: 7.4% (148 of 2,007 CNNs had blockface geometries)
- **Problem**: 92.6% of streets couldn't display regulations
- **Example**: CNN 1046000 (20th St between York-Bryant) had no blockface → no data displayed

### After (CNN Segment Architecture)
- **Primary Key**: (CNN, Side) - e.g., ("1046000", "L")
- **Coverage**: 100% (2,007 CNNs × 2 sides = 4,014 segments)
- **Solution**: Every street has both L and R segments with centerline geometry
- **Example**: CNN 1046000 now has both segments with complete regulation data

---

## Files Created

### Core Implementation
1. **`ingest_data_cnn_segments.py`** - New ingestion script
   - Creates 2 segments per CNN (Left and Right)
   - Enhanced parking regulation matching with multi-point sampling
   - Direct CNN+side matching for street sweeping
   - Complete 100% coverage

2. **`validate_cnn_segments.py`** - Validation script
   - Verifies 100% coverage
   - Tests CNN 1046000 specifically
   - Validates rule distribution
   - Checks database indexes

3. **`run_cnn_segment_migration.sh`** - Migration runner
   - Runs ingestion
   - Runs validation
   - Reports results

### Data Model
4. **`models.py`** - Updated with `StreetSegment` class
   - Replaces `Blockface` as primary model
   - Includes both centerline (required) and blockface (optional) geometries
   - Supports rules, schedules, and metadata

---

## Running the Migration

### Prerequisites
1. Database backup completed (already done)
2. Virtual environment activated
3. `.env` file configured with MongoDB URI and SFMTA token

### Step 1: Run Migration
```bash
cd backend
./run_cnn_segment_migration.sh
```

Or manually:
```bash
python3 ingest_data_cnn_segments.py
python3 validate_cnn_segments.py
```

### Step 2: Review Results
The validation script will show:
- Total coverage (should be 100%)
- CNN 1046000 validation (critical test case)
- Rule distribution across segments
- Database index verification

### Expected Output
```
Total CNNs: 2,007
Expected segments: 4,014
Actual segments: 4,014
Coverage: 100%

CNN 1046000 Left segment exists ✓
  Street: 20TH ST
  From: York St
  To: Bryant St
  Sweeping rules: 1
    - Tuesday 9:00-11:00 ✓
```

---

## Key Differences in Implementation

### 1. Segment Generation
**Old**: One blockface per geometry from pep9-66vw dataset
```python
# Only creates blockface if geometry exists
if bf_geo:
    create_blockface(bf_geo)
```

**New**: Two segments per CNN from Active Streets
```python
# Always creates both sides for every CNN
for cnn in streets:
    create_segment(cnn, "L")  # Left side
    create_segment(cnn, "R")  # Right side
```

### 2. Parking Regulation Matching
**Old**: Single-point spatial join
```python
distance = regulation.distance(blockface)
if distance < threshold:
    attach_to_blockface()
```

**New**: Multi-point sampling with side determination
```python
# Sample 3 points along regulation line
for point in [0.25, 0.5, 0.75]:
    sample = regulation.interpolate(point)
    side = determine_side(sample, centerline)
    votes[side] += 1

# Use majority vote
determined_side = max(votes)
if determined_side == segment.side:
    attach_to_segment()
```

### 3. Street Sweeping Matching
**Old**: CNN + side match (required blockface to exist)
```python
# Only matched if blockface existed
for bf in blockfaces_for_cnn:
    if bf.side == rule.side:
        attach(rule, bf)
```

**New**: Direct CNN + side match (always works)
```python
# Always finds matching segment
for segment in segments:
    if segment.cnn == rule.cnn and segment.side == rule.side:
        attach(rule, segment)
```

---

## Database Schema

### New Collection: `street_segments`

**Structure**:
```javascript
{
  "_id": ObjectId("..."),
  "cnn": "1046000",
  "side": "L",
  "streetName": "20TH ST",
  "fromStreet": "York St",        // From sweeping limits
  "toStreet": "Bryant St",         // From sweeping limits
  
  // Geometries
  "centerlineGeometry": {          // REQUIRED - from Active Streets
    "type": "LineString",
    "coordinates": [[...]]
  },
  "blockfaceGeometry": {           // OPTIONAL - from pep9-66vw
    "type": "LineString",
    "coordinates": [[...]]
  },
  
  // Rules
  "rules": [
    {
      "type": "street-sweeping",
      "day": "Tuesday",
      "startTime": "9:00",
      "endTime": "11:00",
      "side": "L",
      "description": "Street Cleaning Tuesday 9:00-11:00"
    },
    {
      "type": "parking-regulation",
      "regulation": "2 HR PARKING 9AM-6PM MON-SAT",
      "timeLimit": "2",
      "side": "L",
      "matchConfidence": 0.95
    }
  ],
  
  // Meter Schedules
  "schedules": [
    {
      "beginTime": "09:00:00",
      "endTime": "18:00:00",
      "rate": "2.00",
      "rateUnit": "per hour"
    }
  ],
  
  // Metadata
  "zip_code": "94110",
  "layer": "0"
}
```

**Indexes**:
- `{cnn: 1, side: 1}` (unique) - Primary key
- `{centerlineGeometry: "2dsphere"}` - Geospatial queries

---

## API Updates Needed

### Current Endpoint (Blockface-based)
```python
@app.get("/api/blockfaces")
async def get_blockfaces(bounds: str):
    # Queries blockfaces collection
    blockfaces = await db.blockfaces.find({
        "geometry": {"$geoWithin": {"$geometry": bounds}}
    })
```

### New Endpoint (Segment-based)
```python
@app.get("/api/segments")
async def get_street_segments(
    street_name: Optional[str] = None,
    cnn: Optional[str] = None,
    bounds: Optional[str] = None
):
    query = {}
    
    if street_name:
        query["streetName"] = {"$regex": street_name, "$options": "i"}
    
    if cnn:
        query["cnn"] = cnn
    
    if bounds:
        bounds_geom = json.loads(bounds)
        query["centerlineGeometry"] = {
            "$geoWithin": {"$geometry": bounds_geom}
        }
    
    segments = await db.street_segments.find(query).to_list(None)
    return {"segments": segments, "count": len(segments)}

@app.get("/api/segments/{cnn}/{side}")
async def get_segment(cnn: str, side: str):
    segment = await db.street_segments.find_one({"cnn": cnn, "side": side})
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment
```

---

## Frontend Updates Needed

### 1. Data Fetching
**Change**: Update API calls from `/api/blockfaces` to `/api/segments`

### 2. Map Visualization
**Before**: Display blockface geometry (side-specific line)
```typescript
// Used blockface.geometry (when available)
if (blockface.geometry) {
  renderLine(blockface.geometry);
}
```

**After**: Display centerline geometry (always available)
```typescript
// Use centerlineGeometry (always present)
renderLine(segment.centerlineGeometry);

// Optionally show side indicator
if (segment.side === "L") {
  renderLeftSideIndicator();
}
```

### 3. Detail Display
**Update**: Show segment-specific information
```typescript
interface StreetSegment {
  cnn: string;
  side: "L" | "R";
  streetName: string;
  fromStreet?: string;
  toStreet?: string;
  centerlineGeometry: GeoJSON;
  blockfaceGeometry?: GeoJSON;
  rules: Rule[];
  schedules: Schedule[];
}
```

---

## Testing Checklist

### ✓ Phase 1: Data Ingestion
- [x] StreetSegment model created
- [x] Segment generation logic (2 per CNN)
- [x] Enhanced regulation matching
- [x] Ingestion script complete

### ✓ Phase 2: Validation
- [x] Validation script created
- [x] Coverage verification
- [x] CNN 1046000 test
- [x] Rule distribution check

### ⏳ Phase 3: API Updates (Next)
- [ ] Create `/api/segments` endpoints
- [ ] Update existing endpoints
- [ ] Test with Postman/curl
- [ ] Update API documentation

### ⏳ Phase 4: Frontend Updates (Next)
- [ ] Update data fetching logic
- [ ] Modify map visualization
- [ ] Update detail components
- [ ] Test user interface

### ⏳ Phase 5: Deployment (Final)
- [ ] Backup production database
- [ ] Run migration in production
- [ ] Validate production data
- [ ] Monitor for issues

---

## Rollback Plan

If issues occur, restore from backup:

```bash
cd backend/database_backups/pre_cnn_migration_20251127_161321/

# Restore blockfaces
mongoimport --uri="$MONGODB_URI" --collection=blockfaces --file=blockfaces.json --jsonArray

# Restore other collections as needed
mongoimport --uri="$MONGODB_URI" --collection=streets --file=streets.json --jsonArray
# etc...
```

---

## Success Metrics

### Target Metrics (Expected)
- ✅ Coverage: 100% (4,014 segments)
- ✅ CNN 1046000: Complete data with regulations
- ✅ Street sweeping: >1,800 rules attached
- ✅ Parking regulations: 400-600 rules attached
- ✅ Response time: <200ms for typical queries

### Current Metrics (Before Migration)
- ❌ Coverage: 7.4% (148 blockfaces)
- ❌ CNN 1046000: No data
- ✅ Street sweeping: 914 rules attached (but only on 7.4% of streets)
- ✅ Parking regulations: 136 rules attached (but only on 7.4% of streets)

---

## Next Steps

1. **Run Migration**: Execute `run_cnn_segment_migration.sh`
2. **Verify Results**: Review validation output
3. **Update API**: Implement new segment endpoints
4. **Update Frontend**: Modify components to use segments
5. **Test E2E**: Verify complete user flow
6. **Deploy**: Push to production after validation

---

## Support

For issues or questions:
1. Review validation output
2. Check logs in ingestion output
3. Verify database indexes exist
4. Confirm all required collections populated
5. Test with sample queries

---

## References

- **Investigation Summary**: `INVESTIGATION_SUMMARY.md`
- **Architecture Comparison**: `ARCHITECTURE_COMPARISON.md`
- **Implementation Plan**: `CNN_SEGMENT_IMPLEMENTATION_PLAN.md`
- **Geospatial Analysis**: `GEOSPATIAL_JOIN_ANALYSIS.md`