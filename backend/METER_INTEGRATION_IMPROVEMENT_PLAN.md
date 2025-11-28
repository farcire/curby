# Parking Meter Integration - Improvement Plan

**Date**: November 28, 2024  
**Status**: Recommended Enhancement  
**Priority**: High - Improves data accuracy significantly

---

## Current State Analysis

### Current Implementation (Suboptimal)

**Current Approach in [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:516-533)**:
```python
# Match meters to segments
meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
matched_meters = 0
if not meters_df.empty:
    for _, row in meters_df.iterrows():
        cnn = row.get("street_seg_ctrln_id")
        post_id = row.get("post_id")
        
        if not cnn or not post_id:
            continue
        
        # Find segments for this CNN
        # For now, add to both sides (could be refined with location data)
        for segment in all_segments:
            if segment["cnn"] == cnn:
                segment["schedules"].extend(schedules_by_post.get(post_id, []))
                matched_meters += 1
```

**Problems**:
1. ❌ Adds meters to **both L and R sides** of same CNN
2. ❌ No side determination - inaccurate assignment
3. ❌ Results in duplicate meter data
4. ❌ 17.8% coverage with questionable accuracy

---

## Improved Architecture

### Data Flow

```
Parking Meters (8vzz-qzz9)
    ├─ post_id (unique meter ID)
    ├─ blockface_id (links to blockface with CNN + side)
    ├─ street_seg_ctrln_id (CNN)
    ├─ street_name + street_num (address)
    └─ latitude + longitude (exact location)
         ↓
Meter Operating Schedule (6cqg-dxku)
    ├─ post_id (links to meter)
    ├─ days (operating days)
    ├─ beg_time_dt / end_time_dt (hours)
    ├─ rate (cost per hour)
    └─ time_limit (max parking duration)
         ↓
Street Segments (street_segments collection)
    ├─ cnn + side (L or R)
    ├─ fromAddress / toAddress (address range)
    └─ meters: [{post_id, location, schedules}]
```

### Three-Step Matching Strategy

#### Step 1: Blockface ID Match (Primary - Most Accurate)

**Data Available**:
- Meter has `blockface_id`
- Blockface has `cnn_id` and implicit side

**Implementation**:
```python
# 1. Load blockface metadata
blockface_to_segment = {}
for blockface in pep9_records:
    cnn = blockface.get("cnn_id")
    blockface_id = blockface.get("blockface_id")
    
    if cnn and blockface_id:
        # Determine side using geometric analysis
        side = determine_side(centerline_geo, blockface_geo)
        blockface_to_segment[blockface_id] = (cnn, side)

# 2. Match meters using blockface_id
for meter in meters_df.iterrows():
    blockface_id = meter.get("blockface_id")
    post_id = meter.get("post_id")
    
    if blockface_id in blockface_to_segment:
        cnn, side = blockface_to_segment[blockface_id]
        
        # Find exact segment
        segment = find_segment(cnn=cnn, side=side)
        
        # Add meter with schedules
        segment["meters"].append({
            "post_id": post_id,
            "location": {
                "type": "Point",
                "coordinates": [meter["longitude"], meter["latitude"]]
            },
            "street_num": meter["street_num"],
            "schedules": schedules_by_post.get(post_id, [])
        })
```

**Advantages**:
- ✅ Precise CNN + side determination
- ✅ No ambiguity
- ✅ Leverages authoritative blockface data

#### Step 2: Address Range Match (Secondary - Validation)

**Data Available**:
- Meter has `street_name` and `street_num`
- Segment has `fromAddress` and `toAddress`

**Implementation**:
```python
# Validate or determine side using address
meter_address = int(meter["street_num"])
street_name = meter["street_name"]

# Find segment by address range
segment = db.street_segments.find_one({
    "streetName": street_name,
    "fromAddress": {"$lte": str(meter_address)},
    "toAddress": {"$gte": str(meter_address)}
})

# Validate against blockface match
if segment and segment["cnn"] == meter["street_seg_ctrln_id"]:
    # Confirmed match
    pass
```

**Advantages**:
- ✅ Validates blockface match
- ✅ Can determine side when blockface_id missing
- ✅ User-friendly (address-based)

#### Step 3: Spatial Match (Tertiary - Fallback)

**Data Available**:
- Meter has `latitude` and `longitude`
- Segment has `centerlineGeometry` or `blockfaceGeometry`

**Implementation**:
```python
# Use lat/long for spatial matching
meter_point = Point(meter["longitude"], meter["latitude"])

# Find closest segment
closest_segment = None
min_distance = float('inf')

for segment in segments_with_cnn(meter["street_seg_ctrln_id"]):
    segment_line = shape(segment["centerlineGeometry"])
    distance = meter_point.distance(segment_line)
    
    if distance < min_distance:
        min_distance = distance
        closest_segment = segment

# Determine side using cross product
if closest_segment and min_distance < 0.0001:  # ~10 meters
    side = determine_side_from_point(
        meter_point,
        closest_segment["centerlineGeometry"]
    )
```

