# Mission Neighborhood Data Merge Summary

## Overview

This document summarizes how parking regulations, metered parking, and street cleaning data merge over active streets and blockfaces for San Francisco's Mission neighborhood.

---

## Mission Neighborhood Scope

**Target Area**: Mission District, San Francisco
- **Primary Zip Code**: 94110
- **Secondary Zip Code**: 94103 (partial coverage - SOMA/Mission border)
- **Geographic Boundaries**: Approximately 14th St to Cesar Chavez, Mission St to Potrero Ave
- **Expected Coverage**: ~2,000 CNNs → ~4,000 street segments (Left & Right sides)

---

## Data Layer Architecture

### The 5-Layer Merge Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 5: Parking Meters (CNN Join + Schedules)             │
│ • Meter locations and post IDs                              │
│ • Rate schedules by time of day/week                        │
│ • Join Method: CNN match + schedule lookup                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ merges into
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: Parking Regulations (Spatial Join)                │
│ • Time limits (2 HR, 4 HR, etc.)                           │
│ • RPP zones, tow-away zones, loading zones                 │
│ • Join Method: Spatial proximity + geometric side matching │
└─────────────────────────────────────────────────────────────┘
                            ↓ merges into
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Street Cleaning (Direct Join) ⚡ FAST!            │
│ • Street sweeping schedules                                 │
│ • Day and time restrictions                                 │
│ • Join Method: Direct CNN + Side match (no spatial needed!)│
└─────────────────────────────────────────────────────────────┘
                            ↓ merges into
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Blockface Geometries (Enhancement)                │
│ • Precise curb-side geometries (offset from centerline)    │
│ • GlobalID identifiers                                      │
│ • Join Method: CNN match + geometric side determination    │
└─────────────────────────────────────────────────────────────┘
                            ↓ enhances
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Active Streets (Foundation) ⭐ 100% COVERAGE      │
│ • CNN identifiers (primary key)                             │
│ • Street names                                              │
│ • Address ranges (Left & Right)                            │
│ • Centerline geometries (always available)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Layer Descriptions

### Layer 1: Active Streets (Foundation)

**Dataset**: `3psu-pn9h`  
**Role**: Primary backbone providing complete street network

**What It Provides**:
- CNN (Centerline Network ID) - unique identifier for each street segment
- Street name (e.g., "20TH ST", "VALENCIA ST")
- Address ranges:
  - Left side: `lf_fadd` to `lf_toadd` (odd numbers typically)
  - Right side: `rt_fadd` to `rt_toadd` (even numbers typically)
- Centerline geometry (LineString) - always available
- Zip code for filtering

**Coverage**: 100% of all streets in Mission  
**Creates**: 2 segments per CNN (Left & Right sides)

**Example**:
```
CNN: 1046000
Street: "20TH ST"
From: Bryant St → To: Florida St

LEFT SEGMENT:
  Address Range: 3401-3449 (odd)
  Geometry: Centerline

RIGHT SEGMENT:
  Address Range: 3400-3448 (even)
  Geometry: Centerline
```

---

### Layer 2: Blockface Geometries (Enhancement)

**Dataset**: `pep9-66vw`  
**Role**: Optional enhancement with precise curb-side geometries

**What It Provides**:
- Blockface-specific geometries (offset from centerline)
- GlobalID (unique identifier for each blockface)
- Side-specific boundaries

**Join Method**:
1. Match by `cnn_id` to Active Streets CNN
2. Use geometric analysis (cross-product) to determine L/R side
3. Add blockface geometry to appropriate segment
4. Store GlobalID for reference

**Coverage**: ~50-60% of segments (optional enhancement)

**Why It's Optional**:
- Not all CNNs have blockface geometries
- Centerline geometry from Layer 1 is always sufficient
- When available, provides more precise curb-side boundaries

---

### Layer 3: Street Cleaning (Direct Join) ⚡

**Dataset**: `yhqp-riqs`  
**Role**: Street sweeping schedules and restrictions

**What It Provides**:
- Day of week (Monday, Tuesday, etc.)
- Time window (`fromhour` to `tohour`)
- Street limits (from/to streets)
- Cardinal direction (N, S, E, W, NE, NW, SE, SW)

