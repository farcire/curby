# CNN-Based Street Segment Implementation Plan

## Overview

Migrating from blockface-based to CNN-segment-based architecture to achieve 100% coverage and more accurate regulation mapping.

---

## Phase 1: Core Data Model (Priority: CRITICAL)

### 1.1 Create StreetSegment Model

**File**: `backend/models.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class StreetSegment:
    """
    Represents one side of one CNN street segment.
    Primary key: (cnn, side)
    """
    cnn: str                    # e.g., "1046000"
    side: str                   # "L" or "R"
    streetName: str             # e.g., "20TH ST"
    fromStreet: Optional[str]   # From street sweeping limits
    toStreet: Optional[str]     # From street sweeping limits
    
    # Geometries
    centerlineGeometry: Dict    # GeoJSON from Active Streets (REQUIRED)
    blockfaceGeometry: Optional[Dict]  # GeoJSON from pep9 (OPTIONAL)
    
    # Rules and schedules
    rules: List[Dict]           # Parking regs, sweeping, etc.
    schedules: List[Dict]       # Meter schedules
    
    # Metadata
    zip_code: Optional[str]
    layer: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cnn": self.cnn,
            "side": self.side,
            "streetName": self.streetName,
            "fromStreet": self.fromStreet,
            "toStreet": self.toStreet,
            "centerlineGeometry": self.centerlineGeometry,
            "blockfaceGeometry": self.blockfaceGeometry,
            "rules": self.rules,
            "schedules": self.schedules,
            "zip_code": self.zip_code,
            "layer": self.layer
        }
```

---

## Phase 2: Parking Regulation Side Determination (Priority: CRITICAL)

### 2.1 The Challenge

**Problem**: Parking regulations only have:
- ✅ Geometry (LineString along curb)
- ❌ No CNN field
- ❌ No side field

**Solution**: Multi-step spatial + geometric analysis

### 2.2 Enhanced Side Determination Algorithm

**File**: `backend/ingest_data.py`

```python
def match_regulation_to_segment(regulation_geo: Dict, 
                                centerline_geo: Dict,
                                segment_side: str,
                                max_distance: float = 0.0005) -> bool:
    """
    Determines if a parking regulation applies to a specific street segment side.
    
    Args:
        regulation_geo: GeoJSON geometry of parking regulation line
        centerline_geo: GeoJSON geometry of street centerline
        segment_side: Which side we're checking ("L" or "R")
        max_distance: Maximum distance in degrees (~50 meters)
    
    Returns:
        True if regulation applies to this segment side
    """
    try:
        reg_line = shape(regulation_geo)
        center_line = shape(centerline_geo)
        
        # Step 1: Check if regulation is near this centerline
        distance = reg_line.distance(center_line)
        if distance > max_distance:
            return False  # Too far away
        
        # Step 2: Determine which side the regulation is on
        # Sample multiple points along the regulation line
        sample_points = [0.25, 0.5, 0.75]  # 25%, 50%, 75% along line
        side_votes = {"L": 0, "R": 0}
        
        for position in sample_points:
            reg_point = reg_line.interpolate(position, normalized=True)
            
            # Project onto centerline
            projected_dist = center_line.project(reg_point)
            projected_point = center_line.interpolate(projected_dist)
            
            # Get tangent vector at projected point
            delta = 0.001  # Small step for tangent calculation
            if projected_dist + delta > center_line.length:
                p1 = center_line.interpolate(projected_dist - delta)
                p2 = projected_point
            else:
                p1 = projected_point
                p2 = center_line.interpolate(projected_dist + delta)
            
            # Tangent vector along centerline
            tangent = (p2.x - p1.x, p2.y - p1.y)
            
            # Vector from centerline to regulation point
            to_reg = (reg_point.x - projected_point.x, 
                     reg_point.y - projected_point.y)
            
            # Cross product determines side
            # Positive = Left, Negative = Right
            cross = tangent[0] * to_reg[1] - tangent[1] * to_reg[0]
            
            if cross > 0:
                side_votes["L"] += 1
            elif cross < 0:
                side_votes["R"] += 1
        
        # Step 3: Majority vote determines side
        determined_side = "L" if side_votes["L"] > side_votes["R"] else "R"
        
        # Step 4: Check if matches segment side
        return determined_side == segment_side
        
    except Exception as e:
        print(f"Error in match_regulation_to_segment: {e}")
        return False


def extract_street_limits(sweeping_schedule: Dict) -> tuple:
    """
    Extract FROM/TO street names from sweeping schedule limits.
    Example: "York St  -  Bryant St" -> ("York St", "Bryant St")
    """
    limits = sweeping_schedule.get("limits", "")
    if not limits or "-" not in limits:
        return (None, None)
    
    parts = limits.split("-")
    if len(parts) == 2:
        from_street = parts[0].strip()
        to_street = parts[1].strip()
        return (from_street, to_street)
    
    return (None, None)
```