**Advantages**:
- ✅ Works when blockface_id missing
- ✅ Validates other methods
- ✅ Handles edge cases

---

## Meter Operating Schedule Integration

### Current Implementation

**File**: [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:499-513)

```python
# Load meter schedules first
schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
schedules_by_post = {}
if not schedules_df.empty:
    for _, row in schedules_df.iterrows():
        post_id = row.get("post_id")
        if post_id:
            if post_id not in schedules_by_post:
                schedules_by_post[post_id] = []
            schedules_by_post[post_id].append({
                "beginTime": row.get("beg_time_dt"),
                "endTime": row.get("end_time_dt"),
                "rate": row.get("rate"),
                "rateQualifier": None,
                "rateUnit": "per hour"
            })
```

### Improved Implementation

**Enhanced Schedule Data**:
```python
schedules_by_post[post_id].append({
    # Time information
    "beginTime": row.get("beg_time_dt"),      # e.g., "09:00"
    "endTime": row.get("end_time_dt"),        # e.g., "18:00"
    
    # Days of operation
    "days": row.get("days"),                   # e.g., "Mon-Fri"
    "daysOfWeek": parse_days(row.get("days")), # ["Monday", "Tuesday", ...]
    
    # Pricing
    "rate": row.get("rate"),                   # e.g., "2.50"
    "rateUnit": "per hour",
    "rateQualifier": row.get("rate_qualifier"), # e.g., "first 2 hours"
    
    # Time limits
    "timeLimit": row.get("time_limit"),        # e.g., "120" (minutes)
    "timeLimitMinutes": int(row.get("time_limit", 0)),
    
    # Additional rules
    "restrictions": row.get("restrictions"),    # Any special conditions
    "exemptions": row.get("exemptions")        # Who is exempt
})
```

---

## Complete Implementation Plan

### Phase 1: Data Model Updates

**Update [`models.py`](backend/models.py:26-58)**:

```python
class MeterInfo(BaseModel):
    """Individual parking meter information"""
    post_id: str                          # Unique meter identifier
    location: Dict                        # GeoJSON Point
    street_num: str                       # Address number
    blockface_id: Optional[str] = None    # Blockface reference
    schedules: List[MeterSchedule] = []   # Operating schedules

class MeterSchedule(BaseModel):
    """Meter operating schedule"""
    beginTime: str                        # Start time (HH:MM)
    endTime: str                          # End time (HH:MM)
    days: str                             # Day string (e.g., "Mon-Fri")
    daysOfWeek: List[str]                 # Parsed days
    rate: str                             # Cost per hour
    rateUnit: str = "per hour"
    timeLimit: Optional[int] = None       # Max parking minutes
    restrictions: Optional[str] = None
    exemptions: Optional[str] = None

class StreetSegment(BaseModel):
    # ... existing fields ...
    meters: List[MeterInfo] = []          # Meters on this segment (NEW)
    schedules: List[MeterSchedule] = []   # DEPRECATED - use meters[].schedules
```

### Phase 2: Ingestion Logic Updates