**Join Method** (MOST EFFICIENT):
```python
FOR EACH cleaning_schedule:
  segment = find_segment(
    cnn=schedule.cnn,
    side=schedule.cnnrightleft  # Direct match: 'L' or 'R'
  )
  segment.rules.append(cleaning_schedule)
```

**Why It's Fast**:
- 100% of street cleaning records have CNN and Side fields
- No spatial analysis required
- No geometric calculations needed
- Direct key-based lookup

**Coverage**: ~80% of segments (where street cleaning applies)

**Example**:
```
CNN: 1046000, Side: L
Day: Tuesday
Hours: 8AM-10AM
→ Merges into: 1046000-L segment
→ Result: "No parking Tuesday 8AM-10AM (Street Cleaning)"
```

---

### Layer 4: Parking Regulations (Spatial Join)

**Dataset**: `hi6h-neyh`  
**Role**: Time limits, RPP zones, tow-away zones, loading zones

**What It Provides**:
- Regulation type ("2 HR", "NO PARKING", "TOW-AWAY", etc.)
- Time limit in hours
- RPP area codes (W, I, J, K, Q, R, S, T, U, V, X, Y, Z)
- Days of week
- Hours of operation
- Exceptions

**Join Method** (REQUIRES SPATIAL ANALYSIS):
```python
FOR EACH regulation:
  1. Find nearby segments (spatial query within ~50m)
  2. For each nearby segment:
     a. Get centerline geometry
     b. Determine which side regulation is on (geometric analysis)
     c. Match regulation side to segment side
  3. Attach regulation to best matching segment
```

**Why It's Complex**:
- Regulations have geometries that may not align perfectly with segments
- Need to determine which side of street the regulation applies to
- Requires distance calculations and geometric analysis

**Coverage**: Varies by area
- Dense in commercial corridors (Valencia, Mission St)
- Sparse in residential areas
- Concentrated around transit and commercial zones

**Example**:
```
Regulation: "2 HR PARKING 9AM-6PM MON-SAT"
Location: Near CNN 1046000 centerline
Geometric Analysis: Determines LEFT side
→ Merges into: 1046000-L segment
→ Result: "2 hour parking limit Mon-Sat 9AM-6PM"
```

---

### Layer 5: Parking Meters (CNN Join + Schedules)

**Datasets**: `8vzz-qzz9` (Meters) + `6cqg-dxku` (Schedules)  
**Role**: Metered parking locations and rate schedules

**What It Provides**:
- Meter post ID
- Active/inactive status
- Rate schedules by time of day/week
- Operating hours

**Join Method**:
```python
# Step 1: Build schedule lookup
schedules_by_post[post_id] = [schedules]

# Step 2: Link meters to segments
FOR EACH meter:
  segments = find_segments(cnn=meter.street_seg_ctrln_id)
  schedules = schedules_by_post[meter.post_id]
  FOR EACH segment:
    segment.schedules.append(meter_info_with_schedules)
```

**Coverage**: Concentrated in commercial corridors
- Heavy: Mission St, Valencia St, 24th St
- Moderate: Other commercial streets
- None: Residential side streets

**Note**: Currently applies to both sides of street unless meter location is more precise

**Example**:
```
Meter Post: MS-1234
CNN: 1046000
Schedules:
  - Mon-Fri 9AM-6PM: $3.00/hr
  - Sat 9AM-6PM: $2.00/hr
  - Sun: Free
→ Merges into: Both 1046000-L and 1046000-R
→ Result: "Metered parking $3/hr Mon-Fri 9AM-6PM"
```

---

## Complete Merge Example: 20th Street

### Starting Point (Layer 1)
```
CNN: 1046000
Street: "20TH ST"
From: Bryant St → To: Florida St

Segment 1046000-L (LEFT/North side):
  Address Range: 3401-3449
  Centerline Geometry: [coordinates]

Segment 1046000-R (RIGHT/South side):
  Address Range: 3400-3448
  Centerline Geometry: [coordinates]
```