### 2.3 Regulation Matching Process

```python
async def match_parking_regulations_to_segments(segments: List[Dict], 
                                                regulations_df: pd.DataFrame) -> int:
    """
    Match parking regulations to street segments using spatial + geometric analysis.
    
    Returns: Number of regulations successfully matched
    """
    matched_count = 0
    
    for idx, reg_row in regulations_df.iterrows():
        reg_geo = reg_row.get("shape") or reg_row.get("geometry")
        if not reg_geo:
            continue
        
        # Find closest segment(s) that this regulation could apply to
        best_match = None
        best_score = 0
        
        for segment in segments:
            centerline_geo = segment.get("centerlineGeometry")
            if not centerline_geo:
                continue
            
            # Check if regulation matches this segment's side
            if match_regulation_to_segment(
                reg_geo, 
                centerline_geo, 
                segment.get("side")
            ):
                # Calculate confidence score
                reg_line = shape(reg_geo)
                center_line = shape(centerline_geo)
                distance = reg_line.distance(center_line)
                
                # Closer = higher confidence
                score = 1.0 / (distance + 0.0001)
                
                if score > best_score:
                    best_score = score
                    best_match = segment
        
        # Attach regulation to best matching segment
        if best_match:
            best_match["rules"].append({
                "type": "parking-regulation",
                "regulation": reg_row.get("regulation"),
                "timeLimit": reg_row.get("hrlimit"),
                "permitArea": reg_row.get("rpparea1") or reg_row.get("rpparea2"),
                "days": reg_row.get("days"),
                "hours": reg_row.get("hours"),
                "fromTime": reg_row.get("from_time"),
                "toTime": reg_row.get("to_time"),
                "details": reg_row.get("regdetails"),
                "exceptions": reg_row.get("exceptions"),
                "side": best_match.get("side"),
                "matchConfidence": min(best_score, 1.0)  # For debugging
            })
            matched_count += 1
    
    return matched_count
```

---

## Phase 3: Complete Ingestion Rewrite

### 3.1 New Ingestion Flow