**Update [`ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)**:

```python
async def match_meters_to_segments_improved(
    segments: List[Dict],
    meters_df: pd.DataFrame,
    schedules_df: pd.DataFrame,
    blockface_df: pd.DataFrame
) -> int:
    """
    Improved meter matching using blockface_id, address, and spatial data.
    
    Returns: Number of meters successfully matched
    """
    
    # Step 1: Build blockface lookup
    blockface_to_segment = build_blockface_lookup(blockface_df, segments)
    
    # Step 2: Build schedules lookup
    schedules_by_post = build_schedules_lookup(schedules_df)
    
    # Step 3: Match meters
    matched_count = 0
    match_methods = {"blockface": 0, "address": 0, "spatial": 0, "failed": 0}
    
    for _, meter in meters_df.iterrows():
        post_id = meter.get("post_id")
        if not post_id:
            continue
        
        # Try Method 1: Blockface ID
        segment = match_by_blockface_id(
            meter, blockface_to_segment, segments
        )
        if segment:
            match_methods["blockface"] += 1
        
        # Try Method 2: Address Range
        if not segment:
            segment = match_by_address(meter, segments)
            if segment:
                match_methods["address"] += 1
        
        # Try Method 3: Spatial
        if not segment:
            segment = match_by_spatial(meter, segments)
            if segment:
                match_methods["spatial"] += 1
        
        # Add meter to segment
        if segment:
            if "meters" not in segment:
                segment["meters"] = []
            
            segment["meters"].append({
                "post_id": post_id,
                "location": {
                    "type": "Point",
                    "coordinates": [
                        float(meter.get("longitude", 0)),
                        float(meter.get("latitude", 0))
                    ]
                },
                "street_num": meter.get("street_num"),
                "blockface_id": meter.get("blockface_id"),
                "schedules": schedules_by_post.get(post_id, [])
            })
            matched_count += 1
        else:
            match_methods["failed"] += 1
    
    # Print statistics
    print(f"\nMeter Matching Statistics:")
    print(f"  Blockface ID matches: {match_methods['blockface']}")
    print(f"  Address matches: {match_methods['address']}")
    print(f"  Spatial matches: {match_methods['spatial']}")
    print(f"  Failed matches: {match_methods['failed']}")
    print(f"  Total matched: {matched_count}")
    
    return matched_count
```

### Phase 3: API Updates

**Update [`main.py`](backend/main.py:98-155)**:

```python
@app.get("/api/v1/blockfaces", response_model=List[dict])
async def get_blockfaces(lat: float, lng: float, radius_meters: int = 500):
    """
    Get street segments with enhanced meter information.
    """
    # ... existing query logic ...
    
    for doc in segments:
        # ... existing mapping ...
        
        # Enhanced meter information
        segment_response["meters"] = doc.get("meters", [])
        
        # Calculate meter statistics
        if segment_response["meters"]:
            segment_response["meterCount"] = len(segment_response["meters"])
            segment_response["hasMeterParking"] = True
            
            # Get rate range
            rates = [
                float(schedule["rate"]) 
                for meter in segment_response["meters"]
                for schedule in meter.get("schedules", [])
                if schedule.get("rate")
            ]
            if rates:
                segment_response["meterRateRange"] = {
                    "min": min(rates),
                    "max": max(rates)
                }
```

---

## Expected Improvements

### Coverage Improvements

| Metric | Current | Expected | Improvement |
|--------|---------|----------|-------------|
| Meter Accuracy | ~50% | ~95% | +90% |
| Side Determination | Ambiguous | Precise | 100% |
| Duplicate Meters | Yes | No | Eliminated |
| Coverage | 17.8% | 25-30% | +40-70% |

### Data Quality Improvements

**Before**:
```json
{
  "cnn": "13059000",
  "side": "L",
  "schedules": [
    {"rate": "2.50", "beginTime": "09:00", "endTime": "18:00"},
    {"rate": "2.50", "beginTime": "09:00", "endTime": "18:00"}  // Duplicate!
  ]
}
```

**After**:
```json
{
  "cnn": "13059000",
  "side": "L",
  "meters": [
    {
      "post_id": "123-456",
      "location": {"type": "Point", "coordinates": [-122.4194, 37.7529]},
      "street_num": "455",
      "schedules": [
        {
          "rate": "2.50",
          "beginTime": "09:00",
          "endTime": "18:00",
          "days": "Mon-Fri",
          "timeLimit": 120
        }
      ]
    }
  ]
}
```

---

## Implementation Timeline

### Week 1: Data Model & Analysis
- [ ] Update data models in [`models.py`](backend/models.py)
- [ ] Analyze blockface_id coverage in meters dataset
- [ ] Create test cases for matching algorithms

### Week 2: Core Implementation
- [ ] Implement blockface lookup builder
- [ ] Implement three-tier matching strategy
- [ ] Add comprehensive logging and statistics

### Week 3: Testing & Validation
- [ ] Test on Mission neighborhood data
- [ ] Validate meter assignments manually
- [ ] Compare before/after accuracy

### Week 4: Deployment
- [ ] Run full re-ingestion with new logic
- [ ] Update API responses
- [ ] Update frontend to display meter info
- [ ] Document changes

---

## Success Criteria

### Must Have
- [ ] 95%+ meters matched to correct segment side
- [ ] Zero duplicate meter assignments
- [ ] Complete schedule information for each meter
- [ ] Validated against sample addresses

### Should Have
- [ ] 25-30% segment coverage (up from 17.8%)
- [ ] Match method statistics logged
- [ ] Fallback methods working correctly

### Nice to Have
- [ ] Real-time meter availability integration
- [ ] Historical rate data
- [ ] Meter malfunction reporting

---

## Risk Mitigation

### Risk 1: Blockface ID Coverage
**Risk**: Not all meters have blockface_id  
**Mitigation**: Implement address and spatial fallbacks

### Risk 2: Address Parsing
**Risk**: Street numbers may not match exactly  
**Mitigation**: Use fuzzy matching and validation

### Risk 3: Performance
**Risk**: Three-tier matching may be slow  
**Mitigation**: Cache lookups, use efficient data structures

---

## Conclusion

This improved meter integration strategy will:

1. ✅ **Eliminate inaccuracies** from current CNN-only matching
2. ✅ **Provide precise side determination** using blockface_id
3. ✅ **Include complete schedule data** with rates, times, and limits
4. ✅ **Enable address-based validation** for user queries
5. ✅ **Support spatial verification** for edge cases

**Recommendation**: Implement in next sprint for significant data quality improvement.

---

**Document Status**: Ready for Implementation  
**Priority**: High  
**Estimated Effort**: 2-3 weeks  
**Expected ROI**: High - Significantly improves user experience