### After Layer 2 (Blockface Geometries)
```
Segment 1046000-L:
  + Blockface Geometry: [offset coordinates - north curb]
  + GlobalID: {ABC-123-DEF-456}

Segment 1046000-R:
  + Blockface Geometry: [offset coordinates - south curb]
  + GlobalID: {GHI-789-JKL-012}
```

### After Layer 3 (Street Cleaning)
```
Segment 1046000-L:
  + Rule: Street Cleaning Tuesday 8AM-10AM (North side)

Segment 1046000-R:
  + Rule: Street Cleaning Thursday 8AM-10AM (South side)
```

### After Layer 4 (Parking Regulations)
```
Segment 1046000-L:
  + Rule: 2 HR PARKING Mon-Sat 9AM-6PM

Segment 1046000-R:
  + Rule: 2 HR PARKING Mon-Sat 9AM-6PM
```

### After Layer 5 (Parking Meters)
```
Both Segments:
  + Meter MS-5678:
    - Mon-Fri 9AM-6PM: $3.00/hr
    - Sat 9AM-6PM: $2.00/hr
    - Sun: Free
```

### Final Merged Result
```json
{
  "id": "1046000-L",
  "cnn": "1046000",
  "side": "L",
  "streetName": "20TH ST",
  "fromStreet": "BRYANT ST",
  "toStreet": "FLORIDA ST",
  "fromAddress": "3401",
  "toAddress": "3449",
  "zip_code": "94110",
  "centerlineGeometry": { "type": "LineString", "coordinates": [...] },
  "blockfaceGeometry": { "type": "LineString", "coordinates": [...] },
  "globalid": "{ABC-123-DEF-456}",
  "data_layers": [
    "active_streets",
    "blockface_geometry",
    "street_cleaning",
    "parking_regulations",
    "parking_meters"
  ],
  "rules": [
    {
      "type": "street-sweeping",
      "day": "Tuesday",
      "startTime": "08:00",
      "endTime": "10:00",
      "cardinalDirection": "N",
      "description": "No parking Tuesday 8AM-10AM (Street Cleaning)"
    },
    {
      "type": "parking-regulation",
      "regulation": "2 HR PARKING",
      "timeLimit": "2",
      "days": "Mon-Sat",
      "hours": "9AM-6PM",
      "description": "2 hour parking limit Mon-Sat 9AM-6PM"
    }
  ],
  "schedules": [
    {
      "type": "meter",
      "postId": "MS-5678",
      "active": true,
      "schedules": [
        { "days": "Mon-Fri", "hours": "9AM-6PM", "rate": "$3.00/hr" },
        { "days": "Sat", "hours": "9AM-6PM", "rate": "$2.00/hr" },
        { "days": "Sun", "hours": "All Day", "rate": "Free" }
      ]
    }
  ]
}
```

---

## Street Type Comparisons

### Residential Street: Balmy Street

**Characteristics**:
- Quiet residential street
- Minimal commercial activity
- RPP Area W

**Expected Data Layers**:
- ✅ Active Streets (foundation)
- ✅ Blockface Geometry (if available)
- ✅ Street Cleaning (100% coverage)
- ⚠️ Parking Regulations (minimal - mostly RPP)
- ❌ Parking Meters (none)

**Sample Segment**:
```
BALMY ST - L side
Address: 101-199
Data Layers: 3 (active_streets, street_cleaning, parking_regulations)
Rules:
  • Street Cleaning: Thursday 8AM-10AM
  • RPP Area W: Permit required 6PM-8AM
```

---

### Commercial Corridor: Valencia Street

**Characteristics**:
- Major commercial corridor
- High parking demand
- Mix of meters and time limits

**Expected Data Layers**:
- ✅ Active Streets (foundation)
- ✅ Blockface Geometry (high coverage)
- ✅ Street Cleaning (100% coverage)
- ✅ Parking Regulations (dense - multiple rules)
- ✅ Parking Meters (heavy concentration)