```python
async def ingest_street_segments():
    """
    New ingestion process for CNN-based street segments.
    """
    # === STEP 1: Load Active Streets ===
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token, 
                                        where="zip_code='94110' OR zip_code='94103'")
    
    # Create segments for each CNN (Left and Right)
    all_segments = []
    streets_metadata = {}
    
    for _, row in streets_df.iterrows():
        cnn = row.get("cnn")
        if not cnn:
            continue
        
        # Store metadata
        streets_metadata[cnn] = {
            "streetName": row.get("streetname"),
            "centerlineGeometry": row.get("line"),
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer")
        }
        
        # Create LEFT segment
        left_segment = {
            "cnn": cnn,
            "side": "L",
            "streetName": row.get("streetname"),
            "centerlineGeometry": row.get("line"),
            "blockfaceGeometry": None,  # Will populate if available
            "rules": [],
            "schedules": [],
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer"),
            "fromStreet": None,
            "toStreet": None
        }
        all_segments.append(left_segment)
        
        # Create RIGHT segment
        right_segment = {
            "cnn": cnn,
            "side": "R",
            "streetName": row.get("streetname"),
            "centerlineGeometry": row.get("line"),
            "blockfaceGeometry": None,
            "rules": [],
            "schedules": [],
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer"),
            "fromStreet": None,
            "toStreet": None
        }
        all_segments.append(right_segment)
    
    print(f"Created {len(all_segments)} street segments (2 per CNN)")
    
    # === STEP 2: Add Blockface Geometries (if available) ===
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    
    for _, row in geo_df.iterrows():
        cnn = row.get("cnn_id")
        bf_geo = row.get("shape")
        
        if not cnn or not bf_geo or cnn not in streets_metadata:
            continue
        
        # Determine which side this blockface is on
        centerline_geo = streets_metadata[cnn].get("centerlineGeometry")
        if centerline_geo:
            side = get_side_of_street(centerline_geo, bf_geo)
            
            # Find matching segment and add blockface geometry
            for segment in all_segments:
                if segment["cnn"] == cnn and segment["side"] == side:
                    segment["blockfaceGeometry"] = bf_geo
                    break
    
    # === STEP 3: Match Street Sweeping (Easy - Direct CNN + Side) ===
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    matched_sweeping = 0
    
    for _, row in sweeping_df.iterrows():
        cnn = row.get("cnn")
        side = row.get("cnnrightleft")
        
        # Extract street limits
        from_street, to_street = extract_street_limits(row)
        
        # Find matching segment
        for segment in all_segments:
            if segment["cnn"] == cnn and segment["side"] == side:
                segment["rules"].append({
                    "type": "street-sweeping",
                    "day": row.get("weekday"),
                    "startTime": row.get("fromhour"),
                    "endTime": row.get("tohour"),
                    "side": side,
                    "description": f"Street Cleaning {row.get('weekday')} {row.get('fromhour')}-{row.get('tohour')}"
                })
                
                # Update street limits if not already set
                if not segment["fromStreet"] and from_street:
                    segment["fromStreet"] = from_street
                if not segment["toStreet"] and to_street:
                    segment["toStreet"] = to_street
                
                matched_sweeping += 1
                break
    
    print(f"Matched {matched_sweeping} street sweeping schedules")
    
    # === STEP 4: Match Parking Regulations (Complex - Spatial + Side) ===
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token,
                                             where="analysis_neighborhood='Mission'")
    
    matched_regs = await match_parking_regulations_to_segments(all_segments, regulations_df)
    print(f"Matched {matched_regs} parking regulations")
    
    # === STEP 5: Match Meters (Medium - CNN + Location) ===
    # Similar to current implementation
    
    # === STEP 6: Save to Database ===
    await db.street_segments.delete_many({})
    await db.street_segments.insert_many(all_segments)
    await db.street_segments.create_index([("cnn", 1), ("side", 1)])
    await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
    
    print(f"Saved {len(all_segments)} street segments to database")
```

---

## Phase 4: Testing & Validation

### 4.1 Validation Script

**File**: `backend/validate_cnn_segments.py`