**Sample Segment**:
```
VALENCIA ST - L side
Address: 3001-3099
Data Layers: 5 (all layers present)
Rules:
  • Street Cleaning: Tuesday 8AM-10AM
  • 2 HR PARKING: Mon-Sat 9AM-6PM
  • RPP Area W: Permit required 6PM-8AM
  • TOW-AWAY: No stopping 7AM-9AM Mon-Fri
Meters:
  • 15 meter posts with varying rates
  • Peak: $4/hr Mon-Fri 9AM-6PM
  • Off-peak: $2/hr evenings/weekends
```

---

### Major Arterial: Mission Street

**Characteristics**:
- Primary transit corridor
- Very high parking demand
- Complex regulations

**Expected Data Layers**:
- ✅ Active Streets (foundation)
- ✅ Blockface Geometry (high coverage)
- ✅ Street Cleaning (100% coverage)
- ✅ Parking Regulations (very dense - many rules)
- ✅ Parking Meters (very heavy concentration)

**Sample Segment**:
```
MISSION ST - L side
Address: 2400-2498
Data Layers: 5 (all layers present)
Rules:
  • Street Cleaning: Wednesday 8AM-10AM
  • NO PARKING: 7AM-9AM Mon-Fri (transit lane)
  • 1 HR PARKING: 9AM-6PM Mon-Sat
  • TOW-AWAY: Multiple zones
  • LOADING ZONE: 30 min limit 9AM-6PM
Meters:
  • 25+ meter posts
  • Peak: $5/hr Mon-Fri 9AM-6PM
  • High demand area
```

---

## Key Insights

### 1. Foundation is Critical
- Active Streets provides 100% coverage
- Without it, we'd have gaps in the street network
- Address ranges enable deterministic lookups
- Centerline geometry is always available

### 2. Direct Joins are Reliable
- Street Cleaning: 100% reliable (CNN + Side)
- No geometric analysis needed
- Fast and accurate
- Most efficient join method

### 3. Spatial Joins Require Care
- Parking Regulations: Need geometric side determination
- Tolerance settings matter (~50m works well)
- Side matching is critical for accuracy
- More computationally expensive

### 4. Meters Need Refinement
- Currently apply to both sides of street
- Could be improved with precise meter locations
- Schedule lookup works well
- Rate information is comprehensive

### 5. Data Density Varies by Area
- **Commercial corridors**: Very dense (all 5 layers)
- **Residential streets**: Moderate (3-4 layers)
- **Alleys**: Sparse (may only have base layer)

---

## Expected Results for Mission

### Coverage Statistics
- **Total CNNs**: ~2,000
- **Total Segments**: ~4,000 (2 per CNN)
- **With Centerline Geometry**: 100% (4,000)
- **With Blockface Geometry**: ~50-60% (2,000-2,400)
- **With Street Cleaning**: ~80% (3,200)
- **With Parking Regulations**: Varies (dense in commercial)
- **With Meters**: Concentrated on major corridors

### Data Layer Distribution
```
5 layers (fully merged):     ~500 segments (12%)
4 layers:                  ~1,200 segments (30%)
3 layers:                  ~1,800 segments (45%)
2 layers:                    ~400 segments (10%)
1 layer (foundation only):   ~100 segments (3%)
```

---

## Files Created

1. **[`MISSION_FOCUSED_INGESTION_PLAN.md`](backend/MISSION_FOCUSED_INGESTION_PLAN.md)** - Detailed ingestion plan
2. **[`ingest_mission_only.py`](backend/ingest_mission_only.py)** - Mission-specific ingestion script
3. **[`validate_mission_merge.py`](backend/validate_mission_merge.py)** - Validation and analysis script
4. **[`MISSION_DATA_MERGE_SUMMARY.md`](backend/MISSION_DATA_MERGE_SUMMARY.md)** - This document

---

## Next Steps

1. ✅ Run ingestion: `python3 ingest_mission_only.py`
2. ✅ Validate results: `python3 validate_mission_merge.py`
3. 📊 Create visualizations showing data layer density
4. 📄 Generate detailed analysis report with real examples
5. ✅ Validate data quality and coverage metrics

---

**Status**: Documentation Complete  
**Target**: Mission Neighborhood (Zip 94110, 94103)  
**Demonstrates**: How 5 data layers merge over active streets and blockfaces