```python
async def validate():
    """Validate the new CNN segment architecture"""
    
    # Test 1: Coverage
    segments = await db.street_segments.find({}).to_list(None)
    streets = await db.streets.find({}).to_list(None)
    
    expected_segments = len(streets) * 2  # 2 sides per CNN
    actual_segments = len(segments)
    
    print(f"Coverage: {actual_segments}/{expected_segments} segments")
    assert actual_segments == expected_segments, "Missing segments!"
    
    # Test 2: CNN 1046000 Specifically
    segment_1046_L = await db.street_segments.find_one({"cnn": "1046000", "side": "L"})
    segment_1046_R = await db.street_segments.find_one({"cnn": "1046000", "side": "R"})
    
    assert segment_1046_L is not None, "Missing CNN 1046000 Left segment"
    assert segment_1046_R is not None, "Missing CNN 1046000 Right segment"
    
    # Verify sweeping
    left_sweeping = [r for r in segment_1046_L["rules"] if r["type"] == "street-sweeping"]
    assert len(left_sweeping) > 0, "Missing sweeping for Left side"
    assert any(r["day"] == "Tuesday" for r in left_sweeping), "Missing Tuesday sweeping"
    
    print("✓ CNN 1046000 validation passed")
    
    # Test 3: Rule Distribution
    total_sweeping = 0
    total_parking = 0
    
    for segment in segments:
        rules = segment.get("rules", [])
        total_sweeping += sum(1 for r in rules if r["type"] == "street-sweeping")
        total_parking += sum(1 for r in rules if r["type"] == "parking-regulation")
    
    print(f"Total street sweeping rules: {total_sweeping}")
    print(f"Total parking regulations: {total_parking}")
    
    # Test 4: Side Accuracy
    # Sample segments and verify side determination
    for segment in segments[:10]:
        if segment.get("blockfaceGeometry"):
            # Verify side matches
            calculated_side = get_side_of_street(
                segment["centerlineGeometry"],
                segment["blockfaceGeometry"]
            )
            assert calculated_side == segment["side"], f"Side mismatch for CNN {segment['cnn']}"
    
    print("✓ All validation tests passed")
```

---

## Phase 5: API & Frontend Updates

### 5.1 New API Endpoint

```python
@app.get("/api/segments")
async def get_street_segments(
    street_name: Optional[str] = None,
    cnn: Optional[str] = None,
    bounds: Optional[str] = None
):
    """
    Get street segments with all rules.
    
    Query params:
        street_name: Filter by street name
        cnn: Filter by specific CNN
        bounds: GeoJSON bounds for map viewport
    """
    query = {}
    
    if street_name:
        query["streetName"] = {"$regex": street_name, "$options": "i"}
    
    if cnn:
        query["cnn"] = cnn
    
    if bounds:
        # Spatial query
        bounds_geom = json.loads(bounds)
        query["centerlineGeometry"] = {
            "$geoWithin": {"$geometry": bounds_geom}
        }
    
    segments = await db.street_segments.find(query).to_list(None)
    
    return {
        "segments": segments,
        "count": len(segments)
    }


@app.get("/api/segments/{cnn}/{side}")
async def get_segment(cnn: str, side: str):
    """Get specific segment by CNN + side"""
    segment = await db.street_segments.find_one({"cnn": cnn, "side": side})
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return segment
```

---

## Implementation Timeline

**Week 1**: Core Implementation
- Day 1-2: Data model + ingestion rewrite
- Day 3-4: Parking regulation matching + validation
- Day 5: Testing with CNN 1046000

**Week 2**: Integration
- Day 1-2: API updates
- Day 3-4: Frontend updates
- Day 5: End-to-end testing

---

## Success Criteria

1. ✅ 100% CNN coverage (all 2,007 streets × 2 sides = 4,014 segments)
2. ✅ CNN 1046000 shows correct regulations (Tuesday 9-11am, Side L)
3. ✅ All street sweeping rules attached (>1,800 rules)
4. ✅ Parking regulations matched with >90% accuracy
5. ✅ API response time < 200ms for typical queries
6. ✅ Frontend displays all segments correctly

---

## Risk Mitigation

**Risk**: Parking regulation side determination may be inaccurate

**Mitigation**:
- Use multi-point sampling (not single point)
- Add confidence scores to regulations
- Manual validation for sample of 50 regulations
- Add admin tool to override incorrect matches

**Risk**: Performance issues with 4,000+ segments

**Mitigation**:
- Create proper indexes on CNN + side
- Use geospatial indexes for map queries
- Cache frequently accessed segments
- Lazy-load regulation details

---

## Next Steps

1. **Immediate**: Create backup of current database
2. **Day 1**: Implement StreetSegment model
3. **Day 2**: Rewrite ingestion with enhanced parking reg matching
4. **Day 3**: Test with CNN 1046000 and validate results
5. **Day 4-5**: If successful, proceed with full migration